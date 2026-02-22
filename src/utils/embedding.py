"""Embedding 向量化服务模块。

使用 DashScope Embedding API 进行文本向量化，
支持批量文本处理和单个查询向量化。
"""

from langchain_openai import OpenAIEmbeddings
from loguru import logger
from pydantic import SecretStr

from src.core.config import get_settings
from src.core.exceptions import LLMException


class EmbeddingService:
    """Embedding 服务类。

    封装 DashScope Embedding API 调用，提供文本向量化功能。
    使用 OpenAI 兼容模式调用 DashScope API。

    Attributes:
        embeddings: LangChain OpenAIEmbeddings 实例
        model: 使用的 Embedding 模型名称
    """

    def __init__(self) -> None:
        """初始化 Embedding 服务。

        从配置中读取 DashScope API 配置，创建 Embeddings 客户端。
        """
        settings = get_settings()

        self._model = settings.dashscope.embedding_model
        self._api_key = settings.dashscope.api_key
        self._base_url = settings.dashscope.base_url
        self._timeout = settings.app.llm_timeout

        if not self._api_key:
            logger.warning("DashScope API Key 未配置，Embedding 服务将不可用")

        self.embeddings: OpenAIEmbeddings | None = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """确保 Embeddings 客户端已初始化。

        Raises:
            LLMException: API Key 未配置
        """
        if self._initialized:
            return

        if not self._api_key:
            raise LLMException(
                message="DashScope API Key 未配置",
                provider="dashscope",
                model=self._model,
            )

        self.embeddings = OpenAIEmbeddings(
            api_key=SecretStr(self._api_key),
            base_url=self._base_url,
            model=self._model,
        )
        self._initialized = True
        logger.info(f"Embedding 服务初始化完成: model={self._model}")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化。

        将多个文本转换为向量，用于文档入库。

        Args:
            texts: 文本列表

        Returns:
            向量列表，每个向量对应一个文本

        Raises:
            LLMException: Embedding 调用失败
        """
        self._ensure_initialized()

        if not texts:
            logger.warning("文本列表为空，返回空向量列表")
            return []

        try:
            logger.info(f"开始批量向量化: text_count={len(texts)}")

            if self.embeddings is None:
                raise LLMException(
                    message="Embeddings 客户端未初始化",
                    provider="dashscope",
                    model=self._model,
                )

            vectors = await self.embeddings.aembed_documents(texts)

            logger.info(f"批量向量化完成: vector_count={len(vectors)}")
            return vectors

        except LLMException:
            raise
        except Exception as e:
            logger.exception(f"批量向量化失败: {e}")
            raise LLMException(
                message=f"批量向量化失败: {e}",
                provider="dashscope",
                model=self._model,
                details={"text_count": len(texts), "error": str(e)},
            ) from e

    async def embed_query(self, query: str) -> list[float]:
        """单个查询向量化。

        将单个查询文本转换为向量，用于相似度检索。

        Args:
            query: 查询文本

        Returns:
            查询向量

        Raises:
            LLMException: Embedding 调用失败
        """
        self._ensure_initialized()

        if not query:
            logger.warning("查询文本为空")
            return []

        try:
            logger.debug(f"开始查询向量化: query_length={len(query)}")

            if self.embeddings is None:
                raise LLMException(
                    message="Embeddings 客户端未初始化",
                    provider="dashscope",
                    model=self._model,
                )

            vector = await self.embeddings.aembed_query(query)

            logger.debug(f"查询向量化完成: vector_dim={len(vector)}")
            return vector

        except LLMException:
            raise
        except Exception as e:
            logger.exception(f"查询向量化失败: {e}")
            raise LLMException(
                message=f"查询向量化失败: {e}",
                provider="dashscope",
                model=self._model,
                details={"query_length": len(query), "error": str(e)},
            ) from e

    async def embed_single(self, text: str) -> list[float]:
        """单个文本向量化（embed_query 的别名）。

        为保持接口一致性，提供 embed_single 方法。

        Args:
            text: 文本内容

        Returns:
            文本向量

        Raises:
            LLMException: Embedding 调用失败
        """
        return await self.embed_query(text)

    @property
    def model(self) -> str:
        """获取当前使用的模型名称。

        Returns:
            模型名称
        """
        return self._model

    @property
    def dimension(self) -> int:
        """获取向量维度。

        DashScope text-embedding-v3 模型默认输出 1024 维向量。

        Returns:
            向量维度
        """
        return 1024


# 单例实例
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """获取 Embedding 服务单例实例。

    Returns:
        EmbeddingService 实例
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
