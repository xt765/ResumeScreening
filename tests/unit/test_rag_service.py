"""RAG 检索服务单元测试。

本模块测试 RAGService 的核心功能：
- 服务初始化
- 向量检索
- LLM 答案生成
- RAG 查询
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import LLMException
from src.utils.rag_service import LLMConfig, RAGService, get_rag_service


# ==============================================================================
# RAGService 初始化测试
# ==============================================================================
class TestRAGServiceInit:
    """RAGService 初始化测试类。"""

    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_init_success(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
    ) -> None:
        """测试成功初始化 RAG 服务。

        验证：
        - 正确读取配置
        - 初始化 Embedding 服务和 ChromaDB 客户端
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        # Act
        service = RAGService()

        # Assert
        assert service._llm_config["api_key"] == "test-api-key"
        assert service._llm_config["model"] == "deepseek-chat"
        assert service._initialized is False
        assert service._llm is None

    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_init_no_api_key(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
    ) -> None:
        """测试无 API Key 时初始化。

        验证：
        - 允许无 API Key 初始化
        - LLM 配置中 api_key 为空
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = None
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        # Act
        service = RAGService()

        # Assert
        assert service._llm_config["api_key"] is None


# ==============================================================================
# LLM 初始化验证测试
# ==============================================================================
class TestRAGServiceEnsureLlmInitialized:
    """RAGService LLM 初始化验证测试类。"""

    @patch("src.utils.rag_service.ChatOpenAI")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_ensure_llm_initialized_success(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chat_openai: MagicMock,
    ) -> None:
        """测试成功初始化 LLM 客户端。

        验证：
        - 创建 ChatOpenAI 实例
        - 设置初始化标志
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()
        mock_chat_openai.return_value = MagicMock()

        service = RAGService()

        # Act
        service._ensure_llm_initialized()

        # Assert
        assert service._initialized is True
        assert service._llm is not None
        mock_chat_openai.assert_called_once()

    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_ensure_llm_initialized_no_api_key(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
    ) -> None:
        """测试无 API Key 时 LLM 初始化失败。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = None
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        service = RAGService()

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            service._ensure_llm_initialized()

        assert "API Key 未配置" in exc_info.value.message

    @patch("src.utils.rag_service.ChatOpenAI")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_ensure_llm_initialized_idempotent(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chat_openai: MagicMock,
    ) -> None:
        """测试重复初始化是幂等的。

        验证：
        - 多次调用只初始化一次
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()
        mock_chat_openai.return_value = MagicMock()

        service = RAGService()

        # Act
        service._ensure_llm_initialized()
        service._ensure_llm_initialized()
        service._ensure_llm_initialized()

        # Assert
        mock_chat_openai.assert_called_once()


# ==============================================================================
# 向量检索测试
# ==============================================================================
class TestRetrieve:
    """向量检索测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_retrieve_success(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试成功检索文档。

        验证：
        - 返回正确的文档列表
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["文档1", "文档2"]],
            "metadatas": [[{"name": "张三"}, {"name": "李四"}]],
            "distances": [[0.1, 0.2]],
        }
        mock_chroma_client.return_value = mock_chroma

        service = RAGService()

        # Act
        results = await service._retrieve("Python 工程师", top_k=5)

        # Assert
        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["content"] == "文档1"
        assert results[0]["metadata"]["name"] == "张三"

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_retrieve_with_filters(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试带过滤条件的检索。

        验证：
        - 过滤条件正确传递
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [["id1"]],
            "documents": [["文档1"]],
            "metadatas": [[{"education_level": "硕士"}]],
            "distances": [[0.1]],
        }
        mock_chroma_client.return_value = mock_chroma

        service = RAGService()
        filters = {"education_level": "硕士"}

        # Act
        results = await service._retrieve("工程师", top_k=5, filters=filters)

        # Assert
        assert len(results) == 1
        mock_chroma.query.assert_called_once()
        call_kwargs = mock_chroma.query.call_args[1]
        assert call_kwargs["where"] == filters

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_retrieve_empty_vector(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试空向量时返回空结果。

        验证：
        - 返回空列表
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(return_value=[])
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma_client.return_value = MagicMock()

        service = RAGService()

        # Act
        results = await service._retrieve("查询")

        # Assert
        assert results == []

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_retrieve_no_results(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试无结果时返回空列表。

        验证：
        - 返回空列表
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        mock_chroma_client.return_value = mock_chroma

        service = RAGService()

        # Act
        results = await service._retrieve("不存在的查询")

        # Assert
        assert results == []


# ==============================================================================
# RAG 提示词构建测试
# ==============================================================================
class TestBuildRagPrompt:
    """RAG 提示词构建测试类。"""

    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_build_rag_prompt(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
    ) -> None:
        """测试构建 RAG 提示词。

        验证：
        - 提示词包含问题和上下文
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        service = RAGService()

        question = "有哪些 Python 工程师？"
        context_docs = [
            {
                "id": "id1",
                "content": "张三，Python 高级工程师，5年经验",
                "metadata": {
                    "name": "张三",
                    "education_level": "硕士",
                    "work_years": 5,
                    "skills": "Python,FastAPI",
                },
            }
        ]

        # Act
        system_prompt, human_prompt = service._build_rag_prompt(
            question, context_docs
        )

        # Assert
        assert "筛选助手" in system_prompt
        assert "张三" in human_prompt
        assert "Python 工程师" in human_prompt

    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_build_rag_prompt_multiple_docs(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
    ) -> None:
        """测试构建包含多个文档的 RAG 提示词。

        验证：
        - 所有文档都包含在上下文中
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        service = RAGService()

        question = "有哪些候选人？"
        context_docs = [
            {
                "id": "id1",
                "content": "张三的简历",
                "metadata": {"name": "张三", "education_level": "硕士", "work_years": 5, "skills": "Python"},
            },
            {
                "id": "id2",
                "content": "李四的简历",
                "metadata": {"name": "李四", "education_level": "本科", "work_years": 3, "skills": "Java"},
            },
        ]

        # Act
        system_prompt, human_prompt = service._build_rag_prompt(
            question, context_docs
        )

        # Assert
        assert "张三" in human_prompt
        assert "李四" in human_prompt
        assert "候选人 1" in human_prompt
        assert "候选人 2" in human_prompt


# ==============================================================================
# 答案生成测试
# ==============================================================================
class TestGenerateAnswer:
    """答案生成测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChatOpenAI")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_generate_answer_success(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
        mock_chat_openai: MagicMock,
    ) -> None:
        """测试成功生成答案。

        验证：
        - 返回正确的答案
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "找到了两位 Python 工程师：张三和李四。"
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        service = RAGService()

        question = "有哪些 Python 工程师？"
        context_docs = [
            {
                "id": "id1",
                "content": "张三的简历",
                "metadata": {"name": "张三"},
            }
        ]

        # Act
        answer = await service._generate_answer(question, context_docs)

        # Assert
        assert answer == "找到了两位 Python 工程师：张三和李四。"

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_generate_answer_no_context(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试无上下文时返回默认答案。

        验证：
        - 返回提示信息
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        service = RAGService()

        # Act
        answer = await service._generate_answer("问题", [])

        # Assert
        assert "没有找到相关的候选人信息" in answer

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChatOpenAI")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_generate_answer_invalid_response(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
        mock_chat_openai: MagicMock,
    ) -> None:
        """测试 LLM 返回无效响应。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = None  # 无效响应
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        service = RAGService()

        context_docs = [{"id": "id1", "content": "内容", "metadata": {}}]

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            await service._generate_answer("问题", context_docs)

        assert "响应格式错误" in exc_info.value.message

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChatOpenAI")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_generate_answer_api_error(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
        mock_chat_openai: MagicMock,
    ) -> None:
        """测试 LLM API 调用失败。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API 调用失败")
        mock_chat_openai.return_value = mock_llm

        service = RAGService()

        context_docs = [{"id": "id1", "content": "内容", "metadata": {}}]

        # Act & Assert
        with pytest.raises(LLMException) as exc_info:
            await service._generate_answer("问题", context_docs)

        assert "生成答案失败" in exc_info.value.message


# ==============================================================================
# RAG 查询测试
# ==============================================================================
class TestQuery:
    """RAG 查询测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChatOpenAI")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_query_success(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
        mock_chat_openai: MagicMock,
    ) -> None:
        """测试成功执行 RAG 查询。

        验证：
        - 返回答案和来源
        - 包含耗时信息
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [["id1"]],
            "documents": [["张三的简历"]],
            "metadatas": [[{"name": "张三"}]],
            "distances": [[0.1]],
        }
        mock_chroma_client.return_value = mock_chroma

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "找到了张三。"
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        service = RAGService()

        # Act
        result = await service.query("有哪些候选人？")

        # Assert
        assert "answer" in result
        assert "sources" in result
        assert "elapsed_time_ms" in result
        assert result["answer"] == "找到了张三。"
        assert len(result["sources"]) == 1

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_query_embedding_error(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试 Embedding 调用失败。

        验证：
        - 抛出 LLMException
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            side_effect=LLMException(
                message="Embedding 失败",
                provider="dashscope",
                model="text-embedding-v3",
            )
        )
        mock_get_embedding.return_value = mock_embedding_service
        mock_chroma_client.return_value = MagicMock()

        service = RAGService()

        # Act & Assert
        with pytest.raises(LLMException):
            await service.query("问题")


# ==============================================================================
# 向量检索（search）测试
# ==============================================================================
class TestSearch:
    """向量检索（search）测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_search_success(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试成功执行向量检索。

        验证：
        - 返回文档列表
        - 不调用 LLM
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["文档1", "文档2"]],
            "metadatas": [[{"name": "张三"}, {"name": "李四"}]],
            "distances": [[0.1, 0.2]],
        }
        mock_chroma_client.return_value = mock_chroma

        service = RAGService()

        # Act
        results = await service.search("Python 工程师", top_k=10)

        # Assert
        assert len(results) == 2
        assert results[0]["id"] == "id1"

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_search_with_filters(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试带过滤条件的向量检索。

        验证：
        - 过滤条件正确传递
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [["id1"]],
            "documents": [["文档1"]],
            "metadatas": [[{"education_level": "硕士"}]],
            "distances": [[0.1]],
        }
        mock_chroma_client.return_value = mock_chroma

        service = RAGService()
        filters = {"education_level": "硕士"}

        # Act
        results = await service.search("工程师", filters=filters)

        # Assert
        assert len(results) == 1


# ==============================================================================
# 单例模式测试
# ==============================================================================
class TestGetRagService:
    """获取 RAG 服务单例测试类。"""

    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_get_rag_service_singleton(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
    ) -> None:
        """测试获取 RAG 服务单例。

        验证：
        - 多次调用返回同一实例
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        # 重置单例
        import src.utils.rag_service as rag_module
        rag_module._rag_service = None

        # Act
        service1 = get_rag_service()
        service2 = get_rag_service()

        # Assert
        assert service1 is service2

    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_settings")
    def test_get_rag_service_creates_new_if_none(
        self,
        mock_get_settings: MagicMock,
        mock_chroma_client: MagicMock,
        mock_get_embedding: MagicMock,
    ) -> None:
        """测试无实例时创建新实例。

        验证：
        - 返回新创建的实例
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_get_embedding.return_value = MagicMock()
        mock_chroma_client.return_value = MagicMock()

        # 重置单例
        import src.utils.rag_service as rag_module
        rag_module._rag_service = None

        # Act
        service = get_rag_service()

        # Assert
        assert service is not None
        assert isinstance(service, RAGService)


# ==============================================================================
# LLMConfig 类型测试
# ==============================================================================
class TestLLMConfig:
    """LLMConfig 类型测试类。"""

    def test_llm_config_type(self) -> None:
        """测试 LLMConfig 类型定义。

        验证：
        - 类型定义正确
        """
        # Arrange & Act
        config: LLMConfig = {
            "api_key": "test-key",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "timeout": 30,
            "max_retries": 3,
        }

        # Assert
        assert config["api_key"] == "test-key"
        assert config["model"] == "deepseek-chat"


# ==============================================================================
# 边界条件测试
# ==============================================================================
class TestRAGServiceEdgeCases:
    """RAG 服务边界条件测试类。"""

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChatOpenAI")
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_query_long_question(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
        mock_chat_openai: MagicMock,
    ) -> None:
        """测试长问题查询。

        验证：
        - 正确处理长问题
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        mock_chroma_client.return_value = mock_chroma

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "没有找到相关信息。"
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm

        service = RAGService()
        long_question = "请详细介绍一下" * 100

        # Act
        result = await service.query(long_question)

        # Assert
        assert "answer" in result

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_search_large_top_k(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试大 top_k 值检索。

        验证：
        - 正确处理大 top_k
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        # 模拟返回 100 个结果
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [[f"id{i}" for i in range(100)]],
            "documents": [[f"文档{i}" for i in range(100)]],
            "metadatas": [[{"name": f"候选人{i}"} for i in range(100)]],
            "distances": [[0.1] * 100],
        }
        mock_chroma_client.return_value = mock_chroma

        service = RAGService()

        # Act
        results = await service.search("查询", top_k=100)

        # Assert
        assert len(results) == 100

    @pytest.mark.asyncio
    @patch("src.utils.rag_service.ChromaClient")
    @patch("src.utils.rag_service.get_embedding_service")
    @patch("src.utils.rag_service.get_settings")
    async def test_retrieve_special_characters(
        self,
        mock_get_settings: MagicMock,
        mock_get_embedding: MagicMock,
        mock_chroma_client: MagicMock,
    ) -> None:
        """测试特殊字符查询。

        验证：
        - 正确处理特殊字符
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.deepseek.api_key = "test-api-key"
        mock_settings.deepseek.base_url = "https://api.deepseek.com"
        mock_settings.deepseek.model = "deepseek-chat"
        mock_settings.app.llm_timeout = 30
        mock_settings.app.llm_max_retries = 3
        mock_get_settings.return_value = mock_settings

        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_query = AsyncMock(
            return_value=[0.1] * 1024
        )
        mock_get_embedding.return_value = mock_embedding_service

        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        mock_chroma_client.return_value = mock_chroma

        service = RAGService()
        special_query = "特殊字符：\n\t\r\"'<>&@#$%^*()"

        # Act
        results = await service._retrieve(special_query)

        # Assert
        assert isinstance(results, list)
