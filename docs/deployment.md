# 部署指南

## 环境要求

### 硬件要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 20 GB | 50 GB+ SSD |

### 软件要求

| 软件 | 版本要求 |
|------|----------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| Python | 3.13+ |
| uv | 最新版 |

## 部署方式

### 方式一：Docker Compose 部署（推荐）

#### 1. 准备配置文件

```bash
# 克隆项目
git clone <repository-url>
cd ResumeScreening

# 复制环境变量配置
cp .env.example .env
```

#### 2. 配置环境变量

编辑 `.env` 文件，配置必要参数：

```bash
# 应用配置
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_AES_KEY=your-aes-key-at-least-32-bytes!
APP_LLM_TIMEOUT=30
APP_LLM_MAX_RETRIES=3

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-bytes!
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MySQL 配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-secure-password
MYSQL_DATABASE=resume_screening

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# MinIO 配置
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_BUCKET=resume-images

# DeepSeek LLM 配置
DS_API_KEY=your-deepseek-api-key
DS_BASE_URL=https://api.deepseek.com
DS_MODEL=deepseek-chat

# DashScope Embedding 配置
DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3
```

#### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

#### 4. 初始化系统

```bash
# 进入后端容器
docker-compose exec backend bash

# 初始化管理员账户
uv run python scripts/init_admin.py
```

#### 5. 访问服务

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost |
| API 文档 | http://localhost:8000/docs |
| MinIO 控制台 | http://localhost:9001 |

### 方式二：本地开发部署

#### 1. 安装依赖

```bash
# 安装 uv
pip install uv

# 安装项目依赖
uv sync
```

#### 2. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置，修改以下配置为本地服务
MYSQL_HOST=localhost
REDIS_HOST=localhost
MINIO_ENDPOINT=localhost:9000
```

#### 3. 启动依赖服务

```bash
# 仅启动 MySQL、Redis、MinIO
docker-compose up -d mysql redis minio
```

#### 4. 初始化数据库

```bash
# 创建数据库表
uv run python scripts/init_db.py

# 创建管理员账户
uv run python scripts/init_admin.py
```

#### 5. 启动后端服务

```bash
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 6. 启动前端服务

```bash
cd frontend-new
python -m http.server 3000
```

## 服务配置详解

### MySQL 配置

```yaml
mysql:
  image: mysql:8.0
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_PASSWORD}
    MYSQL_DATABASE: resume_screening
    MYSQL_CHARACTER_SET_SERVER: utf8mb4
    MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
  volumes:
    - mysql-data:/var/lib/mysql
```

**优化建议**:
- 生产环境设置强密码
- 配置定期备份
- 根据数据量调整 `innodb_buffer_pool_size`

### Redis 配置

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  volumes:
    - redis-data:/data
```

**优化建议**:
- 生产环境设置密码
- 根据需求调整 `maxmemory`

### MinIO 配置

```yaml
minio:
  image: minio/minio:latest
  environment:
    MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
    MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
  command: server /data --console-address ":9001"
```

**优化建议**:
- 生产环境使用分布式模式
- 配置 HTTPS
- 设置 Bucket 策略

### 后端服务配置

```yaml
backend:
  build:
    context: .
    dockerfile: Dockerfile
  environment:
    - APP_DEBUG=${APP_DEBUG:-false}
    - MYSQL_HOST=${MYSQL_HOST:-mysql}
    # ... 其他环境变量
  volumes:
    - backend-logs:/app/logs
    - chroma-data:/app/data/chroma
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## 生产环境部署

### 1. 安全加固

#### HTTPS 配置

使用 Nginx 反向代理配置 HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://frontend;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 密码安全

- 使用强密码（至少 16 位，包含大小写字母、数字、特殊字符）
- 定期更换密码
- 不同服务使用不同密码

### 2. 性能优化

#### 后端优化

```yaml
backend:
  environment:
    - UVICORN_WORKERS=4
    - UVICORN_THREADS=2
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

#### MySQL 优化

```ini
[mysqld]
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
max_connections = 500
query_cache_size = 0
```

### 3. 监控配置

#### 日志收集

```yaml
backend:
  logging:
    driver: "json-file"
    options:
      max-size: "100m"
      max-file: "10"
```

#### 健康检查

所有服务都配置了健康检查：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### 4. 备份策略

#### MySQL 备份

```bash
# 每日备份脚本
#!/bin/bash
BACKUP_DIR=/backup/mysql
DATE=$(date +%Y%m%d)
docker-compose exec -T mysql mysqldump -u root -p${MYSQL_PASSWORD} resume_screening > ${BACKUP_DIR}/resume_screening_${DATE}.sql
# 保留最近 7 天备份
find ${BACKUP_DIR} -name "*.sql" -mtime +7 -delete
```

#### MinIO 备份

```bash
# 使用 mc 命令行工具
mc mirror local/resume-images /backup/minio/resume-images
```

## 常见问题

### 1. 服务启动失败

**问题**: MySQL 连接失败

**解决方案**:
```bash
# 检查 MySQL 是否就绪
docker-compose logs mysql

# 等待 MySQL 完全启动
docker-compose exec mysql mysql -u root -p -e "SELECT 1"
```

### 2. 内存不足

**问题**: 容器内存不足

**解决方案**:
```bash
# 检查内存使用
docker stats

# 调整 Docker 内存限制
# 在 docker-compose.yml 中添加：
deploy:
  resources:
    limits:
      memory: 4G
```

### 3. 网络问题

**问题**: 容器间无法通信

**解决方案**:
```bash
# 检查网络
docker network ls
docker network inspect resume-network

# 重建网络
docker-compose down
docker-compose up -d
```

### 4. ChromaDB 数据丢失

**问题**: 重启后向量数据丢失

**解决方案**:
确保 ChromaDB 数据目录挂载正确：
```yaml
volumes:
  - chroma-data:/app/data/chroma
```

## 运维命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启单个服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 数据管理

```bash
# 进入 MySQL
docker-compose exec mysql mysql -u root -p

# 进入 Redis
docker-compose exec redis redis-cli

# 进入后端容器
docker-compose exec backend bash
```

### 清理操作

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 完全清理（谨慎使用）
docker-compose down -v --rmi all
```
