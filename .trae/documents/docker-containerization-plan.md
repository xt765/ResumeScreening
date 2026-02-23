# ResumeScreening 项目 Docker 容器化评估与实施计划

## 一、项目现状评估

### 1.1 目录结构

```
ResumeScreening/
├── src/                    # 后端源代码
│   ├── api/               # FastAPI 路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic 模式
│   ├── services/          # 业务服务
│   ├── storage/           # 存储客户端
│   ├── utils/             # 工具函数
│   ├── parsers/           # 文档解析器
│   └── workflows/         # LangGraph 工作流
├── frontend-new/          # 前端静态文件
├── tests/                 # 测试文件
├── Dockerfile             # 后端 Dockerfile（需优化）
├── docker-compose.yml     # 容器编排配置（需完善）
├── .dockerignore          # Docker 忽略文件
└── pyproject.toml         # 项目配置
```

### 1.2 需要容器化的组件

| 组件 | 类型 | 当前状态 | 说明 |
|------|------|----------|------|
| FastAPI 后端 | 应用服务 | 已配置，需优化 | 缺少系统依赖 |
| 前端静态文件 | 应用服务 | **未配置** | 当前使用 Python http.server |
| MySQL 8.0 | 数据库 | 已配置 | 生产就绪 |
| Redis 7 | 缓存 | 已配置 | 生产就绪 |
| MinIO | 对象存储 | 已配置 | 生产就绪 |
| ChromaDB | 向量数据库 | 本地持久化 | 需评估独立部署 |

### 1.3 关键依赖分析

**Python 依赖**：
- `opencv-python>=4.8.0` - 人脸检测，**需要系统依赖**
- `pymupdf>=1.24.0` - PDF 解析
- `chromadb>=0.5.0` - 向量数据库

**系统级依赖需求**（OpenCV）：
```
libgl1-mesa-glx
libglib2.0-0
libsm6
libxext6
libxrender-dev
```

### 1.4 现有配置问题

| 问题 | 影响 | 优先级 |
|------|------|--------|
| Dockerfile 缺少 OpenCV 系统依赖 | 容器启动失败 | **高** |
| 缺少前端服务配置 | 无法统一部署 | **高** |
| 缺少 .env.example | 环境变量文档不完整 | **中** |
| 缺少资源限制 | 安全风险 | **中** |
| 缺少 CI/CD 配置 | 手动部署效率低 | **低** |

---

## 二、实施计划

### 阶段一：基础优化（高优先级）

#### 任务 1：更新 Dockerfile
- [ ] 添加 OpenCV 系统依赖（libgl1、libglib2.0 等）
- [ ] 优化健康检查命令（使用 curl 替代 httpx）
- [ ] 清理 apt 缓存减少镜像大小

#### 任务 2：创建前端服务配置
- [ ] 创建 `Dockerfile.frontend`（基于 nginx:alpine）
- [ ] 创建 `nginx.conf` 配置文件
  - 静态文件托管
  - API 代理转发
  - WebSocket 支持
  - Gzip 压缩

#### 任务 3：完善 docker-compose.yml
- [ ] 添加 frontend 服务
- [ ] 配置服务依赖关系
- [ ] 添加资源限制（可选）

#### 任务 4：创建环境变量模板
- [ ] 创建 `.env.example` 文件
- [ ] 包含所有必要的环境变量说明

### 阶段二：安全加固（中优先级）

#### 任务 5：安全配置
- [ ] 配置只读文件系统
- [ ] 添加资源限制（CPU、内存）
- [ ] 配置安全选项（no-new-privileges）

### 阶段三：CI/CD 集成（低优先级）

#### 任务 6：自动化构建
- [ ] 创建 GitHub Actions 工作流
- [ ] 配置镜像缓存
- [ ] 设置自动测试和部署

---

## 三、文件变更清单

### 新增文件

| 文件路径 | 说明 |
|----------|------|
| `Dockerfile.frontend` | 前端服务 Dockerfile |
| `nginx.conf` | Nginx 配置文件 |
| `.env.example` | 环境变量模板 |

### 修改文件

| 文件路径 | 变更内容 |
|----------|----------|
| `Dockerfile` | 添加系统依赖、优化健康检查 |
| `docker-compose.yml` | 添加前端服务、完善配置 |

---

## 四、预期成果

### 4.1 服务架构

```
                    ┌─────────────────┐
                    │   Frontend      │
                    │   (Nginx:80)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Backend │  │  MinIO   │  │  MySQL   │
        │  (:8000) │  │  (:9000) │  │  (:3306) │
        └────┬─────┘  └──────────┘  └──────────┘
             │
     ┌───────┼───────┐
     │       │       │
     ▼       ▼       ▼
┌────────┐ ┌──────┐ ┌────────┐
│ Redis  │ │Chroma│ │DeepSeek│
│(:6379) │ │  DB  │ │  API   │
└────────┘ └──────┘ └────────┘
```

### 4.2 镜像大小预估

| 镜像 | 预估大小 |
|------|----------|
| resume-backend | ~500MB |
| resume-frontend | ~25MB |
| mysql:8.0 | ~550MB |
| redis:7-alpine | ~40MB |
| minio/minio | ~80MB |

### 4.3 启动命令

```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f backend

# 重新构建
docker-compose build --no-cache
```

---

## 五、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| OpenCV 系统依赖兼容性 | 容器启动失败 | 使用标准 Debian/Ubuntu 基础镜像 |
| ChromaDB 多实例冲突 | 数据不一致 | 当前单实例部署，后续可独立部署 |
| 环境变量泄露 | 安全风险 | 使用 .env 文件，不提交到版本控制 |

---

## 六、时间估算

| 阶段 | 预计时间 |
|------|----------|
| 阶段一：基础优化 | 1-2 小时 |
| 阶段二：安全加固 | 30 分钟 |
| 阶段三：CI/CD 集成 | 1 小时 |
| **总计** | **2.5-3.5 小时** |

---

## 七、确认事项

请确认以下内容后开始实施：

1. ✅ 是否同意新增 `Dockerfile.frontend`、`nginx.conf`、`.env.example` 文件？
2. ✅ 是否同意修改现有 `Dockerfile` 和 `docker-compose.yml`？
3. ✅ 是否需要配置 CI/CD 自动化构建（阶段三）？
4. ✅ 是否需要添加监控服务（Prometheus/Grafana）？
