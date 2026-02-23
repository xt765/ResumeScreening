# Deployment Guide

## Environment Requirements

### Hardware Requirements

| Config | Minimum | Recommended |
|--------|---------|-------------|
| CPU | 2 Cores | 4 Cores+ |
| Memory | 4 GB | 8 GB+ |
| Disk | 20 GB | 50 GB+ SSD |

### Software Requirements

| Software | Version |
|----------|---------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| Python | 3.13+ |
| uv | Latest |

## Deployment Methods

### Method 1: Docker Compose Deployment (Recommended)

#### 1. Prepare Configuration Files

```bash
# Clone project
git clone <repository-url>
cd ResumeScreening

# Copy environment variable config
cp .env.example .env
```

#### 2. Configure Environment Variables

Edit `.env` file, configure required parameters:

```bash
# Application config
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_AES_KEY=your-aes-key-at-least-32-bytes!
APP_LLM_TIMEOUT=30
APP_LLM_MAX_RETRIES=3

# JWT config
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-bytes!
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MySQL config
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-secure-password
MYSQL_DATABASE=resume_screening

# Redis config
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# MinIO config
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_BUCKET=resume-images

# DeepSeek LLM config
DS_API_KEY=your-deepseek-api-key
DS_BASE_URL=https://api.deepseek.com
DS_MODEL=deepseek-chat

# DashScope Embedding config
DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3
```

#### 3. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# View service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

#### 4. Initialize System

```bash
# Enter backend container
docker-compose exec backend bash

# Initialize admin account
uv run python scripts/init_admin.py
```

#### 5. Access Services

| Service | Address |
|---------|---------|
| Frontend | http://localhost |
| API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

### Method 2: Local Development Deployment

#### 1. Install Dependencies

```bash
# Install uv
pip install uv

# Install project dependencies
uv sync
```

#### 2. Configure Environment Variables

```bash
# Copy config file
cp .env.example .env

# Edit config, modify following configs to local services
MYSQL_HOST=localhost
REDIS_HOST=localhost
MINIO_ENDPOINT=localhost:9000
```

#### 3. Start Dependency Services

```bash
# Start MySQL, Redis, MinIO only
docker-compose up -d mysql redis minio
```

#### 4. Initialize Database

```bash
# Create database tables
uv run python scripts/init_db.py

# Create admin account
uv run python scripts/init_admin.py
```

#### 5. Start Backend Service

```bash
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 6. Start Frontend Service

```bash
cd frontend-new
python -m http.server 3000
```

## Service Configuration Details

### MySQL Configuration

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

**Optimization Suggestions**:
- Set strong password in production
- Configure regular backups
- Adjust `innodb_buffer_pool_size` based on data volume

### Redis Configuration

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  volumes:
    - redis-data:/data
```

**Optimization Suggestions**:
- Set password in production
- Adjust `maxmemory` based on needs

### MinIO Configuration

```yaml
minio:
  image: minio/minio:latest
  environment:
    MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
    MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
  command: server /data --console-address ":9001"
```

**Optimization Suggestions**:
- Use distributed mode in production
- Configure HTTPS
- Set Bucket policies

### Backend Service Configuration

```yaml
backend:
  build:
    context: .
    dockerfile: Dockerfile
  environment:
    - APP_DEBUG=${APP_DEBUG:-false}
    - MYSQL_HOST=${MYSQL_HOST:-mysql}
    # ... other environment variables
  volumes:
    - backend-logs:/app/logs
    - chroma-data:/app/data/chroma
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Production Deployment

### 1. Security Hardening

#### HTTPS Configuration

Use Nginx reverse proxy to configure HTTPS:

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

#### Password Security

- Use strong passwords (at least 16 characters, including uppercase, lowercase, numbers, special characters)
- Change passwords regularly
- Use different passwords for different services

### 2. Performance Optimization

#### Backend Optimization

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

#### MySQL Optimization

```ini
[mysqld]
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
max_connections = 500
query_cache_size = 0
```

### 3. Monitoring Configuration

#### Log Collection

```yaml
backend:
  logging:
    driver: "json-file"
    options:
      max-size: "100m"
      max-file: "10"
```

#### Health Check

All services are configured with health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### 4. Backup Strategy

#### MySQL Backup

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/backup/mysql
DATE=$(date +%Y%m%d)
docker-compose exec -T mysql mysqldump -u root -p${MYSQL_PASSWORD} resume_screening > ${BACKUP_DIR}/resume_screening_${DATE}.sql
# Keep last 7 days backups
find ${BACKUP_DIR} -name "*.sql" -mtime +7 -delete
```

#### MinIO Backup

```bash
# Use mc command line tool
mc mirror local/resume-images /backup/minio/resume-images
```

## Common Issues

### 1. Service Startup Failure

**Problem**: MySQL connection failed

**Solution**:
```bash
# Check if MySQL is ready
docker-compose logs mysql

# Wait for MySQL to fully start
docker-compose exec mysql mysql -u root -p -e "SELECT 1"
```

### 2. Insufficient Memory

**Problem**: Container memory insufficient

**Solution**:
```bash
# Check memory usage
docker stats

# Adjust Docker memory limit
# Add in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 4G
```

### 3. Network Issues

**Problem**: Containers cannot communicate

**Solution**:
```bash
# Check network
docker network ls
docker network inspect resume-network

# Rebuild network
docker-compose down
docker-compose up -d
```

### 4. ChromaDB Data Loss

**Problem**: Vector data lost after restart

**Solution**:
Ensure ChromaDB data directory is mounted correctly:
```yaml
volumes:
  - chroma-data:/app/data/chroma
```

## Operations Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart single service
docker-compose restart backend

# View service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Data Management

```bash
# Enter MySQL
docker-compose exec mysql mysql -u root -p

# Enter Redis
docker-compose exec redis redis-cli

# Enter backend container
docker-compose exec backend bash
```

### Cleanup Operations

```bash
# Clean unused images
docker image prune -a

# Clean unused volumes
docker volume prune

# Complete cleanup (use with caution)
docker-compose down -v --rmi all
```
