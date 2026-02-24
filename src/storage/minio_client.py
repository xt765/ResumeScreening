"""MinIO 客户端封装模块。

提供图片存储功能，包括上传、获取、删除图片等操作。
使用单例模式确保全局只有一个客户端实例。
"""

import io
import os
import shutil
from pathlib import Path
from typing import BinaryIO

from loguru import logger
from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

from src.core.config import get_settings


class MinIOClient:
    """MinIO 客户端单例类。

    封装 MinIO 操作，提供图片存储功能。
    支持自动降级到本地文件存储（当 MinIO 不可用时）。

    Attributes:
        _instance: 单例实例
        _initialized: 是否已初始化标志
        client: Minio 客户端实例
        bucket_name: 默认存储桶名称
        _use_local_storage: 是否使用本地存储模式
        _local_storage_dir: 本地存储目录
    """

    _instance: "MinIOClient | None" = None
    _initialized: bool = False
    _use_local_storage: bool = False
    _local_storage_dir: Path = Path("data/minio_mock")

    def __new__(cls) -> "MinIOClient":
        """创建或返回单例实例。

        Returns:
            MinIOClient: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化 MinIO 客户端。

        从配置中读取连接信息并创建客户端实例。
        确保 bucket 存在。
        """
        if self._initialized:
            return

        settings = get_settings()
        self._endpoint = settings.minio.endpoint
        self._access_key = settings.minio.access_key
        self._secret_key = settings.minio.secret_key
        self._secure = settings.minio.secure
        self.bucket_name = settings.minio.bucket

        logger.info(
            f"初始化 MinIO 客户端: endpoint={self._endpoint}, "
            f"bucket={self.bucket_name}, secure={self._secure}"
        )

        self.client = Minio(
            self._endpoint,
            access_key=self._access_key,
            secret_key=self._secret_key,
            secure=self._secure,
        )

        try:
            self._ensure_bucket_exists()
        except Exception as e:
            logger.warning(f"MinIO 连接失败，切换到本地存储模式: {e}")
            self._use_local_storage = True
            self._ensure_local_dir_exists()

        MinIOClient._initialized = True

    def _ensure_local_dir_exists(self) -> None:
        """确保本地存储目录存在。"""
        if not self._local_storage_dir.exists():
            self._local_storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建本地存储目录: {self._local_storage_dir}")
        
        # 确保 bucket 目录存在
        bucket_dir = self._local_storage_dir / self.bucket_name
        if not bucket_dir.exists():
            bucket_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_bucket_exists(self) -> None:
        """确保存储桶存在，不存在则创建。

        Raises:
            S3Error: MinIO 操作错误
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建存储桶: {self.bucket_name}")
            else:
                logger.debug(f"存储桶已存在: {self.bucket_name}")
        except S3Error as e:
            logger.exception(f"确保存储桶存在时发生错误: {e}")
            raise

    def test_connection(self) -> bool:
        """测试 MinIO 连接是否正常。

        Returns:
            bool: 连接成功返回 True，否则返回 False
        """
        if self._use_local_storage:
            return True
            
        try:
            self.client.bucket_exists(self.bucket_name)
            logger.info("MinIO 连接测试成功")
            return True
        except Exception as e:
            logger.error(f"MinIO 连接测试失败: {e}")
            return False

    def upload_image(
        self,
        object_name: str,
        data: BinaryIO | bytes,
        content_type: str = "image/png",
        metadata: dict[str, str | list[str]] | None = None,
    ) -> str:
        """上传图片到 MinIO。

        Args:
            object_name: 对象名称（存储路径）
            data: 图片数据（文件对象或字节）
            content_type: 内容类型，默认 image/png
            metadata: 元数据字典

        Returns:
            str: 图片访问 URL

        Raises:
            S3Error: MinIO 操作错误
        """
        # 本地存储模式
        if self._use_local_storage:
            try:
                file_path = self._local_storage_dir / self.bucket_name / object_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                mode = "wb"
                if isinstance(data, bytes):
                    with open(file_path, mode) as f:
                        f.write(data)
                else:
                    data.seek(0)
                    with open(file_path, mode) as f:
                        shutil.copyfileobj(data, f)
                
                url = f"file://{file_path.absolute()}"
                logger.info(f"图片上传成功(本地): {object_name}, Path: {url}")
                return url
            except Exception as e:
                logger.exception(f"上传图片失败(本地): {object_name}, 错误: {e}")
                raise

        try:
            # 处理字节数据
            if isinstance(data, bytes):
                data = io.BytesIO(data)
                data_size = len(data.getvalue())
            else:
                data.seek(0, 2)  # 移动到末尾获取大小
                data_size = data.tell()
                data.seek(0)  # 回到开头

            self.client.put_object(  # type: ignore[arg-type]
                self.bucket_name,
                object_name,
                data,
                data_size,
                content_type=content_type,
                metadata=metadata,
            )

            url = f"http://{self._endpoint}/{self.bucket_name}/{object_name}"
            logger.info(f"图片上传成功: {object_name}, URL: {url}")
            return url

        except S3Error as e:
            logger.exception(f"上传图片失败: {object_name}, 错误: {e}")
            raise

    def get_image(self, object_name: str) -> bytes | None:
        """从 MinIO 获取图片。

        Args:
            object_name: 对象名称（存储路径）

        Returns:
            bytes | None: 图片字节数据，不存在返回 None
        """
        if self._use_local_storage:
            try:
                file_path = self._local_storage_dir / self.bucket_name / object_name
                if not file_path.exists():
                    logger.debug(f"图片不存在(本地): {object_name}")
                    return None
                
                with open(file_path, "rb") as f:
                    data = f.read()
                logger.info(f"获取图片成功(本地): {object_name}, 大小: {len(data)} bytes")
                return data
            except Exception as e:
                logger.exception(f"获取图片失败(本地): {object_name}, 错误: {e}")
                raise

        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"获取图片成功: {object_name}, 大小: {len(data)} bytes")
            return data

        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.debug(f"图片不存在: {object_name}")
                return None
            logger.exception(f"获取图片失败: {object_name}, 错误: {e}")
            raise

    def delete_image(self, object_name: str) -> bool:
        """从 MinIO 删除图片。

        Args:
            object_name: 对象名称（存储路径）

        Returns:
            bool: 删除成功返回 True，图片不存在返回 False
        """
        if self._use_local_storage:
            try:
                file_path = self._local_storage_dir / self.bucket_name / object_name
                if not file_path.exists():
                    logger.debug(f"图片不存在(本地)，无需删除: {object_name}")
                    return False
                
                os.remove(file_path)
                logger.info(f"删除图片成功(本地): {object_name}")
                return True
            except Exception as e:
                logger.exception(f"删除图片失败(本地): {object_name}, 错误: {e}")
                raise

        try:
            # 先检查图片是否存在
            self.client.stat_object(self.bucket_name, object_name)
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"删除图片成功: {object_name}")
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.debug(f"图片不存在，无需删除: {object_name}")
                return False
            logger.exception(f"删除图片失败: {object_name}, 错误: {e}")
            raise

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """获取图片的预签名 URL。

        Args:
            object_name: 对象名称（存储路径）
            expires: URL 过期时间（秒），默认 1 小时

        Returns:
            str: 预签名 URL

        Raises:
            S3Error: MinIO 操作错误
        """
        if self._use_local_storage:
             file_path = self._local_storage_dir / self.bucket_name / object_name
             return f"file://{file_path.absolute()}"

        try:
            from datetime import timedelta

            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires),
            )
            logger.debug(f"获取预签名 URL: {object_name}")
            return url

        except S3Error as e:
            logger.exception(f"获取预签名 URL 失败: {object_name}, 错误: {e}")
            raise

    def image_exists(self, object_name: str) -> bool:
        """检查图片是否存在。

        Args:
            object_name: 对象名称（存储路径）

        Returns:
            bool: 存在返回 True，否则返回 False
        """
        if self._use_local_storage:
            file_path = self._local_storage_dir / self.bucket_name / object_name
            return file_path.exists()

        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False


# 创建全局单例实例
minio_client = MinIOClient()
