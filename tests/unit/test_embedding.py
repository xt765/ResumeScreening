"""Embedding 向量化服务单元测试。

本模块测试 EmbeddingService 的核心功能：
- 服务初始化
- 批量文本向量化
- 单个查询向量化
- 错误处理
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import LLMException
from src.utils.embedding import EmbeddingService, get_embedding_service


# ==============================================================================
# EmbeddingService 初始化测试
# ==============================================================================
class TestEmbeddingServiceInit:
    """EmbeddingService 初始化测试类。"""

    @patch("src.utils.embedding.get_settings")
    def test_init_success(self, mock_get_settings: MagicMock) -> None:
        """测试成功初始化 Embedding 服务。

        验证：
        - 正确读取配置
        - 初始化状态正确
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        # Act
        service = EmbeddingService()

        # Assert
        assert service._api_key == "test-api-key"
        assert service._model == "text-embedding-v3"
        assert service._initialized is False
        assert service.embeddings is None

    @patch("src.utils.embedding.get_settings")
    def test_init_no_api_key(self, mock_get_settings: MagicMock) -> None:
        """测试无 API Key 时初始化。

        验证：
        - 允许无 API Key 初始化
        - 记录警告日志
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = None
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        # Act
        service = EmbeddingService()

        # Assert
        assert service._api_key is None
        assert service._initialized is False


# ==============================================================================
# EmbeddingService 属性测试
# ==============================================================================
class TestEmbeddingServiceProperties:
    """EmbeddingService 属性测试类。"""

    @patch("src.utils.embedding.get_settings")
    def test_model_property(self, mock_get_settings: MagicMock) -> None:
        """测试 model 属性。

        验证：
        - 返回正确的模型名称
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()

        # Act
        model = service.model

        # Assert
        assert model == "text-embedding-v3"

    @patch("src.utils.embedding.get_settings")
    def test_dimension_property(self, mock_get_settings: MagicMock) -> None:
        """测试 dimension 属性。

        验证：
        - 返回正确的向量维度
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()

        # Act
        dimension = service.dimension

        # Assert
        assert dimension == 1024


# ==============================================================================
# EmbeddingService 初始化验证测试
# ==============================================================================
class TestEmbeddingServiceEnsureInitialized:
    """EmbeddingService 初始化验证测试类。"""

    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    def test_ensure_initialized_success(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试成功初始化 Embeddings 客户端。

        验证：
        - 创建 OpenAIEmbeddings 实例
        - 设置初始化标志
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()

        # Act
        service._ensure_initialized()

        # Assert
        assert service._initialized is True
        assert service.embeddings is not None
        mock_openai_embeddings.assert_called_once()

    @patch("src.utils.embedding.get_settings")
    def test_ensure_initialized_no_api_key(
        self, mock_get_settings: MagicMock
    ) -> None:
        """测试无 API Key 时初始化失败。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = None
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            service._ensure_initialized()

        assert "API Key 未配置" in exc_info.value.message

    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    def test_ensure_initialized_idempotent(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试重复初始化是幂等的。

        验证：
        - 多次调用只初始化一次
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()

        # Act
        service._ensure_initialized()
        service._ensure_initialized()
        service._ensure_initialized()

        # Assert
        mock_openai_embeddings.assert_called_once()


# ==============================================================================
# 批量文本向量化测试
# ==============================================================================
class TestEmbedTexts:
    """批量文本向量化测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_texts_success(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试成功批量向量化。

        验证：
        - 返回正确的向量列表
        - 向量维度正确
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_documents = AsyncMock(
            return_value=[
                [0.1] * 1024,
                [0.2] * 1024,
            ]
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        texts = ["文本一", "文本二"]

        # Act
        vectors = await service.embed_texts(texts)

        # Assert
        assert len(vectors) == 2
        assert len(vectors[0]) == 1024
        assert len(vectors[1]) == 1024

    @pytest.mark.asyncio
    @patch("src.utils.embedding.get_settings")
    async def test_embed_texts_empty_list(
        self, mock_get_settings: MagicMock
    ) -> None:
        """测试空文本列表。

        验证：
        - 返回空列表
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()

        # Act
        vectors = await service.embed_texts([])

        # Assert
        assert vectors == []

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_texts_api_error(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试 API 调用失败。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_documents = AsyncMock(
            side_effect=Exception("API 调用失败")
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        texts = ["文本一"]

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            await service.embed_texts(texts)

        assert "批量向量化失败" in exc_info.value.message

    @pytest.mark.asyncio
    @patch("src.utils.embedding.get_settings")
    async def test_embed_texts_no_api_key(
        self, mock_get_settings: MagicMock
    ) -> None:
        """测试无 API Key 时向量化失败。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = None
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()
        texts = ["文本一"]

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            await service.embed_texts(texts)

        assert "API Key 未配置" in exc_info.value.message


# ==============================================================================
# 单个查询向量化测试
# ==============================================================================
class TestEmbedQuery:
    """单个查询向量化测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_query_success(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试成功查询单个向量化。

        验证：
        - 返回正确的向量
        - 向量维度正确
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        query = "Python 开发工程师"

        # Act
        vector = await service.embed_query(query)

        # Assert
        assert len(vector) == 1024
        mock_embeddings_instance.aembed_query.assert_called_once_with(query)

    @pytest.mark.asyncio
    @patch("src.utils.embedding.get_settings")
    async def test_embed_query_empty(self, mock_get_settings: MagicMock) -> None:
        """测试空查询文本。

        验证：
        - 返回空列表
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()

        # Act
        vector = await service.embed_query("")

        # Assert
        assert vector == []

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_query_api_error(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试查询向量化 API 调用失败。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_query = AsyncMock(
            side_effect=Exception("API 调用失败")
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        query = "测试查询"

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            await service.embed_query(query)

        assert "查询向量化失败" in exc_info.value.message


# ==============================================================================
# embed_single 方法测试
# ==============================================================================
class TestEmbedSingle:
    """embed_single 方法测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_single_is_alias_for_embed_query(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试 embed_single 是 embed_query 的别名。

        验证：
        - 返回与 embed_query 相同的结果
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_query = AsyncMock(
            return_value=[0.5] * 1024
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        text = "测试文本"

        # Act
        vector = await service.embed_single(text)

        # Assert
        assert len(vector) == 1024


# ==============================================================================
# 单例模式测试
# ==============================================================================
class TestGetEmbeddingService:
    """获取 Embedding 服务单例测试类。"""

    @patch("src.utils.embedding.get_settings")
    def test_get_embedding_service_singleton(
        self, mock_get_settings: MagicMock
    ) -> None:
        """测试获取 Embedding 服务单例。

        验证：
        - 多次调用返回同一实例
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        # 重置单例
        import src.utils.embedding as embedding_module
        embedding_module._embedding_service = None

        # Act
        service1 = get_embedding_service()
        service2 = get_embedding_service()

        # Assert
        assert service1 is service2

    @patch("src.utils.embedding.get_settings")
    def test_get_embedding_service_creates_new_if_none(
        self, mock_get_settings: MagicMock
    ) -> None:
        """测试无实例时创建新实例。

        验证：
        - 返回新创建的实例
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        # 重置单例
        import src.utils.embedding as embedding_module
        embedding_module._embedding_service = None

        # Act
        service = get_embedding_service()

        # Assert
        assert service is not None
        assert isinstance(service, EmbeddingService)


# ==============================================================================
# LLMException 异常测试
# ==============================================================================
class TestEmbeddingExceptions:
    """Embedding 异常测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_exception_contains_provider_info(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试异常包含提供商信息。

        验证：
        - LLMException 包含正确的 provider 和 model
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_documents = AsyncMock(
            side_effect=Exception("网络错误")
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            await service.embed_texts(["文本"])

        assert exc_info.value.details["provider"] == "dashscope"
        assert exc_info.value.details["model"] == "text-embedding-v3"

    @pytest.mark.asyncio
    @patch("src.utils.embedding.get_settings")
    async def test_exception_to_dict(
        self, mock_get_settings: MagicMock
    ) -> None:
        """测试异常转换为字典。

        验证：
        - to_dict 方法返回正确的字典
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = None
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            await service.embed_texts(["文本"])

        error_dict = exc_info.value.to_dict()
        assert error_dict["code"] == "LLM_ERROR"
        assert "message" in error_dict
        assert "details" in error_dict


# ==============================================================================
# 边界条件测试
# ==============================================================================
class TestEmbeddingEdgeCases:
    """Embedding 边界条件测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_large_batch(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试大批量文本向量化。

        验证：
        - 正确处理大批量文本
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        # 模拟返回 100 个向量
        mock_embeddings_instance.aembed_documents = AsyncMock(
            return_value=[[0.1] * 1024 for _ in range(100)]
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        texts = [f"文本 {i}" for i in range(100)]

        # Act
        vectors = await service.embed_texts(texts)

        # Assert
        assert len(vectors) == 100

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_long_text(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试长文本向量化。

        验证：
        - 正确处理长文本
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        # 创建一个长文本
        long_text = "这是一段很长的文本。" * 1000

        # Act
        vector = await service.embed_query(long_text)

        # Assert
        assert len(vector) == 1024

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_special_characters(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试特殊字符文本向量化。

        验证：
        - 正确处理特殊字符
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        special_text = "特殊字符：\n\t\r\"'<>&@#$%^*()"

        # Act
        vector = await service.embed_query(special_text)

        # Assert
        assert len(vector) == 1024

    @pytest.mark.asyncio
    @patch("src.utils.embedding.OpenAIEmbeddings")
    @patch("src.utils.embedding.get_settings")
    async def test_embed_multilingual_text(
        self, mock_get_settings: MagicMock, mock_openai_embeddings: MagicMock
    ) -> None:
        """测试多语言文本向量化。

        验证：
        - 正确处理多语言文本
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.dashscope.api_key = "test-api-key"
        mock_settings.dashscope.embedding_model = "text-embedding-v3"
        mock_settings.dashscope.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        mock_settings.app.llm_timeout = 30
        mock_get_settings.return_value = mock_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.aembed_documents = AsyncMock(
            return_value=[
                [0.1] * 1024,
                [0.2] * 1024,
                [0.3] * 1024,
            ]
        )
        mock_openai_embeddings.return_value = mock_embeddings_instance

        service = EmbeddingService()
        texts = [
            "中文文本",
            "English text",
            "日本語テキスト",
        ]

        # Act
        vectors = await service.embed_texts(texts)

        # Assert
        assert len(vectors) == 3
