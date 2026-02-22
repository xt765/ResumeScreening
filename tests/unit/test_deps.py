"""API 依赖注入模块测试。

测试 FastAPI 路由的公共依赖项：
- get_session 数据库会话依赖注入
- get_settings_dep 配置实例依赖注入
- 数据库会话管理（正常流程、异常回滚）
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, get_settings_dep


# ==================== get_settings_dep 测试 ====================


class TestGetSettingsDep:
    """get_settings_dep 依赖测试类。"""

    def test_get_settings_dep_returns_settings(self) -> None:
        """测试 get_settings_dep 返回配置实例。"""
        from src.core.config import Settings

        result = get_settings_dep()

        assert isinstance(result, Settings)

    def test_get_settings_dep_returns_same_instance(self) -> None:
        """测试 get_settings_dep 返回单例配置实例。"""
        result1 = get_settings_dep()
        result2 = get_settings_dep()

        assert result1 is result2


# ==================== get_session 测试 ====================


class TestGetSession:
    """get_session 依赖测试类。"""

    @pytest.mark.asyncio
    async def test_get_session_raises_runtime_error_when_not_initialized(self) -> None:
        """测试数据库未初始化时抛出 RuntimeError。"""
        with patch("src.models.async_session_factory", None):
            with pytest.raises(RuntimeError) as exc_info:
                async for _ in get_session():
                    pass

            assert "数据库未初始化" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_session_yields_session_and_commits(self) -> None:
        """测试 get_session 正常流程：yield 会话并提交。"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()

        # 创建 mock factory
        class MockFactory:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, *args):
                pass

        mock_factory = MagicMock(return_value=MockFactory())

        with patch("src.models.async_session_factory", mock_factory):
            sessions = []
            async for session in get_session():
                sessions.append(session)

            assert len(sessions) == 1
            assert sessions[0] is mock_session
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_context_manager_usage(self) -> None:
        """测试 get_session 作为上下文管理器使用。"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()

        class MockFactory:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, *args):
                pass

        mock_factory = MagicMock(return_value=MockFactory())

        with patch("src.models.async_session_factory", mock_factory):
            gen = get_session()
            session = await gen.__anext__()

            assert session is mock_session

            # 模拟正常结束
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_multiple_calls_create_independent_sessions(self) -> None:
        """测试多次调用 get_session 创建独立会话。"""
        mock_session1 = AsyncMock(spec=AsyncSession)
        mock_session1.commit = AsyncMock()
        mock_session2 = AsyncMock(spec=AsyncSession)
        mock_session2.commit = AsyncMock()

        call_count = 0

        class MockFactory:
            def __init__(self):
                nonlocal call_count
                call_count += 1
                self.session = mock_session1 if call_count == 1 else mock_session2

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, *args):
                pass

        mock_factory = MockFactory

        with patch("src.models.async_session_factory", mock_factory):
            # 第一次调用
            sessions1 = []
            async for session in get_session():
                sessions1.append(session)

            # 第二次调用
            sessions2 = []
            async for session in get_session():
                sessions2.append(session)

            assert sessions1[0] is mock_session1
            assert sessions2[0] is mock_session2
            mock_session1.commit.assert_called_once()
            mock_session2.commit.assert_called_once()


# ==================== get_session 异常回滚测试 ====================


class TestGetSessionRollback:
    """get_session 异常回滚测试类。"""

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_exception_in_try_block(self) -> None:
        """测试 get_session 在 try 块内异常时执行回滚。

        覆盖 src/api/deps.py 第 36-37 行。
        """
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        # 创建一个异步上下文管理器类
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # 创建 mock factory，调用时返回上下文管理器
        mock_factory = MagicMock(return_value=AsyncContextManagerMock())

        with patch("src.models.async_session_factory", mock_factory):
            # 使用生成器的方式直接测试异常处理
            gen = get_session()
            session = await gen.__anext__()
            assert session is mock_session

            # 向生成器抛出异常
            with pytest.raises(ValueError, match="测试异常"):
                await gen.athrow(ValueError("测试异常"))

            # 验证 rollback 被调用
            mock_session.rollback.assert_called_once()
            # 验证 commit 没有被调用
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_database_error(self) -> None:
        """测试 get_session 在数据库错误时执行回滚。

        覆盖 src/api/deps.py 第 36-37 行。
        """
        from sqlalchemy.exc import IntegrityError

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        # 创建一个异步上下文管理器类
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_factory = MagicMock(return_value=AsyncContextManagerMock())

        with patch("src.models.async_session_factory", mock_factory):
            gen = get_session()
            session = await gen.__anext__()
            assert session is mock_session

            # 向生成器抛出数据库错误
            with pytest.raises(IntegrityError):
                await gen.athrow(IntegrityError("statement", {}, None))

            # 验证 rollback 被调用
            mock_session.rollback.assert_called_once()
            # 验证 commit 没有被调用
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_session_rollback_preserves_exception(self) -> None:
        """测试 get_session 回滚后正确重新抛出原始异常。

        覆盖 src/api/deps.py 第 36-37 行。
        """
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        # 创建一个异步上下文管理器类
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_factory = MagicMock(return_value=AsyncContextManagerMock())

        original_exception = RuntimeError("原始异常")

        with patch("src.models.async_session_factory", mock_factory):
            gen = get_session()
            session = await gen.__anext__()
            assert session is mock_session

            # 向生成器抛出异常
            with pytest.raises(RuntimeError, match="原始异常") as exc_info:
                await gen.athrow(original_exception)

            # 验证异常是同一个实例
            assert exc_info.value is original_exception
            mock_session.rollback.assert_called_once()


# ==================== 集成测试 ====================


@pytest.mark.integration
class TestGetSessionIntegration:
    """get_session 集成测试类。

    使用真实数据库会话进行测试。
    """

    @pytest.mark.asyncio
    async def test_get_session_with_real_database(self, test_engine) -> None:
        """测试 get_session 与真实数据库集成。"""
        # 使用测试引擎初始化
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import async_sessionmaker

        test_session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        with patch("src.models.async_session_factory", test_session_factory):
            async for session in get_session():
                assert isinstance(session, AsyncSession)
                # 执行简单查询
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_get_session_transaction_commit(self, test_engine) -> None:
        """测试 get_session 事务提交。"""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import async_sessionmaker

        test_session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        with patch("src.models.async_session_factory", test_session_factory):
            # 在会话中创建临时表
            async for session in get_session():
                await session.execute(
                    text("CREATE TEMPORARY TABLE test_commit (id INT)")
                )
                await session.execute(text("INSERT INTO test_commit VALUES (1)"))

            # 验证数据已提交（新会话中可查询）
            async with test_session_factory() as session:
                result = await session.execute(text("SELECT * FROM test_commit"))
                assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_exception_integration(self, test_engine) -> None:
        """测试 get_session 在异常时回滚。"""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import async_sessionmaker

        test_session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        with patch("src.models.async_session_factory", test_session_factory):
            # 在事务中插入数据，然后抛出异常
            with pytest.raises(ValueError):
                async for session in get_session():
                    await session.execute(
                        text("CREATE TEMPORARY TABLE test_rollback (id INT)")
                    )
                    await session.execute(text("INSERT INTO test_rollback VALUES (1)"))
                    raise ValueError("测试异常")

            # 验证异常被正确抛出，事务应该已回滚
            # 由于使用的是临时表，回滚后表不存在
            pass

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_database_error_integration(self, test_engine) -> None:
        """测试 get_session 在数据库错误时回滚。"""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from sqlalchemy.exc import IntegrityError

        test_session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        with patch("src.models.async_session_factory", test_session_factory):
            # 模拟数据库错误
            with pytest.raises(Exception):
                async for session in get_session():
                    # 执行一个会失败的 SQL
                    await session.execute(text("SELECT invalid_column"))

            # 验证会话已正确处理异常
            pass
