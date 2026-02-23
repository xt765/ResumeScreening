# 人才简历智能筛选与管理系统

> 基于 LangChain + LangGraph + FastAPI 的企业级智能简历筛选平台，集成大语言模型实现简历智能解析、多条件筛选和 RAG 智能问答。

## 项目背景

在企业招聘过程中，HR 每天需要处理大量简历，传统人工筛选方式存在以下痛点：

| 痛点 | 描述 |
|------|------|
| 效率低下 | 人工阅读一份简历平均需要 3-5 分钟 |
| 标准不一 | 不同 HR 筛选标准存在主观差异 |
| 信息遗漏 | 容易遗漏关键信息或优秀候选人 |
| 难以追溯 | 筛选结果缺乏数据支撑和可追溯性 |
| 查询困难 | 海量简历难以快速检索和统计分析 |

本系统利用大语言模型（LLM）技术，实现简历的**智能解析**、**自动筛选**和**智能问答**，大幅提升招聘效率。

## 核心优势

### 1. 智能化程度高

```mermaid
graph LR
    A[传统方式] --> B[人工阅读简历]
    B --> C[主观判断筛选]
    C --> D[手动录入信息]
    
    E[本系统] --> F[AI自动解析]
    F --> G[LLM智能筛选]
    G --> H[结构化存储]
    
    style A fill:#ffcccc
    style E fill:#ccffcc
```

- **智能解析**：自动提取姓名、学历、技能、工作经历等 20+ 字段
- **智能筛选**：基于 LLM 的语义理解，支持自然语言筛选条件
- **智能问答**：RAG 技术实现简历库智能问答，如"有哪些 5 年经验的 Java 开发？"

### 2. 技术架构先进

```mermaid
graph TB
    subgraph 前端层
        UI[响应式 Web 界面]
        WS[WebSocket 实时通信]
    end
    
    subgraph API层
        FastAPI[FastAPI 异步框架]
        Auth[JWT 认证]
        Route[RESTful 路由]
    end
    
    subgraph 工作流层
        LG[LangGraph 状态机]
        Node1[解析节点]
        Node2[筛选节点]
        Node3[存储节点]
        Node4[缓存节点]
    end
    
    subgraph AI层
        LLM[DeepSeek 大模型]
        EMB[DashScope 向量化]
        RAG[RAG 检索增强]
    end
    
    subgraph 存储层
        MySQL[(MySQL)]
        Redis[(Redis)]
        MinIO[(MinIO)]
        Chroma[(ChromaDB)]
    end
    
    UI --> FastAPI
    WS --> FastAPI
    FastAPI --> LG
    LG --> Node1 --> Node2 --> Node3 --> Node4
    Node1 --> LLM
    Node3 --> EMB
    Node3 --> MySQL
    Node3 --> MinIO
    Node3 --> Chroma
    Node4 --> Redis
    RAG --> LLM
    RAG --> Chroma
```

### 3. 功能完整丰富

| 功能模块 | 功能描述 | 技术亮点 |
|----------|----------|----------|
| 简历上传 | 支持 PDF/DOCX 批量上传 | 异步处理、进度实时推送 |
| 智能解析 | 自动提取结构化信息 | LLM 实体提取、人脸检测 |
| 条件筛选 | 多维度智能筛选 | LLM 语义理解、条件组合 |
| 智能问答 | 自然语言查询简历库 | RAG + 向量检索 |
| 系统监控 | 实时监控服务状态 | 健康检查、日志分析 |

### 4. 性能优异

```mermaid
graph LR
    subgraph 性能指标
        A[单份简历处理<br/>3-5秒]
        B[批量上传<br/>支持50+文件]
        C[向量检索<br/>毫秒级响应]
        D[并发处理<br/>异步架构]
    end
```

| 指标 | 数值 | 说明 |
|------|------|------|
| 单份简历处理时间 | 3-5 秒 | 含解析、筛选、存储全流程 |
| 批量上传支持 | 50+ 文件 | 异步后台处理 |
| 向量检索延迟 | <100ms | 千级数据量 |
| 系统可用性 | 99.9% | Docker 容器化部署 |

## 系统架构

### 整体架构图

```mermaid
graph TB
    subgraph 用户层
        User[用户/HR]
    end
    
    subgraph 接入层
        Nginx[Nginx 反向代理]
    end
    
    subgraph 应用层
        API[FastAPI 服务]
        WSS[WebSocket 服务]
    end
    
    subgraph 工作流引擎
        WF[LangGraph 工作流]
    end
    
    subgraph AI 服务
        LLM[DeepSeek LLM]
        EMB[DashScope Embedding]
    end
    
    subgraph 数据层
        DB[(MySQL 8.0)]
        Cache[(Redis 7)]
        OSS[(MinIO)]
        Vec[(ChromaDB)]
    end
    
    User --> Nginx
    Nginx --> API
    Nginx --> WSS
    API --> WF
    WSS --> WF
    WF --> LLM
    WF --> EMB
    WF --> DB
    WF --> Cache
    WF --> OSS
    WF --> Vec
```

### 技术选型

```mermaid
mindmap
  root((技术栈))
    后端
      FastAPI
        异步高性能
        自动API文档
      LangChain
        LLM应用框架
        统一接口
      LangGraph
        状态机工作流
        可视化编排
    AI
      DeepSeek
        国产大模型
        性价比高
      DashScope
        阿里云服务
        中文优化
    存储
      MySQL
        关系数据
        事务支持
      Redis
        高速缓存
        任务队列
      MinIO
        对象存储
        S3兼容
      ChromaDB
        向量存储
        轻量级
    前端
      HTML/CSS/JS
        原生实现
        无框架依赖
      WebSocket
        实时通信
        进度推送
```

## 核心工作流

### 简历处理流程

```mermaid
graph TB
    subgraph 开始
        A([用户上传简历])
    end
    
    subgraph ParseExtractNode[解析提取节点]
        B1[解析文档<br/>PDF/DOCX]
        B2[提取文本内容]
        B3[提取图片]
        B4[LLM提取信息]
        B5[人脸检测]
        B1 --> B2 --> B3 --> B4 --> B5
    end
    
    subgraph FilterNode[筛选判断节点]
        C1[获取筛选条件]
        C2[构建筛选Prompt]
        C3[LLM判断]
        C4[生成筛选原因]
        C1 --> C2 --> C3 --> C4
    end
    
    subgraph StoreNode[数据存储节点]
        D1[加密敏感信息]
        D2[保存MySQL]
        D3[上传MinIO]
        D4[向量存ChromaDB]
        D1 --> D2 --> D3 --> D4
    end
    
    subgraph CacheNode[缓存节点]
        E1[缓存Redis]
        E2[更新状态]
        E3[推送进度]
        E1 --> E2 --> E3
    end
    
    subgraph 结束
        F([返回结果])
    end
    
    A --> B1
    B5 --> C1
    C4 --> D1
    D4 --> E1
    E3 --> F
```

### RAG 智能问答流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as API
    participant E as Embedding
    participant C as ChromaDB
    participant L as LLM
    
    U->>A: 提交问题
    A->>E: 问题向量化
    E-->>A: 返回向量
    A->>C: 向量相似度检索
    C-->>A: 返回相关简历
    A->>L: 构建 Prompt + 上下文
    L-->>A: 生成回答
    A-->>U: 返回结果+来源
```

## 功能模块

### 1. 用户认证模块

```mermaid
graph LR
    A[登录请求] --> B{验证用户名密码}
    B -->|成功| C[生成JWT Token]
    B -->|失败| D[返回错误]
    C --> E[返回Token]
    E --> F[后续请求携带Token]
    F --> G{验证Token}
    G -->|有效| H[允许访问]
    G -->|无效| I[拒绝访问]
```

| 功能 | 描述 |
|------|------|
| 用户登录 | 用户名密码登录，返回 JWT Token |
| 权限控制 | admin/hr/viewer 三级权限 |
| Token 刷新 | Token 过期自动刷新机制 |

### 2. 简历管理模块

```mermaid
graph TB
    subgraph 上传
        A[选择文件] --> B[格式校验]
        B --> C[批量上传]
        C --> D[后台处理]
    end
    
    subgraph 处理
        D --> E[解析文档]
        E --> F[提取信息]
        F --> G[智能筛选]
        G --> H[存储数据]
    end
    
    subgraph 管理
        H --> I[列表查询]
        I --> J[详情查看]
        J --> K[状态更新]
        K --> L[批量操作]
    end
```

### 3. 筛选条件模块

支持多维度筛选条件组合：

```mermaid
graph LR
    A[筛选条件] --> B[学历要求]
    A --> C[技能要求]
    A --> D[工作年限]
    A --> E[院校层级]
    A --> F[自定义条件]
    
    B --> B1[专科/本科/硕士/博士]
    C --> C1[技能列表+熟练度]
    D --> D1[最低年限/最高年限]
    E --> E1[985/211/双一流]
    F --> F1[自然语言描述]
```

### 4. 智能分析模块

```mermaid
graph TB
    A[用户提问] --> B{问题类型}
    B -->|人才查询| C[向量检索]
    B -->|统计分析| D[数据聚合]
    B -->|推荐排序| E[相似度计算]
    
    C --> F[召回相关简历]
    D --> G[生成统计报告]
    E --> H[排序推荐]
    
    F --> I[LLM生成回答]
    G --> I
    H --> I
    
    I --> J[返回结果]
```

## 数据模型

### ER 图

```mermaid
erDiagram
    User ||--o{ TalentInfo : manages
    Condition ||--o{ TalentInfo : filters
    
    User {
        string id PK
        string username UK
        string password_hash
        string role
        boolean is_active
    }
    
    TalentInfo {
        string id PK
        string name
        string phone
        string email
        string education_level
        string school
        string major
        int work_years
        json skills
        string screening_status
        string content_hash
    }
    
    Condition {
        string id PK
        string name
        json conditions
        string description
    }
```

## 快速开始

### 环境要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.13+ | 核心开发语言 |
| Docker | 24.0+ | 容器化部署 |
| Docker Compose | 2.20+ | 服务编排 |
| uv | 最新版 | Python 包管理器 |

### 本地开发

```bash
# 1. 克隆项目
git clone https://gitee.com/xt765/resume-screening.git
cd resume-screening

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要参数

# 4. 启动依赖服务
docker-compose up -d mysql redis minio

# 5. 初始化数据库
uv run python scripts/init_db.py
uv run python scripts/init_admin.py

# 6. 启动后端服务
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 7. 启动前端服务（新终端）
cd frontend-new && python -m http.server 3000
```

### Docker 部署

```bash
# 一键启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | 用户操作界面 |
| API 文档 | http://localhost:8000/docs | Swagger 交互文档 |
| ReDoc | http://localhost:8000/redoc | ReDoc 文档 |
| MinIO 控制台 | http://localhost:9001 | 图片存储管理 |

## 项目结构

```
ResumeScreening/
├── docs/                      # 项目文档
│   ├── architecture.md        # 架构设计
│   ├── api.md                 # API 文档
│   ├── deployment.md          # 部署指南
│   └── development.md         # 开发指南
├── frontend-new/              # 前端代码
│   ├── index.html             # 入口页面
│   ├── css/                   # 样式文件
│   └── js/                    # JavaScript
│       ├── app.js             # 应用入口
│       ├── api.js             # API 封装
│       └── pages/             # 页面模块
├── src/                       # 后端代码
│   ├── api/                   # API 路由
│   ├── core/                  # 核心模块
│   ├── models/                # 数据模型
│   ├── schemas/               # Pydantic 模式
│   ├── services/              # 业务服务
│   ├── storage/               # 存储客户端
│   ├── utils/                 # 工具函数
│   └── workflows/             # LangGraph 工作流
├── scripts/                   # 脚本工具
├── tests/                     # 测试代码
├── docker-compose.yml         # Docker 编排
├── Dockerfile                 # 后端镜像
├── pyproject.toml             # 项目配置
└── README.md                  # 项目说明
```

## 技术亮点

### 1. LangGraph 状态机工作流

```mermaid
stateDiagram-v2
    [*] --> ParseExtract
    ParseExtract --> Filter
    Filter --> Store
    Store --> Cache
    Cache --> [*]
    
    ParseExtract --> Error: 解析失败
    Filter --> Error: 筛选失败
    Store --> Error: 存储失败
    Error --> [*]
```

- 状态可持久化，支持断点续传
- 节点可独立测试和复用
- 支持并行节点执行

### 2. RAG 检索增强生成

```mermaid
graph LR
    Q[用户问题] --> E[向量化]
    E --> R[向量检索]
    R --> C[构建上下文]
    C --> P[Prompt工程]
    P --> L[LLM生成]
    L --> A[回答]
```

- 简历向量化存储，支持语义检索
- 多轮对话上下文管理
- 检索结果可追溯

### 3. 多级缓存策略

```mermaid
graph TB
    A[请求] --> B{Redis缓存}
    B -->|命中| C[返回缓存]
    B -->|未命中| D{查询数据库}
    D -->|找到| E[写入缓存]
    E --> F[返回结果]
    D -->|未找到| G[返回空]
```

### 4. 安全设计

- **数据加密**：敏感信息（手机号、邮箱）AES 加密存储
- **密码安全**：bcrypt 哈希存储
- **JWT 认证**：无状态 Token 认证
- **权限控制**：三级角色权限体系

## 开发指南

### 代码规范

| 工具 | 用途 |
|------|------|
| ruff | 代码格式化 |
| basedpyright | 类型检查 |
| pytest | 单元测试 |
| pytest-cov | 覆盖率报告 |

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 带覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 代码检查

```bash
# 格式化
uv run ruff format src/

# 检查
uv run ruff check src/

# 类型检查
uv run basedpyright src/
```

## 文档

- [架构设计文档](docs/architecture.md) - 详细的系统架构设计说明
- [API 接口文档](docs/api.md) - 完整的 REST API 接口文档
- [部署指南](docs/deployment.md) - Docker 部署详细步骤
- [开发指南](docs/development.md) - 开发环境搭建和代码规范

## 许可证

MIT License
