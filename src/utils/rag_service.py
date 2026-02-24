"""RAG 检索服务模块。

结合 Agentic RAG 工作流，支持基于简历数据的智能问答与分析。
"""

import time
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage
from loguru import logger

from src.core.exceptions import LLMException
from src.utils.retriever import get_hybrid_retriever
from src.workflows.rag_graph import get_agent_workflow
from src.storage.chroma_client import ChromaClient
from src.utils.embedding import get_embedding_service


class RAGService:
    """RAG 服务类。

    使用 LangGraph Agentic RAG 架构。
    
    Attributes:
        agent_workflow: LangGraph 编译后的工作流
    """

    def __init__(self) -> None:
        """初始化 RAG 服务。"""
        self._workflow = get_agent_workflow()
        # 预热/初始化混合检索器（可选，避免首次请求慢）
        # get_hybrid_retriever().initialize() 
        # 这里的初始化可以延迟到第一次调用，或者在应用启动时调用

    async def query(
        self,
        question: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行 RAG 查询。

        Args:
            question: 用户问题
            top_k: 返回结果数量 (在 Agent 模式下，此参数可能由 Agent 自行决定，或者传递给 Tool)
            filters: 元数据过滤条件 (目前 Agent 模式下较难直接传递 filters，除非在 System Prompt 中硬编码或作为 Tool 参数)
                    为了兼容旧接口，这里的 filters 可能暂时无法完全生效，除非我们修改 SearchTool 接受 filters。
                    目前 SearchTool 仅接受 query 和 top_k。
                    如果 filters 很重要，建议将其转换为自然语言合并到 question 中，或者修改 Tool 定义。

        Returns:
            包含答案和来源的字典。
        """
        start_time = time.time()
        logger.info(f"开始 Agentic RAG 查询: question={question[:50]}...")

        try:
            # 构造初始状态
            inputs = {"messages": [HumanMessage(content=question)]}
            
            # 执行工作流
            final_state = await self._workflow.ainvoke(inputs)
            
            # 解析结果
            messages = final_state["messages"]
            answer = messages[-1].content
            
            # 提取来源（如果有工具调用）
            # 在 LangGraph 中，ToolMessage 包含工具输出。
            # 我们需要遍历消息历史，找到 SearchTool 的输出。
            sources = []
            for msg in messages:
                if msg.type == "tool" and msg.name == "search_resumes":
                    # 解析 SearchTool 返回的文本格式结果，尝试还原为 structured data 比较困难
                    # 但旧接口要求返回 structured sources。
                    # 为了兼容性，我们可能需要让 SearchTool 返回结构化数据（Artifacts），
                    # 或者在这里简化处理，只返回空 sources，因为前端可能主要展示 answer。
                    # 或者：修改 SearchTool 让其返回 JSON 字符串，然后在这里解析。
                    # 鉴于 SearchTool 返回的是对 LLM 友好的文本，这里我们暂时无法完美还原 source objects。
                    # 但为了不破坏前端契约，我们可以尝试再次调用 retrieve 获取 structured data (有点浪费)，
                    # 或者让 SearchTool 将 structured data 存入 state。
                    
                    # 临时方案：再次调用 retrieve 获取 structured data 用于前端展示
                    # 这虽然有一次额外开销，但保证了接口兼容性。
                    # 更好的方案是 Tool 返回 Artifacts (LangChain 0.2+ 支持)，但这里为了稳健，先这样做。
                    # 或者只在前端展示 LLM 的回答，忽略 sources 列表。
                    pass

            # 为了兼容性，我们尝试快速检索一次 Top-K 用于前端展示来源
            # 注意：这可能与 Agent 实际使用的来源不完全一致（如果 Agent 改写了查询）
            # 但通常足够接近。
            retriever = get_hybrid_retriever()
            docs = await retriever.retrieve(question, top_k=top_k, filters=filters)
            
            # ---------------------------------------------------------
            # 增强评分逻辑：Re-scoring & Hybrid Scoring
            # ---------------------------------------------------------
            try:
                doc_ids = [doc.metadata.get("id") for doc in docs if doc.metadata.get("id")]
                if doc_ids:
                    chroma_client = ChromaClient()
                    embedding_service = get_embedding_service()
                    
                    # 1. 生成查询向量
                    query_vector = await embedding_service.embed_query(question)
                    
                    # 2. 定向查询 Chroma 获取确切距离 (Re-scoring)
                    # 注意：Chroma query 默认返回 Squared L2 distance
                    chroma_results = chroma_client.query(
                        query_embeddings=[query_vector],
                        n_results=len(doc_ids),
                        where={"id": {"$in": doc_ids}} if len(doc_ids) > 1 else {"id": doc_ids[0]},
                        # 注意：Chroma where 过滤 id 需要 metadata 中有 id 字段
                        # HybridRetriever 入库时已确保 metadata["id"] = doc_id
                    )
                    
                    # 建立 id -> distance 映射
                    id_to_dist = {}
                    if chroma_results and chroma_results.get("ids"):
                        r_ids = chroma_results["ids"][0]
                        r_dists = chroma_results["distances"][0]
                        for rid, rdist in zip(r_ids, r_dists):
                            id_to_dist[rid] = rdist
                            
                    # 3. 计算混合分数
                    for doc in docs:
                        doc_id = doc.metadata.get("id")
                        
                        # 获取/计算向量分 (Vector Score)
                        distance = id_to_dist.get(doc_id)
                        if distance is None:
                            # 如果没查到（罕见），尝试使用原始 distance 或默认值
                            distance = doc.metadata.get("distance", 2.0)
                        
                        # 更新 distance 到 metadata
                        doc.metadata["distance"] = distance
                        
                        # 归一化 L2 距离 -> 相似度 [0, 1]
                        # 假设归一化向量，max L2^2 = 4
                        sim_vec = max(0.0, 1.0 - distance / 2.0)
                        
                        # 计算关键字分 (Keyword Score) - 字符覆盖率
                        content = doc.page_content
                        q_chars = set(question)
                        c_chars = set(content)
                        sim_kw = len(q_chars & c_chars) / len(q_chars) if q_chars else 0.0
                        
                        # 综合评分 (Hybrid Score)
                        # 权重: 向量 0.7, 关键字 0.3
                        hybrid_score = 0.7 * sim_vec + 0.3 * sim_kw
                        
                        # 将综合分写入 metadata，供后续使用
                        doc.metadata["similarity_score"] = hybrid_score
                        
            except Exception as e:
                logger.warning(f"Re-scoring 失败，使用原始分数: {e}")
                # 兜底：确保有 similarity_score
                for doc in docs:
                    if "similarity_score" not in doc.metadata:
                        dist = doc.metadata.get("distance", 2.0)
                        doc.metadata["similarity_score"] = max(0.0, 1.0 - dist / 2.0)

            structured_sources = []
            for doc in docs:
                structured_sources.append({
                    "id": doc.metadata.get("id"),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": doc.metadata.get("distance"),
                    "similarity_score": doc.metadata.get("similarity_score"),
                })

            elapsed_time = int((time.time() - start_time) * 1000)
            logger.info(f"Agentic RAG 查询完成: elapsed_time={elapsed_time}ms")

            return {
                "answer": answer,
                "sources": structured_sources,
                "elapsed_time_ms": elapsed_time,
            }

        except Exception as e:
            logger.exception(f"RAG 查询失败: {e}")
            raise LLMException(
                message=f"RAG 查询失败: {e}",
                provider="agentic_rag",
                model="unknown",
                details={"error": str(e)},
            ) from e

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """仅执行向量检索（兼容旧接口）。"""
        retriever = get_hybrid_retriever()
        docs = await retriever.retrieve(query, top_k=top_k, filters=filters)
        
        return [
            {
                "id": doc.metadata.get("id"),
                "content": doc.page_content,
                "metadata": doc.metadata,
                "distance": doc.metadata.get("distance"),
            }
            for doc in docs
        ]


# 单例实例
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例实例。"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
