"""ChromaDB 客户端封装模块。

提供向量存储功能，包括文档嵌入、相似度查询等操作。
使用单例模式确保全局只有一个客户端实例。
"""

from typing import Any

from chromadb import Collection, PersistentClient
from chromadb.config import Settings
from chromadb.errors import ChromaError
from loguru import logger

from src.core.config import get_settings


class ChromaClient:
    """ChromaDB 客户端单例类。

    封装 ChromaDB 操作，提供向量存储功能。

    Attributes:
        _instance: 单例实例
        _initialized: 是否已初始化标志
        client: ChromaDB 客户端实例
        collection_name: 默认集合名称
    """

    _instance: "ChromaClient | None" = None
    _initialized: bool = False

    def __new__(cls) -> "ChromaClient":
        """创建或返回单例实例。

        Returns:
            ChromaClient: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化 ChromaDB 客户端。

        使用本地持久化存储，创建或获取默认集合。
        """
        if self._initialized:
            return

        settings = get_settings()
        self._persist_directory = settings.chroma.persist_dir
        self.collection_name = settings.chroma.collection

        logger.info(
            "初始化 ChromaDB 客户端: "
            f"persist_dir={self._persist_directory}, collection={self.collection_name}"
        )

        self.client = PersistentClient(
            path=self._persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        self._default_collection = self.get_collection(self.collection_name)
        ChromaClient._initialized = True

    def test_connection(self) -> bool:
        """测试 ChromaDB 连接是否正常。

        Returns:
            bool: 连接成功返回 True，否则返回 False
        """
        try:
            self.client.heartbeat()
            logger.info("ChromaDB 连接测试成功")
            return True
        except ChromaError as e:
            logger.error(f"ChromaDB 连接测试失败: {e}")
            return False

    def get_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> Collection:
        """获取或创建集合。

        Args:
            name: 集合名称
            metadata: 集合元数据

        Returns:
            Collection: 集合对象

        Raises:
            ChromaError: ChromaDB 操作错误
        """
        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata,
                embedding_function=None,
            )
            logger.info(f"获取/创建集合成功: {name}")
            return collection
        except ChromaError as e:
            logger.exception(f"获取/创建集合失败: {name}, 错误: {e}")
            raise

    def _get_target_collection(self, collection: Collection | str | None) -> Collection:
        """获取目标集合。

        Args:
            collection: 集合对象、集合名称字符串或 None

        Returns:
            Collection: 集合对象
        """
        if collection is None:
            return self._default_collection
        if isinstance(collection, str):
            return self.get_collection(collection)
        return collection

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
        collection: Collection | str | None = None,
    ) -> bool:
        """添加文档到集合。

        Args:
            ids: 文档 ID 列表
            documents: 文档内容列表
            metadatas: 元数据列表
            embeddings: 嵌入向量列表（可选，不提供则自动生成）
            collection: 目标集合（Collection 对象、集合名称字符串或 None）

        Returns:
            bool: 添加成功返回 True

        Raises:
            ChromaError: ChromaDB 操作错误
        """
        try:
            target_collection = self._get_target_collection(collection)
            target_collection.add(  # type: ignore[arg-type]
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            logger.info(f"添加文档成功: count={len(ids)}")
            return True
        except ChromaError as e:
            logger.exception(f"添加文档失败: 错误: {e}")
            raise

    def query(
        self,
        query_texts: list[str] | None = None,
        query_embeddings: list[list[float]] | None = None,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        collection: Collection | str | None = None,
    ) -> dict[str, Any]:
        """查询相似文档。

        Args:
            query_texts: 查询文本列表（自动生成嵌入）
            query_embeddings: 查询嵌入向量列表
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            collection: 目标集合（Collection 对象、集合名称字符串或 None）

        Returns:
            dict: 查询结果，包含 ids、documents、metadatas、distances

        Raises:
            ChromaError: ChromaDB 操作错误
        """
        try:
            target_collection = self._get_target_collection(collection)
            results = target_collection.query(  # type: ignore[arg-type]
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document,
            )
            result_count = len(results.get("ids", [[]])[0])
            logger.info(
                "查询成功: "
                f"query_count={len(query_texts or query_embeddings or [])}, results={result_count}"
            )
            return dict(results)
        except ChromaError as e:
            logger.exception(f"查询失败: 错误: {e}")
            raise

    def delete_documents(
        self,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        collection: Collection | str | None = None,
    ) -> bool:
        """删除文档。

        Args:
            ids: 要删除的文档 ID 列表
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            collection: 目标集合（Collection 对象、集合名称字符串或 None）

        Returns:
            bool: 删除成功返回 True

        Raises:
            ChromaError: ChromaDB 操作错误
        """
        try:
            target_collection = self._get_target_collection(collection)
            target_collection.delete(  # type: ignore[arg-type]
                ids=ids,
                where=where,
                where_document=where_document,
            )
            logger.info(f"删除文档成功: ids={ids}")
            return True
        except ChromaError as e:
            logger.exception(f"删除文档失败: 错误: {e}")
            raise

    def get_documents(
        self,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        collection: Collection | str | None = None,
    ) -> dict[str, Any]:
        """获取文档。

        Args:
            ids: 文档 ID 列表
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            collection: 目标集合（Collection 对象、集合名称字符串或 None）

        Returns:
            dict: 文档数据，包含 ids、documents、metadatas

        Raises:
            ChromaError: ChromaDB 操作错误
        """
        try:
            target_collection = self._get_target_collection(collection)
            results = target_collection.get(  # type: ignore[arg-type]
                ids=ids,
                where=where,
                where_document=where_document,
            )
            logger.info(f"获取文档成功: count={len(results.get('ids', []))}")
            return dict(results)
        except ChromaError as e:
            logger.exception(f"获取文档失败: 错误: {e}")
            raise

    def update_documents(
        self,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
        collection: Collection | str | None = None,
    ) -> bool:
        """更新文档。

        Args:
            ids: 文档 ID 列表
            documents: 新文档内容列表
            metadatas: 新元数据列表
            embeddings: 新嵌入向量列表
            collection: 目标集合（Collection 对象、集合名称字符串或 None）

        Returns:
            bool: 更新成功返回 True

        Raises:
            ChromaError: ChromaDB 操作错误
        """
        try:
            target_collection = self._get_target_collection(collection)
            target_collection.update(  # type: ignore[arg-type]
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            logger.info(f"更新文档成功: count={len(ids)}")
            return True
        except ChromaError as e:
            logger.exception(f"更新文档失败: 错误: {e}")
            raise

    def count_documents(self, collection: Collection | str | None = None) -> int:
        """获取集合中的文档数量。

        Args:
            collection: 目标集合（Collection 对象、集合名称字符串或 None）

        Returns:
            int: 文档数量
        """
        try:
            target_collection = self._get_target_collection(collection)
            count = target_collection.count()
            logger.debug(f"文档数量: {count}")
            return count
        except ChromaError as e:
            logger.exception(f"获取文档数量失败: 错误: {e}")
            raise

    def delete_collection(self, name: str) -> bool:
        """删除集合。

        Args:
            name: 集合名称

        Returns:
            bool: 删除成功返回 True
        """
        try:
            self.client.delete_collection(name=name)
            logger.info(f"删除集合成功: {name}")
            return True
        except ChromaError as e:
            logger.exception(f"删除集合失败: {name}, 错误: {e}")
            raise


chroma_client = ChromaClient()
