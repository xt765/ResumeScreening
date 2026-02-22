"""集成测试配置文件。

提供真实数据库连接的 fixtures，用于集成测试：
- MySQL 数据库连接（使用环境变量配置）
- 测试数据清理
- 异步测试客户端
"""

import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from uuid import uuid4

# 设置测试环境变量（必须在导入应用之前）
os.environ["APP_AES_KEY"] = "resume-screening-aes-key-32-byt"
os.environ["MYSQL_HOST"] = "39.108.222.138"
os.environ["MYSQL_PORT"] = "3306"
os.environ["MYSQL_USER"] = "root"
os.environ["MYSQL_PASSWORD"] = "123456"
os.environ["MYSQL_DATABASE"] = "resume_screening_test"
os.environ["MINIO_ENDPOINT"] = "39.108.222.138:9000"
os.environ["MINIO_ACCESS_KEY"] = "root"
os.environ["MINIO_SECRET_KEY"] = "123456"
os.environ["MINIO_BUCKET"] = "resume-images"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import MagicMock

# 创建 Mock Minio 客户端实例
_mock_minio_instance = MagicMock()
_mock_minio_instance.bucket_exists.return_value = True
_mock_minio_instance.make_bucket.return_value = None
_mock_minio_instance.put_object.return_value = MagicMock(object_name="test-object")
_mock_minio_instance.get_object.return_value = MagicMock(data=b"test content")
_mock_minio_instance.stat_object.return_value = MagicMock(size=1024)
_mock_minio_instance.remove_object.return_value = None
_mock_minio_instance.presigned_get_object.return_value = "http://test-url"

# 创建 Mock Minio 类
_mock_minio_class = MagicMock(return_value=_mock_minio_instance)

# 使用 patch 来 mock 外部服务
# 必须在导入 app 之前进行 mock
import minio

minio.Minio = _mock_minio_class

from src.api.main import app
from src.models import Base, ScreeningCondition, StatusEnum, TalentInfo
from src.models.talent import ScreeningStatusEnum, WorkflowStatusEnum


# ==================== 数据库配置 ====================

# 从环境变量获取 MySQL 配置
MYSQL_HOST = os.getenv("MYSQL_HOST", "39.108.222.138")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "resume_screening_test")

# 构建测试数据库 URL（不带数据库名，用于创建数据库）
MYSQL_BASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}"
# 构建测试数据库 URL
TEST_DATABASE_URL = f"{MYSQL_BASE_URL}/{MYSQL_DATABASE}"


@pytest.fixture
async def db_engine():
    """创建集成测试数据库引擎。

    使用真实 MySQL 数据库，每个测试函数创建一次。
    自动创建测试数据库（如果不存在）。

    Yields:
        异步数据库引擎实例。
    """
    # 先连接到 MySQL 服务器（不指定数据库），创建测试数据库
    base_engine = create_async_engine(
        MYSQL_BASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    async with base_engine.begin() as conn:
        # 创建测试数据库（如果不存在）
        await conn.execute(
            text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        )

    await base_engine.dispose()

    # 连接到测试数据库
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 测试结束后清理所有表
    async with engine.begin() as conn:
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession]:
    """创建集成测试数据库会话。

    每个测试函数使用独立的事务，测试结束后回滚以保持数据库干净。

    Args:
        db_engine: 数据库引擎。

    Yields:
        AsyncSession: 异步数据库会话实例。
    """
    async_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        # 测试结束后回滚，保持数据库干净
        await session.rollback()


# ==================== 测试客户端配置 ====================

@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """创建异步测试客户端。

    使用真实数据库会话覆盖依赖注入。

    Args:
        db_session: 数据库会话。

    Yields:
        AsyncClient: 异步 HTTP 客户端实例。
    """
    from src.api.deps import get_session

    async def _get_session_override():
        yield db_session

    # 覆盖依赖
    app.dependency_overrides[get_session] = _get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    # 清理依赖覆盖
    app.dependency_overrides.clear()


# ==================== 测试数据工厂 ====================

@pytest.fixture
def condition_factory(db_session: AsyncSession):
    """筛选条件模型工厂。

    Args:
        db_session: 数据库会话。

    Returns:
        工厂函数，用于创建筛选条件实例。
    """
    async def _create_condition(
        name: str = "测试条件",
        description: str = "测试描述",
        conditions: dict[str, Any] | None = None,
        status: StatusEnum = StatusEnum.ACTIVE,
    ) -> ScreeningCondition:
        """创建筛选条件实例。

        Args:
            name: 条件名称。
            description: 条件描述。
            conditions: 条件配置。
            status: 条件状态。

        Returns:
            ScreeningCondition: 创建的条件实例。
        """
        if conditions is None:
            conditions = {
                "skills": ["Python"],
                "education_level": "bachelor",
                "experience_years": 1,
            }

        condition = ScreeningCondition(
            name=name,
            description=description,
            conditions=conditions,
            status=status,
        )
        db_session.add(condition)
        await db_session.flush()
        await db_session.refresh(condition)
        return condition

    return _create_condition


@pytest.fixture
def talent_factory(db_session: AsyncSession):
    """人才信息模型工厂。

    Args:
        db_session: 数据库会话。

    Returns:
        工厂函数，用于创建人才信息实例。
    """
    async def _create_talent(
        name: str = "测试人才",
        phone: str = "13800138000",
        email: str = "test@example.com",
        education_level: str = "本科",
        school: str = "测试大学",
        major: str = "计算机科学",
        work_years: int = 3,
        skills: list[str] | None = None,
        workflow_status: WorkflowStatusEnum = WorkflowStatusEnum.COMPLETED,
        screening_status: ScreeningStatusEnum | None = ScreeningStatusEnum.QUALIFIED,
        condition_id: str | None = None,
        resume_text: str = "测试简历内容",
    ) -> TalentInfo:
        """创建人才信息实例。

        Args:
            name: 姓名。
            phone: 电话。
            email: 邮箱。
            education_level: 学历。
            school: 学校。
            major: 专业。
            work_years: 工作年限。
            skills: 技能列表。
            workflow_status: 工作流状态。
            screening_status: 筛选状态。
            condition_id: 关联的条件ID。
            resume_text: 简历文本。

        Returns:
            TalentInfo: 创建的人才信息实例。
        """
        if skills is None:
            skills = ["Python", "SQL"]

        talent = TalentInfo(
            name=name,
            phone=phone,
            email=email,
            education_level=education_level,
            school=school,
            major=major,
            work_years=work_years,
            skills=skills,
            workflow_status=workflow_status,
            screening_status=screening_status,
            condition_id=condition_id,
            resume_text=resume_text,
        )
        db_session.add(talent)
        await db_session.flush()
        await db_session.refresh(talent)
        return talent

    return _create_talent


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def sample_condition_data() -> dict[str, Any]:
    """提供示例筛选条件数据。

    Returns:
        dict[str, Any]: 筛选条件数据字典。
    """
    return {
        "name": f"集成测试条件_{uuid4().hex[:8]}",
        "description": "用于集成测试的筛选条件",
        "config": {
            "skills": ["Python", "FastAPI", "SQL"],
            "education_level": "bachelor",
            "experience_years": 3,
            "major": ["计算机科学与技术", "软件工程"],
            "school_tier": "key",
        },
        "is_active": True,
    }


@pytest.fixture
def sample_talent_data() -> dict[str, Any]:
    """提供示例人才数据。

    Returns:
        dict[str, Any]: 人才数据字典。
    """
    return {
        "name": f"测试人才_{uuid4().hex[:8]}",
        "phone": "13800138000",
        "email": "test@example.com",
        "education_level": "硕士",
        "school": "清华大学",
        "major": "计算机科学与技术",
        "work_years": 5,
        "skills": ["Python", "Java", "SQL", "Docker"],
    }


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_chroma():
    """Mock ChromaDB 客户端。

    Returns:
        MagicMock: Mock 的 ChromaDB 客户端实例。
    """
    mock = MagicMock()
    mock.add_documents.return_value = True
    mock.query.return_value = {
        "ids": [["id1", "id2"]],
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{"name": "test1"}, {"name": "test2"}]],
        "distances": [[0.1, 0.2]],
    }
    mock.get_documents.return_value = {
        "ids": ["id1"],
        "documents": ["doc1"],
        "metadatas": [{"name": "test1"}],
    }
    mock.delete_documents.return_value = True
    return mock


@pytest.fixture
def mock_workflow():
    """Mock 简历工作流。

    Returns:
        AsyncMock: Mock 的工作流函数。
    """
    from unittest.mock import AsyncMock

    mock = AsyncMock(return_value={
        "talent_id": str(uuid4()),
        "is_qualified": True,
        "qualification_reason": "符合筛选条件",
        "workflow_status": "completed",
        "total_processing_time": 1.5,
    })
    return mock


# ==================== 额外 Mock Fixtures ====================

@pytest.fixture
def mock_redis():
    """Mock Redis 客户端。

    Returns:
        MagicMock: Mock 的 Redis 客户端实例。
    """
    from unittest.mock import AsyncMock

    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=0)
    mock.expire = AsyncMock(return_value=True)
    mock.ttl = AsyncMock(return_value=-1)
    mock.ping = AsyncMock(return_value=True)
    mock.close = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_minio():
    """Mock MinIO 客户端。

    Returns:
        MagicMock: Mock 的 MinIO 客户端实例。
    """
    from unittest.mock import AsyncMock

    mock = MagicMock()
    mock.bucket_exists = AsyncMock(return_value=True)
    mock.make_bucket = AsyncMock(return_value=None)
    mock.put_object = AsyncMock(return_value=MagicMock(object_name="test-object"))
    mock.get_object = AsyncMock(return_value=MagicMock(data=b"test content"))
    mock.stat_object = AsyncMock(return_value=MagicMock(size=1024))
    mock.remove_object = AsyncMock(return_value=None)
    mock.presigned_get_object = AsyncMock(return_value="http://test-url")
    mock.test_connection = AsyncMock(return_value=True)
    return mock


# ==================== 测试数据清理 Fixtures ====================

@pytest.fixture
async def cleanup_conditions(db_session: AsyncSession):
    """清理筛选条件测试数据。

    Args:
        db_session: 数据库会话。

    Yields:
        None
    """
    yield

    # 测试后清理
    from sqlalchemy import text
    await db_session.execute(text("DELETE FROM screening_condition"))
    await db_session.commit()


@pytest.fixture
async def cleanup_talents(db_session: AsyncSession):
    """清理人才信息测试数据。

    Args:
        db_session: 数据库会话。

    Yields:
        None
    """
    yield

    # 测试后清理
    from sqlalchemy import text
    await db_session.execute(text("DELETE FROM talent_info"))
    await db_session.commit()


# ==================== 批量测试数据 Fixtures ====================

@pytest.fixture
async def multiple_conditions(condition_factory, db_session: AsyncSession):
    """创建多个筛选条件测试数据。

    Args:
        condition_factory: 筛选条件工厂。
        db_session: 数据库会话。

    Returns:
        list[ScreeningCondition]: 创建的条件列表。
    """
    conditions = []
    for i in range(5):
        condition = await condition_factory(
            name=f"批量条件_{i}",
            description=f"批量测试条件描述_{i}",
        )
        conditions.append(condition)
    await db_session.commit()
    return conditions


@pytest.fixture
async def multiple_talents(talent_factory, db_session: AsyncSession):
    """创建多个人才信息测试数据。

    Args:
        talent_factory: 人才信息工厂。
        db_session: 数据库会话。

    Returns:
        list[TalentInfo]: 创建的人才列表。
    """
    talents = []
    for i in range(5):
        talent = await talent_factory(
            name=f"批量人才_{i}",
            school=f"测试大学_{i}",
            major=f"专业_{i}",
        )
        talents.append(talent)
    await db_session.commit()
    return talents


# ==================== 异常测试 Fixtures ====================

@pytest.fixture
def mock_database_error():
    """模拟数据库错误。

    Returns:
        Exception: 数据库异常。
    """
    from sqlalchemy.exc import OperationalError

    return OperationalError("Connection failed", {}, None)


@pytest.fixture
def mock_connection_error():
    """模拟连接错误。

    Returns:
        Exception: 连接异常。
    """
    return ConnectionError("无法连接到服务器")
