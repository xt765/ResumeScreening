#!/bin/bash
# ==================== 人才简历智能筛选系统启动脚本 ====================
# 用途：Docker 容器启动脚本，等待依赖服务就绪后启动应用

set -e

# ==================== 配置变量 ====================
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8501}"

# 依赖服务配置
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
MINIO_HOST="${MINIO_HOST:-minio}"
MINIO_PORT="${MINIO_PORT:-9000}"

# 最大等待时间（秒）
MAX_WAIT="${MAX_WAIT:-120}"
WAIT_INTERVAL="${WAIT_INTERVAL:-2}"

# ==================== 颜色输出 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==================== 健康检查函数 ====================

"""检查 TCP 端口是否可用。"""
check_tcp_port() {
    local host="$1"
    local port="$2"
    local service="$3"

    # 使用 Python 检查端口（因为容器内可能没有 nc）
    python -c "
import socket
import sys
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex(('$host', $port))
sock.close()
sys.exit(0 if result == 0 else 1)
" 2>/dev/null
}

"""等待服务就绪。"""
wait_for_service() {
    local host="$1"
    local port="$2"
    local service="$3"
    local count=0
    local max_count=$((MAX_WAIT / WAIT_INTERVAL))

    log_info "等待 $service 服务就绪 ($host:$port)..."

    while ! check_tcp_port "$host" "$port" "$service"; do
        count=$((count + 1))
        if [ $count -ge $max_count ]; then
            log_error "$service 服务在 ${MAX_WAIT} 秒内未就绪，退出启动"
            exit 1
        fi
        log_warning "$service 服务未就绪，${WAIT_INTERVAL} 秒后重试... ($count/$max_count)"
        sleep $WAIT_INTERVAL
    done

    log_success "$service 服务已就绪"
}

"""等待 MySQL 就绪。"""
wait_for_mysql() {
    local count=0
    local max_count=$((MAX_WAIT / WAIT_INTERVAL))

    log_info "等待 MySQL 数据库就绪..."

    while ! python -c "
import pymysql
import sys
try:
    conn = pymysql.connect(
        host='$MYSQL_HOST',
        port=$MYSQL_PORT,
        user='${MYSQL_USER:-root}',
        password='${MYSQL_PASSWORD:-root123}',
        connect_timeout=2
    )
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
        count=$((count + 1))
        if [ $count -ge $max_count ]; then
            log_error "MySQL 服务在 ${MAX_WAIT} 秒内未就绪，退出启动"
            exit 1
        fi
        log_warning "MySQL 服务未就绪，${WAIT_INTERVAL} 秒后重试... ($count/$max_count)"
        sleep $WAIT_INTERVAL
    done

    log_success "MySQL 数据库已就绪"
}

"""等待 Redis 就绪。"""
wait_for_redis() {
    local count=0
    local max_count=$((MAX_WAIT / WAIT_INTERVAL))

    log_info "等待 Redis 缓存就绪..."

    while ! python -c "
import redis
import sys
try:
    client = redis.Redis(
        host='$REDIS_HOST',
        port=$REDIS_PORT,
        socket_connect_timeout=2
    )
    client.ping()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
        count=$((count + 1))
        if [ $count -ge $max_count ]; then
            log_error "Redis 服务在 ${MAX_WAIT} 秒内未就绪，退出启动"
            exit 1
        fi
        log_warning "Redis 服务未就绪，${WAIT_INTERVAL} 秒后重试... ($count/$max_count)"
        sleep $WAIT_INTERVAL
    done

    log_success "Redis 缓存已就绪"
}

"""等待 MinIO 就绪。"""
wait_for_minio() {
    local count=0
    local max_count=$((MAX_WAIT / WAIT_INTERVAL))

    log_info "等待 MinIO 对象存储就绪..."

    while ! python -c "
import httpx
import sys
try:
    response = httpx.get(
        'http://$MINIO_HOST:$MINIO_PORT/minio/health/live',
        timeout=2.0
    )
    sys.exit(0 if response.status_code == 200 else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
        count=$((count + 1))
        if [ $count -ge $max_count ]; then
            log_error "MinIO 服务在 ${MAX_WAIT} 秒内未就绪，退出启动"
            exit 1
        fi
        log_warning "MinIO 服务未就绪，${WAIT_INTERVAL} 秒后重试... ($count/$max_count)"
        sleep $WAIT_INTERVAL
    done

    log_success "MinIO 对象存储已就绪"
}

# ==================== 主函数 ====================

main() {
    log_info "=========================================="
    log_info "人才简历智能筛选系统启动中..."
    log_info "=========================================="

    # 等待依赖服务就绪
    log_info "检查依赖服务状态..."

    # 并行等待所有服务（提高启动速度）
    wait_for_mysql &
    local mysql_pid=$!

    wait_for_redis &
    local redis_pid=$!

    wait_for_minio &
    local minio_pid=$!

    # 等待所有检查完成
    wait $mysql_pid
    wait $redis_pid
    wait $minio_pid

    log_success "所有依赖服务已就绪"

    # 根据服务类型启动不同的应用
    if [ "${SERVICE_TYPE}" = "backend" ]; then
        log_info "启动后端服务 (FastAPI)..."
        exec uvicorn src.api.main:app \
            --host "$BACKEND_HOST" \
            --port "$BACKEND_PORT" \
            --workers "${UVICORN_WORKERS:-1}" \
            --log-level "${LOG_LEVEL:-info}"
    elif [ "${SERVICE_TYPE}" = "frontend" ]; then
        log_info "启动前端服务 (Streamlit)..."
        exec streamlit run frontend/app.py \
            --server.port "$FRONTEND_PORT" \
            --server.address "0.0.0.0" \
            --server.headless true \
            --browser.gatherUsageStats false
    else
        log_error "未知的服务类型: ${SERVICE_TYPE}"
        log_info "请设置环境变量 SERVICE_TYPE=backend 或 SERVICE_TYPE=frontend"
        exit 1
    fi
}

# ==================== 执行主函数 ====================
main "$@"
