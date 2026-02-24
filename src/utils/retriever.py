"""混合检索器模块。

结合向量检索 (Chroma) 和关键词检索 (BM25) 的混合检索实现。
"""

from typing import Any, List, Dict

from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from loguru import logger

from src.storage.chroma_client import ChromaClient
from src.utils.embedding import get_embedding_service


class ChromaRetriever(BaseRetriever):
    """Chroma 向量检索器封装。

    直接调用 ChromaClient 进行向量检索，适配 LangChain 接口。
    """

    top_k: int = 5
    filters: dict[str, Any] | None = None

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """同步执行向量检索（未实现，请使用异步方法）。"""
        raise NotImplementedError("ChromaRetriever 仅支持异步调用，请使用 ainvoke")

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """异步执行向量检索。"""
        try:
            chroma_client = ChromaClient()
            embedding_service = get_embedding_service()

            # 1. 生成查询向量
            query_vector = await embedding_service.embed_query(query)

            if not query_vector:
                logger.warning("查询向量为空")
                return []

            # 2. 执行检索
            results = chroma_client.query(
                query_embeddings=[query_vector],
                n_results=self.top_k,
                where=self.filters,
            )

            # 3. 转换为 Document 对象
            documents = []
            ids = results.get("ids", [[]])[0]
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for i, doc_id in enumerate(ids):
                if i < len(docs):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    metadata["id"] = doc_id
                    # 距离越小越相似
                    metadata["distance"] = distances[i] if i < len(distances) else 0.0

                    documents.append(
                        Document(page_content=docs[i], metadata=metadata)
                    )

            return documents

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []


class EnsembleRetriever(BaseRetriever):
    """自定义 EnsembleRetriever 实现（加权 RRF）。
    
    由于当前环境可能缺失 langchain.retrievers.EnsembleRetriever，这里手动实现一个简化版。
    """
    retrievers: List[BaseRetriever]
    weights: List[float]
    c: int = 60

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        raise NotImplementedError("Use ainvoke")

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """异步执行并行检索并融合结果。"""
        import asyncio
        
        # 并行调用所有 retrievers
        tasks = [
            retriever.ainvoke(query, config={"callbacks": run_manager.get_child() if run_manager else None})
            for retriever in self.retrievers
        ]
        results = await asyncio.gather(*tasks)
        
        # 执行加权 RRF
        return self.weighted_reciprocal_rank(results)

    def weighted_reciprocal_rank(self, doc_lists: List[List[Document]]) -> List[Document]:
        """执行加权 RRF 融合。"""
        if len(doc_lists) != len(self.weights):
            raise ValueError("文档列表数量必须与权重数量一致")

        rrf_score: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        for doc_list, weight in zip(doc_lists, self.weights):
            for rank, doc in enumerate(doc_list, start=1):
                # 使用文档内容作为 key (假设没有重复内容的文档，或者重复内容视为同一文档)
                # 更好的方式是使用 doc.metadata['id'] 如果存在
                key = doc.metadata.get("id") or doc.page_content
                doc_map[key] = doc
                
                score = weight * (1 / (rank + self.c))
                rrf_score[key] = rrf_score.get(key, 0) + score

        # 排序
        sorted_docs = sorted(rrf_score.items(), key=lambda x: x[1], reverse=True)
        
        # 返回文档列表
        return [doc_map[key] for key, score in sorted_docs]


class HybridRetriever:
    """混合检索器管理类。

    管理 Vector Retriever 和 BM25 Retriever 的初始化与组合。
    单例模式，确保 BM25 索引只构建一次。
    """

    _instance = None
    _ensemble_retriever: EnsembleRetriever | None = None
    _bm25_retriever: BM25Retriever | None = None
    _vector_retriever: ChromaRetriever | None = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, weights: List[float] = [0.7, 0.3]) -> None:
        """初始化混合检索器。

        从 Chroma 加载所有文档构建 BM25 索引。
        """
        if self._initialized:
            return

        logger.info("正在初始化混合检索器...")
        chroma_client = ChromaClient()

        try:
            # 1. 获取所有文档用于构建 BM25
            collection = chroma_client._default_collection
            if not collection:
                logger.warning("默认集合未找到，跳过初始化")
                return

            all_docs = collection.get(include=["documents", "metadatas"])
            
            documents = []
            ids = all_docs.get("ids", [])
            contents = all_docs.get("documents", [])
            metadatas = all_docs.get("metadatas", [])

            for i, doc_id in enumerate(ids):
                if contents and i < len(contents) and contents[i]:
                    doc = Document(
                        page_content=contents[i],
                        metadata=metadatas[i] if metadatas and i < len(metadatas) else {},
                    )
                    doc.metadata["id"] = doc_id
                    documents.append(doc)

            logger.info(f"加载了 {len(documents)} 份文档用于 BM25 索引")

            if not documents:
                logger.warning("没有文档，跳过 BM25 初始化")
                return

            # 2. 初始化 BM25Retriever
            self._bm25_retriever = BM25Retriever.from_documents(documents)
            self._bm25_retriever.k = 10 

            # 3. 初始化 Vector Retriever
            self._vector_retriever = ChromaRetriever()
            self._vector_retriever.top_k = 10

            # 4. 组合 EnsembleRetriever
            self._ensemble_retriever = EnsembleRetriever(
                retrievers=[self._vector_retriever, self._bm25_retriever],
                weights=weights,
            )
            self._initialized = True
            logger.success("混合检索器初始化完成")

        except Exception as e:
            logger.error(f"混合检索器初始化失败: {e}")

    async def retrieve(
        self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None
    ) -> List[Document]:
        """执行混合检索。"""
        # 确保已尝试初始化
        if not self._initialized:
            self.initialize()

        # 如果初始化失败或没有 BM25，回退到纯向量检索
        if not self._ensemble_retriever or not self._vector_retriever:
            logger.warning("混合检索不可用，使用纯向量检索")
            vector_retriever = ChromaRetriever()
            vector_retriever.top_k = top_k
            vector_retriever.filters = filters
            return await vector_retriever.ainvoke(query)

        # 更新参数
        self._vector_retriever.top_k = top_k
        self._vector_retriever.filters = filters
        
        if self._bm25_retriever:
            self._bm25_retriever.k = top_k

        # 执行检索
        return await self._ensemble_retriever.ainvoke(query)

    def add_document(self, doc: Document) -> None:
        """动态添加文档到 BM25 索引。"""
        if self._bm25_retriever:
            self._bm25_retriever.add_documents([doc])
            
    def get_retriever(self) -> BaseRetriever | None:
        """获取底层的 EnsembleRetriever 实例（用于 LangChain Agent）。"""
        if not self._initialized:
            self.initialize()
        return self._ensemble_retriever


# 全局单例
_hybrid_retriever = HybridRetriever()

def get_hybrid_retriever() -> HybridRetriever:
    """获取混合检索器单例。"""
    return _hybrid_retriever
