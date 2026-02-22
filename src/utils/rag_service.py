"""RAG 检索服务模块。

结合向量检索和 LLM 生成答案，
支持基于简历数据的智能问答。
"""

import time
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import SecretStr

from src.core.config import get_settings
from src.core.exceptions import LLMException
from src.storage.chroma_client import ChromaClient
from src.utils.embedding import get_embedding_service


class LLMConfig(TypedDict):
    """LLM 配置类型定义。

    Attributes:
        api_key: API 密钥
        base_url: API 基础 URL
        model: 模型名称
        timeout: 超时时间
        max_retries: 最大重试次数
    """

    api_key: str
    base_url: str
    model: str
    timeout: int
    max_retries: int


class RAGService:
    """RAG 服务类。

    结合 ChromaDB 向量检索和 DeepSeek LLM 生成，
    提供基于简历数据的智能问答功能。

    Attributes:
        embedding_service: Embedding 服务实例
        chroma_client: ChromaDB 客户端实例
        llm: DeepSeek LLM 实例
    """

    def __init__(self) -> None:
        """初始化 RAG 服务。

        初始化 Embedding 服务、ChromaDB 客户端和 LLM。
        """
        settings = get_settings()

        self._embedding_service = get_embedding_service()
        self._chroma_client = ChromaClient()
        self._llm_config: LLMConfig = {
            "api_key": settings.deepseek.api_key,
            "base_url": settings.deepseek.base_url,
            "model": settings.deepseek.model,
            "timeout": settings.app.llm_timeout,
            "max_retries": settings.app.llm_max_retries,
        }

        self._llm: ChatOpenAI | None = None
        self._initialized = False

    def _ensure_llm_initialized(self) -> None:
        """确保 LLM 客户端已初始化。

        Raises:
            LLMException: API Key 未配置
        """
        if self._initialized:
            return

        if not self._llm_config["api_key"]:
            raise LLMException(
                message="DeepSeek API Key 未配置",
                provider="deepseek",
                model=self._llm_config["model"],
            )

        self._llm = ChatOpenAI(
            api_key=SecretStr(self._llm_config["api_key"]),
            base_url=self._llm_config["base_url"],
            model=self._llm_config["model"],
            temperature=0.3,  # RAG 场景使用较低温度
            timeout=self._llm_config["timeout"],
            max_retries=self._llm_config["max_retries"],
        )
        self._initialized = True
        logger.info(f"RAG LLM 初始化完成: model={self._llm_config['model']}")

    async def _retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """检索相关文档。

        使用向量相似度检索相关简历文档。

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            检索到的文档列表

        Raises:
            LLMException: Embedding 调用失败
        """
        # 生成查询向量
        query_vector = await self._embedding_service.embed_query(query)

        if not query_vector:
            logger.warning("查询向量为空，返回空结果")
            return []

        # 执行向量检索
        results = self._chroma_client.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filters,
        )

        # 解析结果
        documents: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            documents.append(
                {
                    "id": doc_id,
                    "content": docs[i] if i < len(docs) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0.0,
                }
            )

        logger.info(f"检索完成: query_length={len(query)}, results={len(documents)}")
        return documents

    def _build_rag_prompt(
        self,
        question: str,
        context_docs: list[dict[str, Any]],
    ) -> tuple[str, str]:
        """构建 RAG 提示词。

        Args:
            question: 用户问题
            context_docs: 检索到的上下文文档

        Returns:
            tuple[str, str]: 系统提示词和用户提示词
        """
        system_prompt = """你是一个专业的简历筛选助手，帮助用户查询和分析候选人信息。

## 核心职责
1. 基于提供的候选人资料回答问题，严禁编造信息
2. 在回答中明确标注信息来源（使用[候选人X]格式引用）
3. 提供数据驱动的分析结论

## 回答格式
### 分析结论
[主要回答内容，引用来源如：根据[候选人1]的简历...]

### 候选人概览
[如涉及多个候选人，提供简要对比表格]

### 建议
[基于分析给出招聘建议]

## 注意事项
- 如果资料中没有相关信息，明确说明"根据现有资料未找到相关信息"
- 数值类信息需精确引用，如工作年限、学历等
- 技能匹配度分析需基于简历实际内容"""

        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            candidate_info = (
                f"【候选人 {i}】\n"
                + f"姓名: {metadata.get('name', '未知')}\n"
                + f"学校: {metadata.get('school', '未知')}\n"
                + f"专业: {metadata.get('major', '未知')}\n"
                + f"学历: {metadata.get('education_level', '未知')}\n"
                + f"工作年限: {metadata.get('work_years', '未知')}年\n"
                + f"技能: {metadata.get('skills', '未知')}\n"
                + f"筛选状态: {metadata.get('screening_status', '未知')}\n"
                + f"简历摘要: {content[:800]}..."
            )
            context_parts.append(candidate_info)

        context_text = "\n\n".join(context_parts)

        human_prompt = f"""请根据以下候选人资料回答问题：

【候选人资料】
{context_text}

【用户问题】
{question}

请按照指定格式给出准确、专业的回答："""

        return system_prompt, human_prompt

    async def _generate_answer(
        self,
        question: str,
        context_docs: list[dict[str, Any]],
    ) -> str:
        """生成答案。

        使用 LLM 基于检索结果生成答案。

        Args:
            question: 用户问题
            context_docs: 检索到的上下文文档

        Returns:
            生成的答案

        Raises:
            LLMException: LLM 调用失败
        """
        self._ensure_llm_initialized()

        if not context_docs:
            return "抱歉，没有找到相关的候选人信息。"

        try:
            if self._llm is None:
                raise LLMException(
                    message="LLM 客户端未初始化",
                    provider="deepseek",
                    model=self._llm_config["model"],
                )

            system_prompt, human_prompt = self._build_rag_prompt(question, context_docs)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]

            logger.info(f"开始生成答案: question_length={len(question)}")
            response = self._llm.invoke(messages)

            content = response.content
            if not isinstance(content, str):
                raise LLMException(
                    message="LLM 响应格式错误",
                    provider="deepseek",
                    model=self._llm_config["model"],
                )

            logger.info(f"答案生成完成: answer_length={len(content)}")
            return content

        except LLMException:
            raise
        except Exception as e:
            logger.exception(f"生成答案失败: {e}")
            raise LLMException(
                message=f"生成答案失败: {e}",
                provider="deepseek",
                model=self._llm_config["model"],
                details={"error": str(e)},
            ) from e

    async def query(
        self,
        question: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行 RAG 查询。

        结合向量检索和 LLM 生成，回答用户问题。

        Args:
            question: 用户问题
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            包含答案和来源的字典，格式：
            {
                "answer": "生成的答案",
                "sources": [{"id": "...", "content": "...", "metadata": {...}}],
                "elapsed_time_ms": 123
            }

        Raises:
            LLMException: Embedding 或 LLM 调用失败
        """
        start_time = time.time()
        logger.info(f"开始 RAG 查询: question={question[:50]}...")

        try:
            # 1. 检索相关文档
            context_docs = await self._retrieve(question, top_k, filters)

            # 2. 生成答案
            answer = await self._generate_answer(question, context_docs)

            elapsed_time = int((time.time() - start_time) * 1000)
            logger.info(f"RAG 查询完成: elapsed_time={elapsed_time}ms")

            return {
                "answer": answer,
                "sources": context_docs,
                "elapsed_time_ms": elapsed_time,
            }

        except LLMException:
            raise
        except Exception as e:
            logger.exception(f"RAG 查询失败: {e}")
            raise LLMException(
                message=f"RAG 查询失败: {e}",
                provider="rag",
                model="unknown",
                details={"error": str(e)},
            ) from e

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """仅执行向量检索（不生成答案）。

        适用于只需要检索结果的场景。

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            检索到的文档列表

        Raises:
            LLMException: Embedding 调用失败
        """
        logger.info(f"开始向量检索: query={query[:50]}...")
        return await self._retrieve(query, top_k, filters)


# 单例实例
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例实例。

    Returns:
        RAGService 实例
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
