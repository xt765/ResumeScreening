# ==================== 后端服务 Dockerfile ====================
# 多阶段构建优化镜像大小

# ==================== 构建阶段 ====================
FROM python:3.13-slim AS builder

# 设置工作目录
WORKDIR /build

# 安装 uv 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 设置环境变量
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# 复制依赖文件
COPY pyproject.toml .

# 安装依赖到虚拟环境
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache -e .

# ==================== 运行阶段 ====================
FROM python:3.13-slim AS runner

# 设置工作目录
WORKDIR /app

# 创建非 root 用户
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # 应用配置
    APP_DEBUG=false \
    APP_LOG_LEVEL=INFO \
    APP_LOG_DIR=logs

# 复制源代码
COPY --chown=appuser:appgroup src ./src
COPY --chown=appuser:appgroup pyproject.toml .

# 创建日志和数据目录
RUN mkdir -p logs data/chroma && \
    chown -R appuser:appgroup logs data

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)" || exit 1

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
