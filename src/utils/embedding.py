"""Embedding 向量化服务模块。

使用 DashScope Embedding API 进行文本向量化，
支持批量文本处理和单个查询向量化。
"""

import httpx
from loguru import logger

from src.core.config import get_settings
from src.core.exceptions import LLMException


class EmbeddingService:
    """Embedding 服务类。

    封装 DashScope Embedding API 调用，提供文本向量化功能。

    Attributes:
        model: 使用的 Embedding 模型名称
        api_key: DashScope API 密钥
        base_url: API 基础 URL
    """

    def __init__(self) -> None:
        """初始化 Embedding 服务。

        从配置中读取 DashScope API 配置。
        """
        settings = get_settings()

        self._model = settings.dashscope.embedding_model
        self._api_key = settings.dashscope.api_key
        self._base_url = settings.dashscope.base_url.rstrip("/")
        self._timeout = settings.app.llm_timeout

        if not self._api_key:
            logger.warning("DashScope API Key 未配置，Embedding 服务将不可用")

    async def _call_embedding_api(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """调用 DashScope Embedding API。

        Args:
            texts: 文本列表

        Returns:
            向量列表

        Raises:
            LLMException: API 调用失败
        """
        if not self._api_key:
            raise LLMException(
                message="DashScope API Key 未配置",
                provider="dashscope",
                model=self._model,
            )

        url = f"{self._base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            vectors = [item["embedding"] for item in data["data"]]
            return vectors

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = str(error_body)
            except Exception:
                error_detail = e.response.text

            logger.error(f"DashScope Embedding API 错误: {error_detail}")
            raise LLMException(
                message=f"Embedding API 调用失败: {error_detail}",
                provider="dashscope",
                model=self._model,
                details={"status_code": e.response.status_code, "error": error_detail},
            ) from e
        except Exception as e:
            logger.exception(f"Embedding API 调用异常: {e}")
            raise LLMException(
                message=f"Embedding API 调用异常: {e}",
                provider="dashscope",
                model=self._model,
            ) from e

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
        if not texts:
            logger.warning("文本列表为空，返回空向量列表")
            return []

        try:
            logger.info(f"开始批量向量化: text_count={len(texts)}")

            batch_size = 20
            all_vectors: list[list[float]] = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                vectors = await self._call_embedding_api(batch)
                all_vectors.extend(vectors)

            logger.info(f"批量向量化完成: vector_count={len(all_vectors)}")
            return all_vectors

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
        if not query:
            logger.warning("查询文本为空")
            return []

        try:
            logger.debug(f"开始查询向量化: query_length={len(query)}")

            vectors = await self._call_embedding_api([query])

            logger.debug(f"查询向量化完成: vector_dim={len(vectors[0])}")
            return vectors[0]

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
