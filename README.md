# 人才简历智能筛选与管理系统

基于 LangChain + LangGraph + FastAPI 的智能简历筛选平台，集成 LLM 实现简历解析、智能筛选和 RAG 智能问答。

## 核心特性

- **智能简历解析**: 支持 PDF/DOCX 格式，自动提取文本和图片
- **LLM 信息提取**: 使用 DeepSeek 大模型提取候选人结构化信息
- **多条件智能筛选**: 支持学历、技能、工作年限等多维度筛选
- **RAG 智能问答**: 基于向量检索的简历智能问答系统
- **实时进度推送**: WebSocket 实时推送处理进度
- **人脸检测**: 自动检测简历照片中的人脸

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | >=0.120.0 |
| LLM 框架 | LangChain | >=1.2.0 |
| 工作流引擎 | LangGraph | >=1.0.0 |
| 数据库 | MySQL 8.0 | - |
| 缓存 | Redis 7 | - |
| 对象存储 | MinIO | - |
| 向量数据库 | ChromaDB | >=0.5.0 |
| LLM | DeepSeek | - |
| Embedding | DashScope | - |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (HTML/CSS/JS)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI 后端服务                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Auth    │ │ Talents │ │Analysis │ │ Monitor │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph 工作流引擎                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ParseExtract  │ → │   Filter    │ → │    Store    │       │
│  │    Node      │   │    Node     │   │    Node     │       │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                              ↓                               │
│                     ┌──────────────┐                        │
│                     │ Cache Node   │                        │
│                     └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    MySQL     │     │    MinIO     │     │   ChromaDB   │
│  (关系数据)   │     │  (图片存储)   │     │  (向量存储)   │
└──────────────┘     └──────────────┘     └──────────────┘
```

## 快速开始

### 环境要求

- Python 3.13+
- Docker & Docker Compose
- uv 包管理器

### 本地开发

```bash
# 克隆项目
git clone <repository-url>
cd ResumeScreening

# 安装依赖
uv sync

# 复制环境变量配置
cp .env.example .env

# 初始化数据库
uv run python scripts/init_db.py

# 创建管理员账户
uv run python scripts/init_admin.py

# 启动后端服务
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端服务（新终端）
cd frontend-new && python -m http.server 3000
```

### Docker 部署

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| API 文档 | http://localhost:8000/docs |
| ReDoc 文档 | http://localhost:8000/redoc |
| MinIO 控制台 | http://localhost:9001 |

## 项目结构

```
ResumeScreening/
├── docs/                    # 项目文档
│   ├── architecture.md      # 架构设计
│   ├── api.md               # API 文档
│   ├── deployment.md        # 部署指南
│   └── development.md       # 开发指南
├── frontend-new/            # 前端代码
│   ├── index.html
│   ├── css/
│   └── js/
│       ├── app.js           # 应用入口
│       ├── api.js           # API 封装
│       └── pages/           # 页面模块
├── src/                     # 后端代码
│   ├── api/                 # API 路由
│   │   └── v1/              # v1 版本 API
│   ├── core/                # 核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── security.py      # 安全加密
│   │   └── exceptions.py    # 异常定义
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic 模式
│   ├── services/            # 业务服务
│   ├── storage/             # 存储客户端
│   ├── utils/               # 工具函数
│   └── workflows/           # LangGraph 工作流
├── scripts/                 # 脚本工具
├── tests/                   # 测试代码
├── docker-compose.yml       # Docker 编排
├── Dockerfile               # 后端镜像
├── Dockerfile.frontend      # 前端镜像
├── pyproject.toml           # 项目配置
└── README.md                # 项目说明
```

## 核心模块

### 1. LangGraph 工作流

系统采用 LangGraph 构建 4 节点工作流：

| 节点 | 功能 |
|------|------|
| ParseExtractNode | 文档解析、文本提取、LLM 实体提取 |
| FilterNode | LLM 条件筛选判断 |
| StoreNode | MySQL 存储、MinIO 图片存储、ChromaDB 向量存储 |
| CacheNode | Redis 缓存结果 |

### 2. API 模块

| 模块 | 路径 | 功能 |
|------|------|------|
| auth | /api/v1/auth | 用户认证登录 |
| users | /api/v1/users | 用户管理 |
| conditions | /api/v1/conditions | 筛选条件管理 |
| talents | /api/v1/talents | 简历上传、查询、管理 |
| analysis | /api/v1/analysis | RAG 智能问答 |
| monitor | /api/v1/monitor | 系统监控 |

### 3. 存储服务

| 服务 | 用途 |
|------|------|
| MySQL | 人才信息、筛选条件、用户数据 |
| MinIO | 简历照片存储 |
| Redis | 任务状态、缓存数据 |
| ChromaDB | 简历向量存储 |

## 配置说明

主要环境变量配置（详见 `.env.example`）：

```bash
# 应用配置
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_AES_KEY=your-aes-key-at-least-32-bytes!

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-bytes!
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=resume_screening

# DeepSeek LLM 配置
DS_API_KEY=your-deepseek-api-key
DS_BASE_URL=https://api.deepseek.com
DS_MODEL=deepseek-chat

# DashScope Embedding 配置
DASHSCOPE_API_KEY=your-dashscope-api-key
```

## 开发指南

### 代码规范

- 使用 **ruff** 进行代码格式化
- 使用 **basedpyright** 进行类型检查
- 使用 **pytest** 进行测试
- 测试覆盖率要求 >= 95%

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行带覆盖率报告
uv run pytest --cov=src --cov-report=html

# 运行特定测试
uv run pytest tests/test_workflows.py -v
```

### 代码检查

```bash
# 格式化代码
uv run ruff format src/

# 代码检查
uv run ruff check src/

# 类型检查
uv run basedpyright src/
```

## 文档

- [架构设计文档](docs/architecture.md)
- [API 接口文档](docs/api.md)
- [部署指南](docs/deployment.md)
- [开发指南](docs/development.md)

## 许可证

MIT License
