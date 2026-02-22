# 系统监控性能优化与 Redis 连接问题修复计划

## 问题分析

### 1. Redis 连接错误根本原因

**错误信息**：`Error while reading from 39.108.222.138:6379 : (10054, '远程主机强迫关闭了一个现有的连接。')`

**日志分析**：
- Redis 连接测试成功后，间隔几分钟再测试就会失败
- 例如：03:55:41 成功 → 03:55:43 失败（间隔 2 秒）
- 这表明连接池中的空闲连接被 Redis 服务器断开

**根本原因**：
1. **Redis 服务器端断开空闲连接**：远程 Redis 服务器配置了 `timeout` 参数，会断开空闲超过一定时间的连接
2. **连接池没有健康检查**：当前连接池配置没有 `health_check_interval`，无法自动检测和重建失效连接
3. **没有重试机制**：当连接失效时，没有自动重试

### 2. 系统监控检查慢的原因

**日志分析**：
- 某次检查 MySQL 延迟高达 **19255ms（19秒）**
- 其他服务延迟正常（Redis 53ms, MinIO 29ms, ChromaDB 1ms）

**原因**：
- 4 个服务检查是**顺序执行**的，不是并行
- 如果某个服务响应慢，整体检查时间会很长
- 没有设置超时限制

## 解决方案

### 1. Redis 连接优化

**修改文件**：`src/storage/redis_client.py`

添加以下配置：
```python
self._pool = ConnectionPool(
    host=self._host,
    port=self._port,
    password=self._password,
    db=self._db,
    decode_responses=True,
    max_connections=10,
    socket_timeout=5,              # 读写超时 5 秒
    socket_connect_timeout=5,      # 连接超时 5 秒
    health_check_interval=30,      # 每 30 秒检查连接健康
    retry_on_timeout=True,         # 超时时自动重试
)
```

**效果**：
- `socket_timeout`：防止读写操作长时间阻塞
- `socket_connect_timeout`：防止连接建立长时间等待
- `health_check_interval`：连接池自动检测失效连接并重建
- `retry_on_timeout`：超时时自动重试一次

### 2. 系统监控并行检查

**修改文件**：`src/api/v1/monitor.py`

将顺序检查改为并行检查：
```python
# 并行执行所有服务检查，设置超时限制
services = await asyncio.gather(
    asyncio.wait_for(check_mysql_status(), timeout=5),
    asyncio.wait_for(check_redis_status(), timeout=3),
    asyncio.wait_for(check_minio_status(), timeout=5),
    asyncio.wait_for(check_chroma_status(), timeout=3),
    return_exceptions=True,
)
```

**效果**：
- 4 个服务并行检查，总时间取决于最慢的服务
- 每个服务有超时限制，不会无限等待
- 单个服务超时不影响其他服务

## 实施步骤

1. 修改 `src/storage/redis_client.py` - 添加连接池健康检查和超时配置
2. 修改 `src/api/v1/monitor.py` - 并行执行服务检查，添加超时限制

## 预期效果

- Redis 连接更稳定，自动重连失效连接
- 系统健康检查时间从最长 4 个服务等待时间变为最长 1 个服务等待时间（约 5 秒）
- 单个服务超时不会阻塞整体检查
