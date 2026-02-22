"""存储客户端单元测试。

本模块测试 MinIO、Redis、ChromaDB 三个存储客户端的核心功能。
使用真实服务进行测试，测试完成后自动清理数据。

测试服务配置：
- MinIO: 39.108.222.138:9000
- Redis: 39.108.222.138:6379
- ChromaDB: data/chroma
"""

import os
import uuid
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest

# 在导入任何模块之前设置环境变量，确保使用真实服务配置
os.environ["MINIO_ENDPOINT"] = "39.108.222.138:9000"
os.environ["MINIO_ACCESS_KEY"] = "root"
os.environ["MINIO_SECRET_KEY"] = "12345678"
os.environ["MINIO_BUCKET"] = "resume-images"
os.environ["MINIO_SECURE"] = "false"

os.environ["REDIS_HOST"] = "39.108.222.138"
os.environ["REDIS_PORT"] = "6379"
os.environ["REDIS_PASSWORD"] = "123456"
os.environ["REDIS_DB"] = "0"

os.environ["CHROMA_PERSIST_DIR"] = "data/chroma"
os.environ["CHROMA_COLLECTION"] = "talent_resumes"


# ==============================================================================
# MinIO 客户端测试
# ==============================================================================
class TestMinIOClient:
    """MinIO 客户端测试类。

    测试图片上传、获取、删除功能。
    使用真实 MinIO 服务进行测试。
    """

    @pytest.fixture(autouse=True)
    def setup(self, real_minio_client) -> Generator[None, None, None]:
        """测试前置和后置处理。

        测试前：初始化客户端和测试数据。
        测试后：清理上传的测试图片。
        """
        # 使用 fixture 提供的真实客户端
        self.client = real_minio_client
        # 存储测试中上传的图片名称，用于清理
        self.uploaded_objects: list[str] = []

        yield

        # 清理测试数据
        for object_name in self.uploaded_objects:
            try:
                self.client.delete_image(object_name)
            except Exception:
                pass  # 忽略清理错误

    def test_upload_image(self) -> None:
        """测试图片上传功能。

        验证：
        - 上传成功返回 URL
        - URL 包含正确的对象名称
        """
        # Arrange: 准备测试数据
        object_name = f"test/test_upload_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"test image content" * 100
        content_type = "image/png"

        # Act: 执行上传
        result = self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type=content_type,
        )

        # 记录以便清理
        self.uploaded_objects.append(object_name)

        # Assert: 验证结果
        assert result is not None
        assert isinstance(result, str)
        assert object_name in result

    def test_upload_image_with_metadata(self) -> None:
        """测试带元数据的图片上传功能。

        验证：
        - 带元数据上传成功
        - 返回有效的 URL
        """
        # Arrange: 准备测试数据
        object_name = f"test/test_metadata_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"test image with metadata" * 50
        content_type = "image/png"
        metadata = {"resume_id": "test-123", "page": "1"}

        # Act: 执行上传
        result = self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type=content_type,
            metadata=metadata,
        )

        # 记录以便清理
        self.uploaded_objects.append(object_name)

        # Assert: 验证结果
        assert result is not None
        assert isinstance(result, str)

    def test_get_image(self) -> None:
        """测试图片获取功能。

        验证：
        - 上传后能正确获取图片数据
        - 获取的数据与上传的数据一致
        """
        # Arrange: 先上传图片
        object_name = f"test/test_get_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"test image for get" * 100
        self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type="image/png",
        )
        self.uploaded_objects.append(object_name)

        # Act: 获取图片
        result = self.client.get_image(object_name)

        # Assert: 验证结果
        assert result is not None
        assert isinstance(result, bytes)
        assert result == image_data

    def test_get_image_not_found(self) -> None:
        """测试获取不存在的图片。

        验证：
        - 获取不存在的图片返回 None
        """
        # Arrange: 使用不存在的对象名称
        object_name = f"test/not_exist_{uuid.uuid4().hex}.png"

        # Act: 获取图片
        result = self.client.get_image(object_name)

        # Assert: 验证结果
        assert result is None

    def test_delete_image(self) -> None:
        """测试图片删除功能。

        验证：
        - 删除成功返回 True
        - 删除后无法获取图片
        """
        # Arrange: 先上传图片
        object_name = f"test/test_delete_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"test image for delete" * 50
        self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type="image/png",
        )

        # Act: 删除图片
        result = self.client.delete_image(object_name)

        # Assert: 验证删除结果
        assert result is True

        # 验证删除后无法获取
        get_result = self.client.get_image(object_name)
        assert get_result is None

    def test_delete_image_not_found(self) -> None:
        """测试删除不存在的图片。

        验证：
        - 删除不存在的图片返回 False
        """
        # Arrange: 使用不存在的对象名称
        object_name = f"test/not_exist_delete_{uuid.uuid4().hex}.png"

        # Act: 删除图片
        result = self.client.delete_image(object_name)

        # Assert: 验证结果
        assert result is False

    def test_connection(self) -> None:
        """测试 MinIO 连接。

        验证：
        - 能成功连接到 MinIO 服务
        """
        # Act: 测试连接
        result = self.client.test_connection()

        # Assert: 验证连接成功
        assert result is True

    def test_get_presigned_url(self) -> None:
        """测试获取预签名 URL 功能。

        验证：
        - 获取预签名 URL 成功
        - URL 包含正确的对象名称
        """
        # Arrange: 先上传图片
        object_name = f"test/test_presigned_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"test image for presigned url" * 50
        self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type="image/png",
        )
        self.uploaded_objects.append(object_name)

        # Act: 获取预签名 URL
        url = self.client.get_presigned_url(object_name, expires=3600)

        # Assert: 验证 URL
        assert url is not None
        assert isinstance(url, str)
        assert object_name in url
        assert "http" in url

    def test_get_presigned_url_custom_expiry(self) -> None:
        """测试自定义过期时间的预签名 URL。

        验证：
        - 自定义过期时间生效
        - 返回有效的 URL
        """
        # Arrange: 先上传图片
        object_name = f"test/test_presigned_custom_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"test image" * 30
        self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type="image/png",
        )
        self.uploaded_objects.append(object_name)

        # Act: 获取自定义过期时间的预签名 URL
        url = self.client.get_presigned_url(object_name, expires=7200)

        # Assert: 验证 URL
        assert url is not None
        assert isinstance(url, str)

    def test_image_exists_true(self) -> None:
        """测试图片存在检查 - 图片存在的情况。

        验证：
        - 存在的图片返回 True
        """
        # Arrange: 先上传图片
        object_name = f"test/test_exists_true_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"test image for exists check" * 40
        self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type="image/png",
        )
        self.uploaded_objects.append(object_name)

        # Act: 检查图片是否存在
        result = self.client.image_exists(object_name)

        # Assert: 验证存在
        assert result is True

    def test_image_exists_false(self) -> None:
        """测试图片存在检查 - 图片不存在的情况。

        验证：
        - 不存在的图片返回 False
        """
        # Arrange: 使用不存在的对象名称
        object_name = f"test/not_exists_{uuid.uuid4().hex}.png"

        # Act: 检查图片是否存在
        result = self.client.image_exists(object_name)

        # Assert: 验证不存在
        assert result is False

    def test_upload_image_with_file_object(self) -> None:
        """测试使用文件对象上传图片。

        验证：
        - 使用 BytesIO 对象上传成功
        - 返回有效的 URL
        """
        import io

        # Arrange: 准备文件对象
        object_name = f"test/test_file_object_{uuid.uuid4().hex}.png"
        image_data = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"test image from file object" * 60)

        # Act: 使用文件对象上传
        result = self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type="image/png",
        )

        # 记录以便清理
        self.uploaded_objects.append(object_name)

        # Assert: 验证上传成功
        assert result is not None
        assert isinstance(result, str)
        assert object_name in result

    def test_ensure_bucket_exists(self) -> None:
        """测试确保存储桶存在功能。

        验证：
        - 存储桶存在检查正常
        - 已存在的存储桶不会重复创建
        """
        # Act: 调用 _ensure_bucket_exists（已在初始化时调用）
        self.client._ensure_bucket_exists()

        # Assert: 验证存储桶存在
        assert self.client.client.bucket_exists(self.client.bucket_name) is True

    def test_upload_large_image(self) -> None:
        """测试上传大图片。

        验证：
        - 大文件上传成功
        - 返回有效的 URL
        """
        # Arrange: 准备较大的图片数据（约 1MB）
        object_name = f"test/test_large_{uuid.uuid4().hex}.png"
        image_data = b"\x89PNG\r\n\x1a\n" + b"x" * (1024 * 1024)  # 1MB 数据

        # Act: 上传大图片
        result = self.client.upload_image(
            object_name=object_name,
            data=image_data,
            content_type="image/png",
        )

        # 记录以便清理
        self.uploaded_objects.append(object_name)

        # Assert: 验证上传成功
        assert result is not None
        assert isinstance(result, str)

        # 验证获取图片
        get_result = self.client.get_image(object_name)
        assert get_result is not None
        assert len(get_result) == len(image_data)


# ==============================================================================
# Redis 客户端测试
# ==============================================================================
class TestRedisClient:
    """Redis 客户端测试类。

    测试缓存存取、JSON 存取功能。
    使用真实 Redis 服务进行测试。
    """

    @pytest.fixture(autouse=True)
    @pytest.mark.asyncio
    async def setup(self, real_redis_client) -> AsyncGenerator[None]:
        """测试前置和后置处理。

        测试前：初始化客户端和测试数据。
        测试后：清理测试键。
        """
        # 使用 fixture 提供的真实客户端
        self.client = real_redis_client
        # 存储测试中创建的键，用于清理
        self.test_keys: list[str] = []

        yield

        # 清理测试数据
        for key in self.test_keys:
            try:
                await self.client.delete_cache(key)
            except Exception:
                pass  # 忽略清理错误

        # 关闭连接
        await self.client.close()

    @pytest.mark.asyncio
    async def test_set_get_cache(self) -> None:
        """测试缓存存取功能。

        验证：
        - 设置缓存成功
        - 获取缓存值正确
        """
        # Arrange: 准备测试数据
        key = f"test:cache:{uuid.uuid4().hex}"
        value = "test_cache_value_测试"
        self.test_keys.append(key)

        # Act: 设置缓存
        set_result = await self.client.set_cache(key, value, expire=60)

        # Assert: 验证设置成功
        assert set_result is True

        # Act: 获取缓存
        get_result = await self.client.get_cache(key)

        # Assert: 验证获取值正确
        assert get_result is not None
        assert get_result == value

    @pytest.mark.asyncio
    async def test_set_cache_with_expire(self) -> None:
        """测试带过期时间的缓存设置。

        验证：
        - 设置带过期时间的缓存成功
        - TTL 设置正确
        """
        # Arrange: 准备测试数据
        key = f"test:expire:{uuid.uuid4().hex}"
        value = "test_expire_value"
        expire_seconds = 120
        self.test_keys.append(key)

        # Act: 设置缓存
        set_result = await self.client.set_cache(key, value, expire=expire_seconds)

        # Assert: 验证设置成功
        assert set_result is True

        # Act: 获取 TTL
        ttl = await self.client.get_ttl(key)

        # Assert: 验证 TTL 在合理范围内
        assert ttl is not None
        assert ttl > 0
        assert ttl <= expire_seconds

    @pytest.mark.asyncio
    async def test_get_cache_not_found(self) -> None:
        """测试获取不存在的缓存。

        验证：
        - 获取不存在的键返回 None
        """
        # Arrange: 使用不存在的键
        key = f"test:not_exist:{uuid.uuid4().hex}"

        # Act: 获取缓存
        result = await self.client.get_cache(key)

        # Assert: 验证返回 None
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_cache(self) -> None:
        """测试缓存删除功能。

        验证：
        - 删除成功
        - 删除后无法获取
        """
        # Arrange: 先设置缓存
        key = f"test:delete:{uuid.uuid4().hex}"
        value = "test_delete_value"
        await self.client.set_cache(key, value, expire=60)

        # Act: 删除缓存
        result = await self.client.delete_cache(key)

        # Assert: 验证删除成功
        assert result is True

        # Act: 验证删除后无法获取
        get_result = await self.client.get_cache(key)

        # Assert: 验证返回 None
        assert get_result is None

    @pytest.mark.asyncio
    async def test_set_get_json(self) -> None:
        """测试 JSON 存取功能。

        验证：
        - 设置 JSON 成功
        - 获取 JSON 值正确
        """
        # Arrange: 准备测试数据
        key = f"test:json:{uuid.uuid4().hex}"
        value = {
            "name": "张三",
            "age": 30,
            "skills": ["Python", "LangChain", "FastAPI"],
            "metadata": {"level": "senior", "active": True},
        }
        self.test_keys.append(key)

        # Act: 设置 JSON
        set_result = await self.client.set_json(key, value, expire=60)

        # Assert: 验证设置成功
        assert set_result is True

        # Act: 获取 JSON
        get_result = await self.client.get_json(key)

        # Assert: 验证获取值正确
        assert get_result is not None
        assert get_result["name"] == value["name"]
        assert get_result["age"] == value["age"]
        assert get_result["skills"] == value["skills"]
        assert get_result["metadata"] == value["metadata"]

    @pytest.mark.asyncio
    async def test_set_json_with_list(self) -> None:
        """测试 JSON 列表存取功能。

        验证：
        - 设置 JSON 列表成功
        - 获取列表值正确
        """
        # Arrange: 准备测试数据
        key = f"test:json_list:{uuid.uuid4().hex}"
        value = [
            {"id": 1, "name": "项目一"},
            {"id": 2, "name": "项目二"},
            {"id": 3, "name": "项目三"},
        ]
        self.test_keys.append(key)

        # Act: 设置 JSON
        set_result = await self.client.set_json(key, value, expire=60)

        # Assert: 验证设置成功
        assert set_result is True

        # Act: 获取 JSON
        get_result = await self.client.get_json(key)

        # Assert: 验证获取值正确
        assert get_result is not None
        assert len(get_result) == 3
        assert get_result[0]["name"] == "项目一"

    @pytest.mark.asyncio
    async def test_get_json_not_found(self) -> None:
        """测试获取不存在的 JSON。

        验证：
        - 获取不存在的键返回 None
        """
        # Arrange: 使用不存在的键
        key = f"test:json_not_exist:{uuid.uuid4().hex}"

        # Act: 获取 JSON
        result = await self.client.get_json(key)

        # Assert: 验证返回 None
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self) -> None:
        """测试键存在检查功能。

        验证：
        - 存在的键返回 True
        - 不存在的键返回 False
        """
        # Arrange: 设置一个键
        key = f"test:exists:{uuid.uuid4().hex}"
        value = "test_exists_value"
        self.test_keys.append(key)
        await self.client.set_cache(key, value, expire=60)

        # Act & Assert: 验证存在的键
        exists_result = await self.client.exists(key)
        assert exists_result is True

        # Act & Assert: 验证不存在的键
        not_exists_key = f"test:not_exists:{uuid.uuid4().hex}"
        not_exists_result = await self.client.exists(not_exists_key)
        assert not_exists_result is False

    @pytest.mark.asyncio
    async def test_connection(self) -> None:
        """测试 Redis 连接。

        验证：
        - 能成功连接到 Redis 服务
        """
        # Act: 测试连接
        result = await self.client.test_connection()

        # Assert: 验证连接成功
        assert result is True

    @pytest.mark.asyncio
    async def test_set_expire(self) -> None:
        """测试设置过期时间功能。

        验证：
        - 设置过期时间成功
        - TTL 更新正确
        """
        # Arrange: 先设置缓存（无过期时间）
        key = f"test:expire_set:{uuid.uuid4().hex}"
        value = "test_set_expire_value"
        self.test_keys.append(key)
        await self.client.set_cache(key, value)

        # Act: 设置过期时间
        result = await self.client.set_expire(key, expire=300)

        # Assert: 验证设置成功
        assert result is True

        # 验证 TTL 已更新
        ttl = await self.client.get_ttl(key)
        assert ttl is not None
        assert 0 < ttl <= 300

    @pytest.mark.asyncio
    async def test_set_expire_nonexistent_key(self) -> None:
        """测试对不存在的键设置过期时间。

        验证：
        - 对不存在的键设置过期时间返回 False
        """
        # Arrange: 使用不存在的键
        key = f"test:expire_nonexistent:{uuid.uuid4().hex}"

        # Act: 设置过期时间
        result = await self.client.set_expire(key, expire=60)

        # Assert: 验证返回 False
        assert result is False

    @pytest.mark.asyncio
    async def test_get_ttl_no_expire(self) -> None:
        """测试获取无过期时间键的 TTL。

        验证：
        - 无过期时间的键返回 -1
        """
        # Arrange: 设置无过期时间的缓存
        key = f"test:ttl_no_expire:{uuid.uuid4().hex}"
        value = "test_ttl_no_expire"
        self.test_keys.append(key)
        await self.client.set_cache(key, value)

        # Act: 获取 TTL
        ttl = await self.client.get_ttl(key)

        # Assert: 验证返回 -1（永不过期）
        assert ttl == -1

    @pytest.mark.asyncio
    async def test_get_ttl_nonexistent_key(self) -> None:
        """测试获取不存在键的 TTL。

        验证：
        - 不存在的键返回 -2
        """
        # Arrange: 使用不存在的键
        key = f"test:ttl_nonexistent:{uuid.uuid4().hex}"

        # Act: 获取 TTL
        ttl = await self.client.get_ttl(key)

        # Assert: 验证返回 -2（键不存在）
        assert ttl == -2

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """测试关闭连接功能。

        验证：
        - 关闭连接不抛出异常
        """
        # Arrange: 创建新的客户端实例用于关闭测试
        from src.storage.redis_client import RedisClient

        test_client = RedisClient()

        # 先执行一些操作确保连接已建立
        await test_client.set_cache("test:close_test", "value", expire=10)

        # Act: 关闭连接
        await test_client.close()

        # Assert: 不抛出异常即成功
        # 注意：关闭后不应再使用该客户端

    @pytest.mark.asyncio
    async def test_set_cache_without_expire(self) -> None:
        """测试设置无过期时间的缓存。

        验证：
        - 设置成功
        - 缓存永不过期
        """
        # Arrange: 准备测试数据
        key = f"test:no_expire:{uuid.uuid4().hex}"
        value = "test_no_expire_value"
        self.test_keys.append(key)

        # Act: 设置缓存（无过期时间）
        set_result = await self.client.set_cache(key, value)

        # Assert: 验证设置成功
        assert set_result is True

        # 验证 TTL 为 -1（永不过期）
        ttl = await self.client.get_ttl(key)
        assert ttl == -1

    @pytest.mark.asyncio
    async def test_delete_cache_nonexistent_key(self) -> None:
        """测试删除不存在的缓存。

        验证：
        - 删除不存在的键返回 True（Redis DELETE 命令特性）
        """
        # Arrange: 使用不存在的键
        key = f"test:delete_nonexistent:{uuid.uuid4().hex}"

        # Act: 删除缓存
        result = await self.client.delete_cache(key)

        # Assert: 验证返回 True
        assert result is True

    @pytest.mark.asyncio
    async def test_set_json_complex_structure(self) -> None:
        """测试复杂 JSON 结构存取。

        验证：
        - 嵌套 JSON 结构正确存储和读取
        """
        # Arrange: 准备复杂的嵌套数据
        key = f"test:json_complex:{uuid.uuid4().hex}"
        value = {
            "candidate": {
                "name": "测试候选人",
                "contact": {
                    "phone": "13800138000",
                    "email": "test@example.com",
                },
                "skills": ["Python", "FastAPI", "LangChain"],
                "experience": [
                    {"company": "公司A", "years": 3},
                    {"company": "公司B", "years": 2},
                ],
            },
            "metadata": {
                "created_at": "2024-01-01",
                "updated_at": "2024-01-15",
            },
        }
        self.test_keys.append(key)

        # Act: 设置 JSON
        set_result = await self.client.set_json(key, value, expire=60)

        # Assert: 验证设置成功
        assert set_result is True

        # Act: 获取 JSON
        get_result = await self.client.get_json(key)

        # Assert: 验证数据完整性
        assert get_result is not None
        assert get_result["candidate"]["name"] == "测试候选人"
        assert get_result["candidate"]["contact"]["phone"] == "13800138000"
        assert len(get_result["candidate"]["skills"]) == 3
        assert len(get_result["candidate"]["experience"]) == 2

    @pytest.mark.asyncio
    async def test_exists_multiple_checks(self) -> None:
        """测试多次检查键存在性。

        验证：
        - 设置前不存在
        - 设置后存在
        - 删除后不存在
        """
        # Arrange: 准备测试数据
        key = f"test:exists_multi:{uuid.uuid4().hex}"
        value = "test_exists_multi"

        # Act & Assert: 设置前不存在
        exists_before = await self.client.exists(key)
        assert exists_before is False

        # Act: 设置缓存
        await self.client.set_cache(key, value, expire=60)
        self.test_keys.append(key)

        # Assert: 设置后存在
        exists_after_set = await self.client.exists(key)
        assert exists_after_set is True

        # Act: 删除缓存
        await self.client.delete_cache(key)

        # Assert: 删除后不存在
        exists_after_delete = await self.client.exists(key)
        assert exists_after_delete is False


# ==============================================================================
# ChromaDB 客户端测试
# ==============================================================================
class TestChromaClient:
    """ChromaDB 客户端测试类。

    测试文档添加、查询、删除功能。
    使用真实 ChromaDB 服务进行测试。
    """

    @pytest.fixture(autouse=True)
    def setup(self, real_chroma_client) -> Generator[None, None, None]:
        """测试前置和后置处理。

        测试前：初始化客户端和测试数据。
        测试后：清理测试文档。
        """
        # 使用 fixture 提供的真实客户端
        self.client = real_chroma_client
        # 使用唯一的测试集合名称
        self.test_collection = f"test_collection_{uuid.uuid4().hex[:8]}"
        # 存储测试中添加的文档 ID，用于清理
        self.test_doc_ids: list[str] = []

        yield

        # 清理测试数据
        if self.test_doc_ids:
            try:
                self.client.delete_documents(
                    ids=self.test_doc_ids, collection=self.test_collection
                )
            except Exception:
                pass  # 忽略清理错误

    def test_add_documents(self) -> None:
        """测试文档添加功能。

        验证：
        - 添加文档成功
        - 返回 True
        """
        # Arrange: 准备测试数据
        doc_id = f"test_doc_{uuid.uuid4().hex}"
        self.test_doc_ids.append(doc_id)
        document = "这是一份测试简历，包含 Python、LangChain、FastAPI 技能。"
        metadata = {"source": "test", "category": "resume"}

        # Act: 添加文档
        result = self.client.add_documents(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
            collection=self.test_collection,
        )

        # Assert: 验证添加成功
        assert result is True

    def test_add_multiple_documents(self) -> None:
        """测试批量添加文档功能。

        验证：
        - 批量添加文档成功
        - 文档数量正确
        """
        # Arrange: 准备测试数据
        doc_ids = [f"test_doc_{uuid.uuid4().hex}_{i}" for i in range(3)]
        self.test_doc_ids.extend(doc_ids)
        documents = [
            "候选人 A：5年 Python 开发经验，熟悉 Django 和 FastAPI。",
            "候选人 B：3年机器学习经验，熟悉 TensorFlow 和 PyTorch。",
            "候选人 C：8年全栈开发经验，熟悉 React 和 Node.js。",
        ]
        metadatas = [
            {"candidate": "A", "experience": "5年"},
            {"candidate": "B", "experience": "3年"},
            {"candidate": "C", "experience": "8年"},
        ]

        # Act: 批量添加文档
        result = self.client.add_documents(
            ids=doc_ids,
            documents=documents,
            metadatas=metadatas,
            collection=self.test_collection,
        )

        # Assert: 验证添加成功
        assert result is True

        # 验证文档数量
        count = self.client.count_documents(collection=self.test_collection)
        assert count >= 3

    def test_query(self) -> None:
        """测试文档查询功能。

        验证：
        - 查询返回正确的结果
        - 结果包含文档和元数据
        """
        # Arrange: 先添加文档
        doc_id = f"test_doc_query_{uuid.uuid4().hex}"
        self.test_doc_ids.append(doc_id)
        document = "张三，Python 高级工程师，10年开发经验，精通 LangChain 和 LLM 应用开发。"
        metadata = {"name": "张三", "role": "高级工程师"}

        self.client.add_documents(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
            collection=self.test_collection,
        )

        # Act: 查询文档
        result = self.client.query(
            query_texts=["Python 工程师"],
            n_results=3,
            collection=self.test_collection,
        )

        # Assert: 验证查询结果
        assert result is not None
        assert "ids" in result
        assert "documents" in result
        assert "metadatas" in result
        assert len(result["ids"]) > 0

    def test_query_with_filter(self) -> None:
        """测试带过滤条件的查询功能。

        验证：
        - 过滤条件生效
        - 只返回符合条件的文档
        """
        # Arrange: 添加多个文档
        doc_ids = [f"test_doc_filter_{uuid.uuid4().hex}_{i}" for i in range(2)]
        self.test_doc_ids.extend(doc_ids)
        documents = [
            "李四，前端工程师，精通 React 和 Vue。",
            "王五，后端工程师，精通 Python 和 Java。",
        ]
        metadatas = [
            {"role": "前端工程师", "level": "中级"},
            {"role": "后端工程师", "level": "高级"},
        ]

        self.client.add_documents(
            ids=doc_ids,
            documents=documents,
            metadatas=metadatas,
            collection=self.test_collection,
        )

        # Act: 带过滤条件查询
        result = self.client.query(
            query_texts=["工程师"],
            n_results=5,
            where={"level": "高级"},
            collection=self.test_collection,
        )

        # Assert: 验证过滤结果
        assert result is not None
        # 验证返回的文档都符合过滤条件
        if result["metadatas"] and len(result["metadatas"][0]) > 0:
            for metadata in result["metadatas"][0]:
                assert metadata.get("level") == "高级"

    def test_delete_documents(self) -> None:
        """测试文档删除功能。

        验证：
        - 删除成功返回 True
        - 删除后查询不到文档
        """
        # Arrange: 先添加文档
        doc_id = f"test_doc_delete_{uuid.uuid4().hex}"
        document = "待删除的测试文档"
        self.client.add_documents(
            ids=[doc_id],
            documents=[document],
            collection=self.test_collection,
        )

        # Act: 删除文档
        result = self.client.delete_documents(
            ids=[doc_id], collection=self.test_collection
        )

        # Assert: 验证删除成功
        assert result is True

        # 从清理列表中移除（已删除）
        if doc_id in self.test_doc_ids:
            self.test_doc_ids.remove(doc_id)

    def test_count_documents(self) -> None:
        """测试文档计数功能。

        验证：
        - 计数返回正确的文档数量
        """
        # Arrange: 添加文档
        doc_ids = [f"test_doc_count_{uuid.uuid4().hex}_{i}" for i in range(2)]
        self.test_doc_ids.extend(doc_ids)
        documents = ["文档一", "文档二"]

        self.client.add_documents(
            ids=doc_ids,
            documents=documents,
            collection=self.test_collection,
        )

        # Act: 获取文档数量
        count = self.client.count_documents(collection=self.test_collection)

        # Assert: 验证计数正确
        assert count >= 2

    def test_connection(self) -> None:
        """测试 ChromaDB 连接。

        验证：
        - 能成功连接到 ChromaDB 服务
        """
        # Act: 测试连接
        result = self.client.test_connection()

        # Assert: 验证连接成功
        assert result is True

    def test_get_documents(self) -> None:
        """测试获取文档功能。

        验证：
        - 获取文档成功
        - 返回正确的文档数据
        """
        # Arrange: 先添加文档
        doc_id = f"test_doc_get_{uuid.uuid4().hex}"
        self.test_doc_ids.append(doc_id)
        document = "测试获取文档内容，包含 Python 和 LangChain 技能。"
        metadata = {"source": "get_test", "type": "resume"}

        self.client.add_documents(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
            collection=self.test_collection,
        )

        # Act: 获取文档
        result = self.client.get_documents(
            ids=[doc_id],
            collection=self.test_collection,
        )

        # Assert: 验证结果
        assert result is not None
        assert "ids" in result
        assert "documents" in result
        assert "metadatas" in result
        assert doc_id in result["ids"]
        assert document in result["documents"]

    def test_get_documents_with_where(self) -> None:
        """测试带过滤条件获取文档功能。

        验证：
        - 过滤条件生效
        - 只返回符合条件的文档
        """
        # Arrange: 添加多个文档
        doc_ids = [f"test_doc_get_where_{uuid.uuid4().hex}_{i}" for i in range(2)]
        self.test_doc_ids.extend(doc_ids)
        documents = ["文档A", "文档B"]
        metadatas = [
            {"category": "A", "level": "senior"},
            {"category": "B", "level": "junior"},
        ]

        self.client.add_documents(
            ids=doc_ids,
            documents=documents,
            metadatas=metadatas,
            collection=self.test_collection,
        )

        # Act: 带过滤条件获取
        result = self.client.get_documents(
            where={"level": "senior"},
            collection=self.test_collection,
        )

        # Assert: 验证过滤结果
        assert result is not None
        assert len(result["ids"]) >= 1

    def test_get_documents_by_id(self) -> None:
        """测试按 ID 获取单个文档。

        验证：
        - 按 ID 获取文档成功
        - 返回正确的文档数据
        """
        # Arrange: 先添加文档
        doc_id = f"test_doc_get_single_{uuid.uuid4().hex}"
        self.test_doc_ids.append(doc_id)
        document = "单个文档测试内容"
        metadata = {"type": "single"}

        self.client.add_documents(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
            collection=self.test_collection,
        )

        # Act: 按 ID 获取文档
        result = self.client.get_documents(
            ids=[doc_id],
            collection=self.test_collection,
        )

        # Assert: 验证结果
        assert result is not None
        assert doc_id in result["ids"]

    def test_update_documents(self) -> None:
        """测试更新文档功能。

        验证：
        - 更新文档成功
        - 更新后的数据正确
        """
        # Arrange: 先添加文档
        doc_id = f"test_doc_update_{uuid.uuid4().hex}"
        self.test_doc_ids.append(doc_id)
        original_document = "原始文档内容"
        original_metadata = {"version": "1"}

        self.client.add_documents(
            ids=[doc_id],
            documents=[original_document],
            metadatas=[original_metadata],
            collection=self.test_collection,
        )

        # Act: 更新文档
        updated_document = "更新后的文档内容，包含更多技能信息。"
        updated_metadata = {"version": "2", "updated": True}

        result = self.client.update_documents(
            ids=[doc_id],
            documents=[updated_document],
            metadatas=[updated_metadata],
            collection=self.test_collection,
        )

        # Assert: 验证更新成功
        assert result is True

        # 验证更新后的数据
        get_result = self.client.get_documents(
            ids=[doc_id],
            collection=self.test_collection,
        )
        assert updated_document in get_result["documents"]

    def test_update_documents_metadata_only(self) -> None:
        """测试仅更新元数据功能。

        验证：
        - 仅更新元数据成功
        - 文档内容保持不变
        """
        # Arrange: 先添加文档
        doc_id = f"test_doc_update_meta_{uuid.uuid4().hex}"
        self.test_doc_ids.append(doc_id)
        document = "文档内容保持不变"
        original_metadata = {"status": "pending"}

        self.client.add_documents(
            ids=[doc_id],
            documents=[document],
            metadatas=[original_metadata],
            collection=self.test_collection,
        )

        # Act: 仅更新元数据
        updated_metadata = {"status": "completed", "reviewed": True}

        result = self.client.update_documents(
            ids=[doc_id],
            metadatas=[updated_metadata],
            collection=self.test_collection,
        )

        # Assert: 验证更新成功
        assert result is True

    def test_get_collection(self) -> None:
        """测试获取集合功能。

        验证：
        - 获取已存在的集合成功
        - 返回有效的集合对象
        """
        # Act: 获取集合
        collection = self.client.get_collection(self.test_collection)

        # Assert: 验证集合对象
        assert collection is not None
        assert collection.name == self.test_collection

    def test_get_collection_with_metadata(self) -> None:
        """测试创建带元数据的集合。

        验证：
        - 创建带元数据的集合成功
        - 集合名称正确
        """
        # Arrange: 使用唯一的集合名称
        collection_name = f"test_meta_collection_{uuid.uuid4().hex[:8]}"
        metadata = {"description": "测试集合", "created_by": "test"}

        # Act: 获取/创建集合
        collection = self.client.get_collection(collection_name, metadata=metadata)

        # Assert: 验证集合对象
        assert collection is not None
        assert collection.name == collection_name

        # 清理：删除测试集合
        self.client.delete_collection(collection_name)

    def test_delete_collection(self) -> None:
        """测试删除集合功能。

        验证：
        - 删除集合成功
        - 删除后集合不存在
        """
        # Arrange: 创建一个临时集合
        temp_collection_name = f"temp_collection_{uuid.uuid4().hex[:8]}"
        self.client.get_collection(temp_collection_name)

        # Act: 删除集合
        result = self.client.delete_collection(temp_collection_name)

        # Assert: 验证删除成功
        assert result is True

    def test_count_documents_empty_collection(self) -> None:
        """测试空集合的文档计数。

        验证：
        - 空集合返回 0
        """
        # Arrange: 使用新的空集合
        empty_collection = f"empty_collection_{uuid.uuid4().hex[:8]}"

        # Act: 获取文档数量
        count = self.client.count_documents(collection=empty_collection)

        # Assert: 验证计数为 0
        assert count == 0

        # 清理
        self.client.delete_collection(empty_collection)

    def test_query_with_embeddings(self) -> None:
        """测试使用嵌入向量查询。

        验证：
        - 使用嵌入向量查询成功
        - 返回正确的结果格式
        """
        # Arrange: 先添加文档
        doc_id = f"test_doc_embed_{uuid.uuid4().hex}"
        self.test_doc_ids.append(doc_id)
        document = "测试嵌入向量查询的文档"

        self.client.add_documents(
            ids=[doc_id],
            documents=[document],
            collection=self.test_collection,
        )

        # Act: 使用嵌入向量查询（提供 query_texts，底层自动生成嵌入）
        result = self.client.query(
            query_texts=["查询文本"],
            n_results=1,
            collection=self.test_collection,
        )

        # Assert: 验证结果格式
        assert result is not None
        assert "ids" in result
        assert "documents" in result
        assert "distances" in result

    def test_delete_documents_with_where(self) -> None:
        """测试带过滤条件删除文档。

        验证：
        - 过滤删除成功
        - 只删除符合条件的文档
        """
        # Arrange: 添加多个文档
        doc_ids = [f"test_doc_del_where_{uuid.uuid4().hex}_{i}" for i in range(2)]
        documents = ["待删除文档A", "保留文档B"]
        metadatas = [
            {"delete_flag": "yes"},
            {"delete_flag": "no"},
        ]

        self.client.add_documents(
            ids=doc_ids,
            documents=documents,
            metadatas=metadatas,
            collection=self.test_collection,
        )

        # Act: 带条件删除
        result = self.client.delete_documents(
            where={"delete_flag": "yes"},
            collection=self.test_collection,
        )

        # Assert: 验证删除成功
        assert result is True

        # 从清理列表中移除已删除的文档
        for doc_id in doc_ids:
            if doc_id in self.test_doc_ids:
                self.test_doc_ids.remove(doc_id)


# ==============================================================================
# 错误处理测试 - MinIO
# ==============================================================================
class TestMinIOClientErrorHandling:
    """MinIO 客户端错误处理测试类。

    测试各种异常情况的处理。
    使用 Mock 来模拟错误场景。
    """

    @pytest.fixture(autouse=True)
    def setup(self, reset_minio_singleton: None) -> Generator[None, None, None]:
        """测试前置处理。

        重置单例并创建客户端实例。
        """
        from src.storage.minio_client import MinIOClient

        self.client = MinIOClient()
        yield

    def test_test_connection_failure(self) -> None:
        """测试连接测试失败的情况。

        验证：
        - 连接失败返回 False
        """
        from minio.error import S3Error
        from unittest.mock import MagicMock, patch

        # Arrange: Mock 客户端抛出 S3Error 异常
        with patch.object(
            self.client.client,
            "bucket_exists",
            side_effect=S3Error(
                code="InternalError",
                message="Connection failed",
                resource="test",
                request_id="test-id",
                host_id="test-host",
                response=None,
            ),
        ):
            # Act: 测试连接
            result = self.client.test_connection()

            # Assert: 验证返回 False
            assert result is False

    def test_upload_image_failure(self) -> None:
        """测试上传图片失败的情况。

        验证：
        - 上传失败抛出异常
        """
        from minio.error import S3Error
        from unittest.mock import patch

        # Arrange: Mock put_object 抛出异常
        with patch.object(
            self.client.client,
            "put_object",
            side_effect=S3Error(
                code="InternalError",
                message="Upload failed",
                resource="test",
                request_id="test-id",
                host_id="test-host",
                response=None,
            ),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(S3Error):
                self.client.upload_image(
                    object_name="test/fail.png",
                    data=b"test data",
                    content_type="image/png",
                )

    def test_get_image_s3_error(self) -> None:
        """测试获取图片时发生 S3 错误（非 NoSuchKey）。

        验证：
        - 非 NoSuchKey 错误抛出异常
        """
        from minio.error import S3Error
        from unittest.mock import patch

        # Arrange: Mock get_object 抛出非 NoSuchKey 异常
        with patch.object(
            self.client.client,
            "get_object",
            side_effect=S3Error(
                code="AccessDenied",
                message="Access denied",
                resource="test",
                request_id="test-id",
                host_id="test-host",
                response=None,
            ),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(S3Error):
                self.client.get_image("test/error.png")

    def test_delete_image_s3_error(self) -> None:
        """测试删除图片时发生 S3 错误（非 NoSuchKey）。

        验证：
        - 非 NoSuchKey 错误抛出异常
        """
        from minio.error import S3Error
        from unittest.mock import patch

        # Arrange: Mock stat_object 抛出非 NoSuchKey 异常
        with patch.object(
            self.client.client,
            "stat_object",
            side_effect=S3Error(
                code="AccessDenied",
                message="Access denied",
                resource="test",
                request_id="test-id",
                host_id="test-host",
                response=None,
            ),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(S3Error):
                self.client.delete_image("test/error.png")

    def test_get_presigned_url_failure(self) -> None:
        """测试获取预签名 URL 失败的情况。

        验证：
        - 获取失败抛出异常
        """
        from minio.error import S3Error
        from unittest.mock import patch

        # Arrange: Mock presigned_get_object 抛出异常
        with patch.object(
            self.client.client,
            "presigned_get_object",
            side_effect=S3Error(
                code="InternalError",
                message="Presigned URL failed",
                resource="test",
                request_id="test-id",
                host_id="test-host",
                response=None,
            ),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(S3Error):
                self.client.get_presigned_url("test/error.png")

    def test_ensure_bucket_exists_failure(self) -> None:
        """测试确保存储桶存在失败的情况。

        验证：
        - 创建存储桶失败抛出异常
        """
        from minio.error import S3Error
        from unittest.mock import patch

        # Arrange: Mock bucket_exists 返回 False，make_bucket 抛出异常
        with patch.object(
            self.client.client,
            "bucket_exists",
            return_value=False,
        ):
            with patch.object(
                self.client.client,
                "make_bucket",
                side_effect=S3Error(
                    code="BucketAlreadyExists",
                    message="Bucket creation failed",
                    resource="test",
                    request_id="test-id",
                    host_id="test-host",
                    response=None,
                ),
            ):
                # Act & Assert: 验证抛出异常
                with pytest.raises(S3Error):
                    self.client._ensure_bucket_exists()

    def test_ensure_bucket_exists_create_new(self) -> None:
        """测试创建新存储桶的情况。

        验证：
        - 存储桶不存在时创建成功
        - 日志正确记录
        """
        from unittest.mock import patch

        # Arrange: Mock bucket_exists 返回 False，make_bucket 成功
        with patch.object(
            self.client.client,
            "bucket_exists",
            return_value=False,
        ):
            with patch.object(
                self.client.client,
                "make_bucket",
                return_value=None,
            ):
                # Act: 调用 _ensure_bucket_exists
                self.client._ensure_bucket_exists()

                # Assert: 不抛出异常即成功


# ==============================================================================
# 错误处理测试 - Redis
# ==============================================================================
class TestRedisClientErrorHandling:
    """Redis 客户端错误处理测试类。

    测试各种异常情况的处理。
    使用 Mock 来模拟错误场景。
    """

    @pytest.fixture(autouse=True)
    def setup(self, reset_redis_singleton: None) -> Generator[None, None, None]:
        """测试前置处理。

        重置单例并创建客户端实例。
        """
        from src.storage.redis_client import RedisClient

        self.client = RedisClient()
        yield

    @pytest.mark.asyncio
    async def test_test_connection_failure(self) -> None:
        """测试连接测试失败的情况。

        验证：
        - 连接失败返回 False
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock ping 抛出 RedisError 异常
        with patch.object(
            self.client.client,
            "ping",
            new_callable=AsyncMock,
            side_effect=RedisError("Connection failed"),
        ):
            # Act: 测试连接
            result = await self.client.test_connection()

            # Assert: 验证返回 False
            assert result is False

    @pytest.mark.asyncio
    async def test_set_cache_failure(self) -> None:
        """测试设置缓存失败的情况。

        验证：
        - 设置失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock set 抛出异常
        with patch.object(
            self.client.client,
            "set",
            new_callable=AsyncMock,
            side_effect=RedisError("Set failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.set_cache("test_key", "test_value")

    @pytest.mark.asyncio
    async def test_get_cache_failure(self) -> None:
        """测试获取缓存失败的情况。

        验证：
        - 获取失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock get 抛出异常
        with patch.object(
            self.client.client,
            "get",
            new_callable=AsyncMock,
            side_effect=RedisError("Get failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.get_cache("test_key")

    @pytest.mark.asyncio
    async def test_delete_cache_failure(self) -> None:
        """测试删除缓存失败的情况。

        验证：
        - 删除失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock delete 抛出异常
        with patch.object(
            self.client.client,
            "delete",
            new_callable=AsyncMock,
            side_effect=RedisError("Delete failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.delete_cache("test_key")

    @pytest.mark.asyncio
    async def test_set_json_failure(self) -> None:
        """测试设置 JSON 失败的情况。

        验证：
        - 设置失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock set 抛出异常
        with patch.object(
            self.client.client,
            "set",
            new_callable=AsyncMock,
            side_effect=RedisError("Set JSON failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.set_json("test_key", {"key": "value"})

    @pytest.mark.asyncio
    async def test_get_json_failure(self) -> None:
        """测试获取 JSON 失败的情况。

        验证：
        - 获取失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock get 抛出异常
        with patch.object(
            self.client.client,
            "get",
            new_callable=AsyncMock,
            side_effect=RedisError("Get JSON failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.get_json("test_key")

    @pytest.mark.asyncio
    async def test_exists_failure(self) -> None:
        """测试检查键存在失败的情况。

        验证：
        - 检查失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock exists 抛出异常
        with patch.object(
            self.client.client,
            "exists",
            new_callable=AsyncMock,
            side_effect=RedisError("Exists check failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.exists("test_key")

    @pytest.mark.asyncio
    async def test_set_expire_failure(self) -> None:
        """测试设置过期时间失败的情况。

        验证：
        - 设置失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock expire 抛出异常
        with patch.object(
            self.client.client,
            "expire",
            new_callable=AsyncMock,
            side_effect=RedisError("Set expire failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.set_expire("test_key", 60)

    @pytest.mark.asyncio
    async def test_get_ttl_failure(self) -> None:
        """测试获取 TTL 失败的情况。

        验证：
        - 获取失败抛出异常
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock ttl 抛出异常
        with patch.object(
            self.client.client,
            "ttl",
            new_callable=AsyncMock,
            side_effect=RedisError("Get TTL failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(RedisError):
                await self.client.get_ttl("test_key")

    @pytest.mark.asyncio
    async def test_close_failure(self) -> None:
        """测试关闭连接失败的情况。

        验证：
        - 关闭失败不抛出异常（仅记录日志）
        """
        from redis.exceptions import RedisError
        from unittest.mock import AsyncMock, patch

        # Arrange: Mock close 抛出异常
        with patch.object(
            self.client.client,
            "close",
            new_callable=AsyncMock,
            side_effect=RedisError("Close failed"),
        ):
            # Act: 关闭连接（不应抛出异常）
            await self.client.close()

            # Assert: 不抛出异常即成功


# ==============================================================================
# 错误处理测试 - ChromaDB
# ==============================================================================
class TestChromaClientErrorHandling:
    """ChromaDB 客户端错误处理测试类。

    测试各种异常情况的处理。
    使用 Mock 来模拟错误场景。
    """

    @pytest.fixture(autouse=True)
    def setup(self, reset_chroma_singleton: None) -> Generator[None, None, None]:
        """测试前置处理。

        重置单例并创建客户端实例。
        """
        from src.storage.chroma_client import ChromaClient

        self.client = ChromaClient()
        yield

    def test_test_connection_failure(self) -> None:
        """测试连接测试失败的情况。

        验证：
        - 连接失败返回 False
        """
        from chromadb.errors import ChromaError
        from unittest.mock import patch

        # Arrange: Mock heartbeat 抛出 ChromaError 异常
        with patch.object(
            self.client.client,
            "heartbeat",
            side_effect=ChromaError("Connection failed"),
        ):
            # Act: 测试连接
            result = self.client.test_connection()

            # Assert: 验证返回 False
            assert result is False

    def test_get_collection_failure(self) -> None:
        """测试获取集合失败的情况。

        验证：
        - 获取失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import patch

        # Arrange: Mock get_or_create_collection 抛出异常
        with patch.object(
            self.client.client,
            "get_or_create_collection",
            side_effect=ChromaError("Collection failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.get_collection("test_collection")

    def test_add_documents_failure(self) -> None:
        """测试添加文档失败的情况。

        验证：
        - 添加失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import MagicMock, patch

        # Arrange: Mock collection.add 抛出异常
        mock_collection = MagicMock()
        mock_collection.add.side_effect = ChromaError("Add failed")

        with patch.object(
            self.client,
            "_get_target_collection",
            return_value=mock_collection,
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.add_documents(
                    ids=["test_id"],
                    documents=["test doc"],
                )

    def test_query_failure(self) -> None:
        """测试查询失败的情况。

        验证：
        - 查询失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import MagicMock, patch

        # Arrange: Mock collection.query 抛出异常
        mock_collection = MagicMock()
        mock_collection.query.side_effect = ChromaError("Query failed")

        with patch.object(
            self.client,
            "_get_target_collection",
            return_value=mock_collection,
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.query(query_texts=["test query"])

    def test_delete_documents_failure(self) -> None:
        """测试删除文档失败的情况。

        验证：
        - 删除失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import MagicMock, patch

        # Arrange: Mock collection.delete 抛出异常
        mock_collection = MagicMock()
        mock_collection.delete.side_effect = ChromaError("Delete failed")

        with patch.object(
            self.client,
            "_get_target_collection",
            return_value=mock_collection,
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.delete_documents(ids=["test_id"])

    def test_get_documents_failure(self) -> None:
        """测试获取文档失败的情况。

        验证：
        - 获取失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import MagicMock, patch

        # Arrange: Mock collection.get 抛出异常
        mock_collection = MagicMock()
        mock_collection.get.side_effect = ChromaError("Get failed")

        with patch.object(
            self.client,
            "_get_target_collection",
            return_value=mock_collection,
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.get_documents(ids=["test_id"])

    def test_update_documents_failure(self) -> None:
        """测试更新文档失败的情况。

        验证：
        - 更新失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import MagicMock, patch

        # Arrange: Mock collection.update 抛出异常
        mock_collection = MagicMock()
        mock_collection.update.side_effect = ChromaError("Update failed")

        with patch.object(
            self.client,
            "_get_target_collection",
            return_value=mock_collection,
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.update_documents(
                    ids=["test_id"],
                    documents=["updated doc"],
                )

    def test_count_documents_failure(self) -> None:
        """测试计数文档失败的情况。

        验证：
        - 计数失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import MagicMock, patch

        # Arrange: Mock collection.count 抛出异常
        mock_collection = MagicMock()
        mock_collection.count.side_effect = ChromaError("Count failed")

        with patch.object(
            self.client,
            "_get_target_collection",
            return_value=mock_collection,
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.count_documents()

    def test_delete_collection_failure(self) -> None:
        """测试删除集合失败的情况。

        验证：
        - 删除失败抛出异常
        """
        from chromadb.errors import ChromaError
        from unittest.mock import patch

        # Arrange: Mock delete_collection 抛出异常
        with patch.object(
            self.client.client,
            "delete_collection",
            side_effect=ChromaError("Delete collection failed"),
        ):
            # Act & Assert: 验证抛出异常
            with pytest.raises(ChromaError):
                self.client.delete_collection("test_collection")

    def test_get_target_collection_with_none(self) -> None:
        """测试 _get_target_collection 方法传入 None。

        验证：
        - 传入 None 返回默认集合
        """
        # Act: 传入 None
        result = self.client._get_target_collection(None)

        # Assert: 验证返回默认集合
        assert result is not None
        assert result.name == self.client.collection_name

    def test_get_target_collection_with_collection_object(self) -> None:
        """测试 _get_target_collection 方法传入 Collection 对象。

        验证：
        - 传入 Collection 对象直接返回
        """
        # Arrange: 获取一个集合对象
        collection = self.client.get_collection("test_direct_collection")

        # Act: 传入 Collection 对象
        result = self.client._get_target_collection(collection)

        # Assert: 验证返回相同的集合对象
        assert result is collection

        # 清理
        self.client.delete_collection("test_direct_collection")

    def test_singleton_already_initialized(self) -> None:
        """测试单例已初始化的情况。

        验证：
        - 再次创建实例返回相同的单例
        """
        from src.storage.chroma_client import ChromaClient

        # Act: 再次创建实例
        another_client = ChromaClient()

        # Assert: 验证是同一个实例
        assert another_client is self.client
