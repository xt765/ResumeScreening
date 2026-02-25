<div align="center">
  <img src="https://i-blog.csdnimg.cn/direct/8abea218c2804256a17cc8f2d6c81630.jpeg" width="150" >
  <h1><strong>玄同 765</strong></h1>
  <p><strong>大语言模型 (LLM) 开发工程师 | 中国传媒大学 · 数字媒体技术（智能交互与游戏设计）</strong></p>
  <p>
    <a href="https://blog.csdn.net/Yunyi_Chi" target="_blank" style="text-decoration: none;">
      <span style="background-color: #f39c12; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; display: inline-block;">CSDN · 个人主页 |</span>
    </a>
    <a href="https://github.com/xt765" target="_blank" style="text-decoration: none; margin-left: 8px;">
      <span style="background-color: #24292e; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; display: inline-block;">GitHub · Follow</span>
    </a>
  </p>
</div>

---

### **关于作者**

- **深耕领域**：大语言模型开发 / RAG 知识库 / AI Agent 落地 / 模型微调
- **技术栈**：Python | RAG (LangChain / Dify + Milvus) | FastAPI + Docker
- **工程能力**：专注模型工程化部署、知识库构建与优化，擅长全流程解决方案

> **「让 AI 交互更智能，让技术落地更高效」**
> 欢迎技术探讨与项目合作，解锁大模型与智能交互的无限可能！

---
# 【开源发布】简历智能筛选系统 - 基于 LangGraph 的企业级招聘自动化方案

> 作者：玄同765 (xt765)
> 
> 项目地址：[GitHub - ResumeScreening](https://github.com/xt765/ResumeScreening)
> 
> 国内镜像：[Gitee - ResumeScreening](https://gitee.com/xt765/resume-screening)

---

## 摘要

简历智能筛选系统是一个基于 LangChain v1.2 和 LangGraph v1.0 构建的企业级智能简历处理平台。它不是又一个简单的 LLM 封装，而是一个深思熟虑的架构设计，专注于解决招聘领域的核心痛点：

- **如何让简历处理效率提升 60 倍？** — 通过 LangGraph 状态机工作流
- **如何让筛选标准统一可控？** — 通过 LLM 语义理解 + 复杂布尔逻辑
- **如何让简历库智能问答？** — 通过 Agentic RAG 检索增强生成技术
- **如何实现检索结果更精准？** — 通过加权 RRF 混合检索算法
- **如何实现零依赖极速部署？** — 通过 Local Fallback 本地回退机制

本文将深入剖析系统的架构设计，带你了解一个生产级简历筛选系统的诞生过程。

---

## 一、为什么需要智能简历筛选？

### 1.1 传统招聘的痛点

在 AI 技术飞速发展的今天，企业招聘依然面临着效率瓶颈。作为一名深耕大语言模型开发的工程师，我在观察 HR 日常工作后发现：

| 痛点 | 描述 | 影响 |
|------|------|------|
| 效率低下 | 人工阅读一份简历平均需要 3-5 分钟 | 招聘周期长，错失优秀人才 |
| 标准不一 | 不同 HR 筛选标准存在主观差异 | 筛选结果不可控，质量参差不齐 |
| 信息遗漏 | 容易遗漏关键信息或优秀候选人 | 人才流失，招聘成本增加 |
| 难以追溯 | 筛选结果缺乏数据支撑和可追溯性 | 无法复盘优化筛选标准 |
| 查询困难 | 海量简历难以快速检索和统计分析 | 数据价值无法挖掘 |

### 1.2 传统方案 vs 本系统

传统人工筛选与本系统对比如下：

```mermaid
graph LR
    subgraph Legacy [传统招聘流程]
        direction LR
        A1[人工阅读简历] --> A2{主观判断}
        A2 -->|通过| A3[手动录入Excel]
        A2 -->|淘汰| A4[丢弃]
        A3 --> A5[人工检索查找]
    end
    style Legacy fill:#f8f9fa,stroke:#dee2e6
    style A1 fill:#fff3cd,stroke:#e0c97f
    style A2 fill:#f8d7da,stroke:#e8b4b8
    style A3 fill:#fff3cd,stroke:#e0c97f
    style A4 fill:#f8d7da,stroke:#e8b4b8
    style A5 fill:#fff3cd,stroke:#e0c97f
```
```mermaid
graph LR
    subgraph System [智能筛选系统]
        direction LR
        B1[AI自动解析] --> B2{LLM智能筛选}
        B2 -->|自动结构化| B3[多维数据库]
        B3 --> B4[自然语言问答]
    end
    style System fill:#e8f4f8,stroke:#7fb3d5
    style B1 fill:#d4edda,stroke:#90c695
    style B2 fill:#fff3cd,stroke:#e0c97f
    style B3 fill:#e2d4f0,stroke:#b8a9d0
    style B4 fill:#fce4ec,stroke:#f0b8c4
```


**对比说明**：

| 维度 | 传统方式 | 本系统 | 提升 |
|------|----------|--------|------|
| 处理速度 | 3-5 分钟/份 | 3-5 秒/份 | **60倍** |
| 信息提取 | 手动录入，易遗漏 | AI 自动提取 20+ 字段 | **100%覆盖** |
| 筛选标准 | 主观判断，因人而异 | LLM 语义理解，标准统一 | **一致性保障** |
| 数据检索 | 翻阅文件或 Excel | 自然语言智能问答 | **秒级响应** |

### 1.3 为什么选择 LLM + LangGraph？

传统方案如规则引擎、关键词匹配存在明显局限：

| 对比维度 | 传统方案 | LLM + LangGraph |
|----------|----------|-----------------|
| 信息提取 | 规则/正则 | 语义理解，自动提取 20+ 字段 |
| 筛选判断 | 关键词匹配 | 自然语言条件，语义匹配 |
| 数据检索 | SQL 查询 | Agentic RAG 智能问答 |
| 可扩展性 | 需修改代码 | 配置化，零代码扩展 |
| 处理速度 | 依赖人工 | 3-5 秒/份，效率提升 60 倍 |

---

## 二、系统架构设计

### 2.1 整体架构

系统采用分层架构设计，各层职责清晰：

```mermaid
graph TD
    User((用户/HR))
    
    subgraph Frontend [前端交互层]
        UI[Web 界面]
        Monitor[监控面板]
    end

    subgraph Gateway [网关层]
        API_GW[API 网关 / 负载均衡]
    end

    subgraph Service [后端服务层]
        Auth[认证服务]
        Resume[简历管理]
        Analysis[智能分析]
        Workflow[工作流引擎]
    end

    subgraph AI_Core [AI 能力层]
        LLM[DeepSeek LLM]
        Embedding[向量化模型]
        RAG[RAG 检索引擎]
    end

    subgraph Data [数据存储层]
        MySQL[(MySQL)]
        Redis[(Redis)]
        MinIO[(MinIO)]
        Chroma[(ChromaDB)]
    end

    User <--> Frontend
    Frontend <--> Gateway
    Gateway <--> Service
    Service <--> AI_Core
    Service <--> Data

    style User fill:#e8f4f8,stroke:#7fb3d5
    style Frontend fill:#d4edda,stroke:#90c695
    style Gateway fill:#fff3cd,stroke:#e0c97f
    style Service fill:#e2d4f0,stroke:#b8a9d0
    style AI_Core fill:#fce4ec,stroke:#f0b8c4
    style Data fill:#e8f4f8,stroke:#7fb3d5
```

**架构设计理念**：

1. **分层解耦**：前端、API、工作流、AI、存储各层独立，降低耦合度
2. **异步处理**：FastAPI 原生支持异步，批量上传后台处理不阻塞
3. **状态管理**：LangGraph 状态机管理工作流，支持断点续传和错误恢复
4. **多模态存储与回退**：支持 MySQL/Redis/MinIO 标准模式，同时也支持 SQLite/Memory/LocalFS 的纯本地开发模式，实现"零依赖"快速启动。

### 2.2 微服务架构

系统采用微服务架构思想设计，支持容器化部署和水平扩展：

```mermaid
graph TD
    User((用户)) --> Nginx[Nginx 网关]
    
    subgraph App_Layer [应用服务]
        API[FastAPI 后端]
        WS[WebSocket 服务]
    end
    
    subgraph Workflow_Layer [工作流引擎]
        LangGraph[LangGraph 状态机]
        
        subgraph Nodes [处理节点]
            N1[解析提取]
            N2[智能筛选]
            N3[数据存储]
            N4[缓存通知]
        end
    end
    
    subgraph AI_Layer [AI 能力]
        LLM[DeepSeek API]
        Embedding[DashScope API]
        RAG[RAG 引擎]
    end
    
    subgraph Data_Layer [数据存储]
        MySQL[(MySQL)]
        Redis[(Redis)]
        MinIO[(MinIO)]
        Chroma[(ChromaDB)]
    end
    
    Nginx --> API
    Nginx --> WS
    
    API --> LangGraph
    WS --> LangGraph
    
    LangGraph --> N1 --> N2 --> N3 --> N4
    
    N1 --> LLM
    N2 --> LLM
    N3 --> MySQL
    N3 --> MinIO
    N3 --> Chroma
    N3 --> Embedding
    N4 --> Redis
    
    RAG --> LLM
    RAG --> Chroma
    RAG --> Embedding
    
    style User fill:#e8f4f8,stroke:#7fb3d5
    style Nginx fill:#d4edda,stroke:#90c695
    style App_Layer fill:#fff3cd,stroke:#e0c97f
    style Workflow_Layer fill:#e2d4f0,stroke:#b8a9d0
    style AI_Layer fill:#fce4ec,stroke:#f0b8c4
    style Data_Layer fill:#e8f4f8,stroke:#7fb3d5
    style Nodes fill:#fff,stroke:#e2d4f0
```

**各层职责说明**：

| 层级 | 组件 | 职责 |
|------|------|------|
| 用户接入层 | 浏览器 | 用户交互界面，响应式设计适配多终端 |
| 网关接入层 | Nginx | 反向代理、负载均衡、SSL 证书、静态资源服务 |
| 应用服务层 | FastAPI + WebSocket | 业务逻辑处理、API 接口、实时通信 |
| 工作流引擎层 | LangGraph | 简历处理流程编排、状态管理、错误处理 |
| AI 能力层 | DeepSeek + DashScope | 文本理解、信息提取、向量化、智能问答 |
| 数据存储层 | MySQL/Redis/MinIO/ChromaDB | 数据持久化、缓存、文件存储、向量检索 |

### 2.3 核心技术选型

| 层级 | 技术选型 | 版本 | 选型理由 |
|------|----------|------|----------|
| 后端框架 | FastAPI | >=0.120.0 | 异步高性能，自动生成 API 文档，类型提示友好 |
| LLM 框架 | LangChain | >=1.2.0 | 成熟的 LLM 应用开发框架，统一的大模型调用接口 |
| 工作流引擎 | LangGraph | >=1.0.0 | 状态机工作流，支持可视化编排，便于复杂业务流程管理 |
| 大模型 | DeepSeek | - | 国产大模型，中文理解能力强，API 价格低廉 |
| 向量化 | DashScope | - | 阿里云服务，中文语义效果好，稳定可靠 |
| 数据库 | MySQL | 8.0 | 成熟的关系数据库，支持事务，社区活跃 |
| 缓存 | Redis | 7 | 高性能内存数据库，支持多种数据结构 |
| 对象存储 | MinIO | - | S3 兼容的私有化对象存储，部署简单 |
| 向量数据库 | ChromaDB | >=0.5.0 | 轻量级向量存储，无需额外依赖 |

---

## 三、LangGraph 工作流设计

### 3.1 为什么选择 LangGraph？

在简历处理场景中，我们需要处理复杂的业务流程：

1. 文档解析（PDF/DOCX）
2. 信息提取（LLM）
3. 智能筛选（LLM）
4. 数据存储（多存储）
5. 结果缓存（Redis）

传统方案如 Celery 任务队列存在以下问题：

| 痛点 | Celery | LangGraph |
|------|--------|-----------|
| 状态管理 | 需要额外实现 | 内置状态持久化 |
| 流程可视化 | 不支持 | 原生支持 |
| 错误恢复 | 手动重试 | 节点级重试 |
| 调试困难 | 需要查看日志 | 可视化追踪 |

### 3.2 四节点状态机设计

简历处理采用 LangGraph 状态机工作流，分为 4 个节点顺序执行：

```mermaid
graph TD
    Start([开始]) --> Upload[用户上传简历]
    
    subgraph P1 [阶段一：智能解析]
        direction TB
        Upload --> Parse{文件类型?}
        Parse -->|PDF/DOCX| Extract[文本/图片提取]
        Extract --> LLM1[LLM 信息抽取]
        LLM1 --> Face[人脸检测]
    end
    
    subgraph P2 [阶段二：智能筛选]
        direction TB
        Face --> Cond[加载筛选条件]
        Cond --> Prompt[构建筛选 Prompt]
        Prompt --> LLM2[LLM 语义判断]
        LLM2 --> Reason[生成筛选理由]
    end
    
    subgraph P3 [阶段三：数据存储]
        direction TB
        Reason --> Encrypt[敏感信息加密]
        Encrypt --> SaveDB[(MySQL 存储)]
        SaveDB --> SaveOSS[(MinIO 存储)]
        SaveOSS --> Embed[文本向量化]
        Embed --> SaveVec[(ChromaDB 存储)]
    end
    
    subgraph P4 [阶段四：反馈通知]
        direction TB
        SaveVec --> Cache[Redis 缓存结果]
        Cache --> Notify[WebSocket 推送进度]
    end

    Notify --> End([流程结束])

    style Start fill:#e8f4f8,stroke:#7fb3d5
    style End fill:#e8f4f8,stroke:#7fb3d5
    style P1 fill:#e8f4f8,stroke:#7fb3d5
    style P2 fill:#d4edda,stroke:#90c695
    style P3 fill:#fff3cd,stroke:#e0c97f
    style P4 fill:#e2d4f0,stroke:#b8a9d0
```

**各节点详细说明**：

#### ParseExtractNode - 解析提取节点

**职责**：将非结构化简历文档转换为结构化数据

**处理步骤**：
1. **文档解析**：根据文件类型选择解析器
   - PDF：使用 PyMuPDF (fitz) 提取文本和嵌入图片
   - DOCX：使用 python-docx 提取文本和图片
2. **文本提取**：保留段落格式，便于 LLM 理解上下文
3. **图片提取**：提取简历中的证件照
4. **LLM 信息提取**：调用 DeepSeek 大模型，提取 20+ 字段
5. **人脸检测**：使用 OpenCV Haar 级联分类器检测照片中的人脸

#### FilterNode - 筛选判断节点

**职责**：根据预设条件判断候选人是否符合要求

**处理步骤**：
1. **获取筛选条件**：从数据库读取条件配置
2. **构建筛选 Prompt**：将条件转换为自然语言描述
3. **LLM 判断**：调用大模型进行语义理解匹配
4. **复杂逻辑运算**：支持 AND/OR/NOT 等复杂布尔逻辑组合，确保筛选结果的精确性
5. **生成筛选原因**：详细说明符合/不符合的具体原因

#### StoreNode - 数据存储节点

**职责**：持久化存储处理结果

**处理步骤**：
1. **加密敏感信息**：使用 AES 对称加密手机号、邮箱
2. **保存 MySQL**：存储人才信息到 `talent_info` 表
3. **上传 MinIO**：存储简历照片，生成访问 URL
4. **向量存储**：生成简历文本向量，存入 ChromaDB

#### CacheNode - 缓存节点

**职责**：缓存处理结果，推送实时进度

**处理步骤**：
1. **缓存 Redis**：存储处理结果，设置过期时间
2. **更新任务状态**：更新数据库中的任务记录
3. **WebSocket 推送**：实时通知前端处理进度

### 3.3 工作流状态机图

```mermaid
stateDiagram-v2
    [*] --> ParseExtract: 提交简历
    
    state ParseExtract {
        [*] --> Analyzing: 文档解析
        Analyzing --> Extracting: 内容提取
        Extracting --> [*]: 提取成功
    }
    
    ParseExtract --> Filter: 解析完成
    ParseExtract --> Error: 解析失败
    
    state Filter {
        [*] --> Matching: 规则匹配
        Matching --> Judging: LLM判断
        Judging --> [*]: 筛选完成
    }
    
    Filter --> Store: 筛选完成
    Filter --> Error: 筛选失败
    
    state Store {
        [*] --> Encrypting: 数据加密
        Encrypting --> Saving: 多库写入
        Saving --> [*]: 存储完成
    }
    
    Store --> Cache: 存储成功
    Store --> Error: 存储失败
    
    Cache --> [*]: 任务结束
    Error --> [*]: 异常终止
    
    note right of Error
        记录错误日志
        通知用户重试
    end note
```

**技术优势**：
- **状态持久化**：每个节点的状态保存到数据库，支持断点续传
- **可视化编排**：工作流可视化，便于理解和调试
- **独立测试**：每个节点可独立单元测试，提高代码质量
- **错误恢复**：失败节点可重试，无需重新执行整个流程

---

## 四、Agentic RAG 智能问答设计

### 4.1 为什么选择 Agentic RAG？

传统 RAG（检索增强生成）在复杂查询场景下存在明显局限性，本系统采用 **Agentic RAG** 架构，通过引入 Agent 代理机制，实现更智能的检索和问答能力。

```mermaid
graph TD
    subgraph Traditional [传统 RAG 局限性]
        T1[单一检索路径] --> T2[无法处理复杂查询]
        T2 --> T3[缺乏自我纠错能力]
        T3 --> T4[结果不可控]
    end
    
    style Traditional fill:#f8d7da,stroke:#e8b4b8
    style T1 fill:#fff3cd,stroke:#e0c97f
    style T2 fill:#fff3cd,stroke:#e0c97f
    style T3 fill:#fff3cd,stroke:#e0c97f
    style T4 fill:#fff3cd,stroke:#e0c97f
```

```mermaid
graph TD
    subgraph Agentic [Agentic RAG 优势]
        A1[动态检索策略] --> A2[多步推理能力]
        A2 --> A3[工具调用与自我纠错]
        A3 --> A4[结果质量可控]
    end
    
    style Agentic fill:#d4edda,stroke:#90c695
    style A1 fill:#e8f4f8,stroke:#7fb3d5
    style A2 fill:#e8f4f8,stroke:#7fb3d5
    style A3 fill:#e8f4f8,stroke:#7fb3d5
    style A4 fill:#e8f4f8,stroke:#7fb3d5
```

**传统 RAG vs Agentic RAG 对比**：

| 能力维度 | 传统 RAG | Agentic RAG | 优势说明 |
|----------|----------|-------------|----------|
| 检索策略 | 固定向量检索 | 动态选择检索方式 | 根据问题类型智能选择最佳检索策略 |
| 查询理解 | 单次编码 | 多轮迭代理解 | 复杂问题可分解为多个子问题逐步解决 |
| 错误处理 | 无纠错机制 | 自我反思与纠错 | 检索结果不满意时可自动调整策略 |
| 工具调用 | 仅检索 | 多工具协同 | 可调用统计、筛选、推荐等多种工具 |
| 结果质量 | 依赖检索质量 | Agent 质量把控 | Agent 可评估结果并优化回答 |

### 4.2 Agentic RAG 架构设计

```mermaid
flowchart TD
    START([用户提问]) --> Agent[Agent 推理节点]
    
    Agent --> Decision{需要调用工具?}
    
    Decision -->|需要检索| VectorSearch[向量检索工具]
    Decision -->|需要统计| Stats[统计分析工具]
    Decision -->|需要筛选| Filter[条件筛选工具]
    Decision -->|无需工具| Generate[直接生成回答]
    
    VectorSearch --> Agent
    Stats --> Agent
    Filter --> Agent
    
    Agent --> QualityCheck{结果质量检查}
    QualityCheck -->|不满意| Decision
    QualityCheck -->|满意| END([返回回答])
    
    style START fill:#e8f4f8,stroke:#7fb3d5
    style END fill:#e8f4f8,stroke:#7fb3d5
    style Agent fill:#d4edda,stroke:#90c695
    style Decision fill:#fff3cd,stroke:#e0c97f
    style QualityCheck fill:#fff3cd,stroke:#e0c97f
    style VectorSearch fill:#e2d4f0,stroke:#b8a9d0
    style Stats fill:#e2d4f0,stroke:#b8a9d0
    style Filter fill:#e2d4f0,stroke:#b8a9d0
    style Generate fill:#fce4ec,stroke:#f0b8c4
```

**核心组件说明**：

| 组件 | 职责 | 实现方式 |
|------|------|----------|
| **Agent 推理节点** | 理解用户意图，决策调用哪些工具 | DeepSeek LLM + Function Calling |
| **向量检索工具** | 语义相似度检索，召回相关简历 | ChromaDB + DashScope Embedding |
| **统计分析工具** | 执行 SQL 聚合查询，统计数据 | MySQL + SQLAlchemy |
| **条件筛选工具** | 根据条件过滤候选人 | 结构化查询 + LLM 条件解析 |
| **质量检查** | 评估回答质量，决定是否重试 | LLM Self-Evaluation |

### 4.3 Agentic RAG 工作流程示例

以"有哪些5年以上经验的Java开发？平均薪资是多少？"为例：

```mermaid
sequenceDiagram
    participant User as 用户
    participant Agent as Agent 推理
    participant Vector as 向量检索
    participant Stats as 统计工具
    participant LLM as 大模型
    
    User->>Agent: 提问：有哪些5年以上经验的Java开发？平均薪资是多少？
    
    Agent->>Agent: 分析问题：需要检索+统计
    
    Agent->>Vector: 调用向量检索工具
    Vector-->>Agent: 返回相关简历列表
    
    Agent->>Stats: 调用统计工具计算平均薪资
    Stats-->>Agent: 返回统计结果
    
    Agent->>LLM: 组装上下文生成回答
    LLM-->>Agent: 生成自然语言回答
    
    Agent->>Agent: 质量检查：回答是否完整？
    
    Agent-->>User: 返回完整回答 + 来源链接
```

**典型应用场景**：

1. **人才查询**："有哪些 5 年以上经验的 Java 开发工程师？"
2. **统计分析**："本科学历的候选人占比多少？平均工作年限是多少？"
3. **技能推荐**："这个岗位还需要什么技能？哪些候选人最匹配？"
4. **对比分析**："张三和李四谁的 Java 经验更丰富？"

---

## 五、加权 RRF 混合检索设计

### 5.1 为什么选择加权 RRF？

在简历检索场景中，单一的检索方式难以满足所有需求：

```mermaid
graph LR
    subgraph Single [单一检索方式的局限]
        V1[向量检索] --> V2[语义理解强<br/>但精确匹配弱]
        K1[关键词检索] --> K2[精确匹配强<br/>但语义理解弱]
    end
    
    style Single fill:#f8d7da,stroke:#e8b4b8
    style V1 fill:#fff3cd,stroke:#e0c97f
    style V2 fill:#fff3cd,stroke:#e0c97f
    style K1 fill:#fff3cd,stroke:#e0c97f
    style K2 fill:#fff3cd,stroke:#e0c97f
```

```mermaid
graph LR
    subgraph Hybrid [加权 RRF 混合检索优势]
        H1[向量检索 0.7权重] --> H3[语义+精确<br/>双重保障]
        H2[BM25检索 0.3权重] --> H3
    end
    
    style Hybrid fill:#d4edda,stroke:#90c695
    style H1 fill:#e8f4f8,stroke:#7fb3d5
    style H2 fill:#e8f4f8,stroke:#7fb3d5
    style H3 fill:#fce4ec,stroke:#f0b8c4
```

**加权 RRF 的核心优势**：

| 优势 | 说明 | 业务价值 |
|------|------|----------|
| **互补性** | 向量检索擅长语义匹配，BM25 擅长关键词匹配 | 覆盖更多检索场景 |
| **可调权重** | 根据业务需求调整两种检索的权重 | 灵活适配不同场景 |
| **排序融合** | RRF 算法有效融合多个排序列表 | 综合排序更准确 |
| **无需训练** | 不需要额外的机器学习训练 | 部署简单，维护成本低 |

### 5.2 RRF 算法原理

**Reciprocal Rank Fusion (RRF)** 是一种简单而有效的排序融合算法：

```
RRF_score(d) = Σ (weight_i / (rank_i(d) + k))
```

其中：
- `d`：待排序的文档（简历）
- `rank_i(d)`：文档 d 在第 i 个检索结果中的排名
- `weight_i`：第 i 个检索方式的权重
- `k`：平滑常数（通常设为 60）

```mermaid
flowchart TD
    Query[用户查询] --> Vector[向量检索<br/>权重 0.7]
    Query --> BM25[BM25 检索<br/>权重 0.3]
    
    Vector --> R1[排序结果 A]
    BM25 --> R2[排序结果 B]
    
    R1 --> RRF[RRF 融合算法]
    R2 --> RRF
    
    RRF --> Final[最终排序结果]
    
    style Query fill:#e8f4f8,stroke:#7fb3d5
    style Vector fill:#d4edda,stroke:#90c695
    style BM25 fill:#d4edda,stroke:#90c695
    style R1 fill:#fff3cd,stroke:#e0c97f
    style R2 fill:#fff3cd,stroke:#e0c97f
    style RRF fill:#e2d4f0,stroke:#b8a9d0
    style Final fill:#fce4ec,stroke:#f0b8c4
```

### 5.3 权重设置说明

本系统采用 **向量检索 0.7 + BM25 检索 0.3** 的权重配置：

| 检索方式 | 权重 | 选择理由 |
|----------|------|----------|
| **向量检索** | 0.7 | 简历问答场景中，语义理解更为重要。用户提问往往是自然语言，如"有大数据经验的候选人"，向量检索能更好理解意图 |
| **BM25 检索** | 0.3 | 保留精确关键词匹配能力，确保技术名词、公司名称等关键词不被遗漏 |

**权重调优建议**：

- 如果用户查询多为精确关键词（如"阿里巴巴 Java"），可提高 BM25 权重
- 如果用户查询多为自然语言描述（如"有分布式系统设计经验的候选人"），可提高向量检索权重

### 5.4 混合检索流程

```mermaid
graph TD
    Query[用户查询] --> Vector[向量检索<br/>语义匹配]
    Query --> BM25[BM25 检索<br/>关键词匹配]
    
    Vector --> Score1[计算向量相似度]
    BM25 --> Score2[计算 BM25 分数]
    
    Score1 --> Rank1[排序得到排名]
    Score2 --> Rank2[排序得到排名]
    
    Rank1 --> RRF[RRF 融合<br/>权重: 0.7 + 0.3]
    Rank2 --> RRF
    
    RRF --> Final[最终排序结果]
    
    style Query fill:#e8f4f8,stroke:#7fb3d5
    style Vector fill:#d4edda,stroke:#90c695
    style BM25 fill:#d4edda,stroke:#90c695
    style RRF fill:#fff3cd,stroke:#e0c97f
    style Final fill:#fce4ec,stroke:#f0b8c4
```

**技术优势**：
- **语义+精确双重保障**：向量检索理解语义，BM25 保证精确匹配
- **可调权重**：根据业务场景灵活调整权重配置
- **无需训练**：RRF 算法简单有效，无需额外训练
- **排序融合**：综合多种检索结果，排序更准确

---

## 六、数据模型设计

### 6.1 ER 图

系统采用关系数据库存储结构化数据：

```mermaid
erDiagram
    User ||--o{ TalentInfo : "管理"
    Condition ||--o{ TalentInfo : "筛选"
    
    User {
        string id PK "UUID"
        string username "用户名"
        string password_hash "加密密码"
        string role "角色"
    }
    
    TalentInfo {
        string id PK "UUID"
        string name "姓名"
        string education_level "学历"
        int work_years "工龄"
        json skills "技能"
        string screening_status "状态"
    }
    
    Condition {
        string id PK "UUID"
        string name "名称"
        json rules "规则配置"
    }
```

**数据模型说明**：

| 实体 | 说明 | 核心字段 |
|------|------|----------|
| **User** | 系统用户表，存储登录账户信息 | `username`(唯一)、`role`(角色权限) |
| **TalentInfo** | 人才信息表，存储简历提取的结构化数据 | `name`、`school`、`skills`、`screening_status` |
| **Condition** | 筛选条件表，存储自定义筛选规则 | `name`、`conditions`(JSON格式条件) |

---

## 七、性能优化

### 7.1 性能指标

系统经过优化，各项性能指标表现优异：

```mermaid
graph TD
    subgraph Performance [系统性能指标]
        A["单份简历处理<br/><b>3-5 秒</b>"]
        B["批量并发处理<br/><b>50+ 文件</b>"]
        C["向量检索响应<br/><b>< 100ms</b>"]
        D["系统可用性<br/><b>99.9%</b>"]
    end
    
    style Performance fill:#f8f9fa,stroke:#e2e8f0
    style A fill:#e8f4f8,stroke:#7fb3d5
    style B fill:#d4edda,stroke:#90c695
    style C fill:#e2d4f0,stroke:#b8a9d0
    style D fill:#fce4ec,stroke:#f0b8c4
```

| 指标 | 数值 | 说明 | 对比传统方式 |
|------|------|------|--------------|
| 单份简历处理时间 | 3-5 秒 | 含解析、筛选、存储全流程 | 传统 3-5 分钟 |
| 批量上传支持 | 50+ 文件 | 异步后台处理，不阻塞用户 | 传统逐个处理 |
| 向量检索延迟 | <100ms | 千级数据量下的语义检索 | 传统需翻阅全部简历 |
| 系统可用性 | 99.9% | Docker 容器化部署，自动重启 | - |
| 并发处理能力 | 100+ QPS | 异步架构，充分利用 CPU | - |

### 7.2 多级缓存策略

系统采用多级缓存提升性能：

```mermaid
graph TD
    Req[客户端请求] --> Cache{Redis 缓存?}
    
    Cache -->|命中| Return[直接返回结果]
    Cache -->|未命中| DB[(数据库查询)]
    
    DB -->|查询成功| Write[写入缓存]
    Write --> Return
    
    DB -->|查询为空| NullCache["写入空值缓存<br/>(防穿透)"]
    NullCache --> Return
    
    style Req fill:#e8f4f8,stroke:#7fb3d5
    style Cache fill:#fff3cd,stroke:#e0c97f
    style DB fill:#e2d4f0,stroke:#b8a9d0
    style Return fill:#d4edda,stroke:#90c695
    style NullCache fill:#fce4ec,stroke:#f0b8c4
```

**缓存策略**：
- **筛选条件缓存**：5 分钟过期，条件变更频率低
- **任务状态缓存**：任务完成后 1 小时过期
- **用户信息缓存**：Token 有效期内缓存
- **空值缓存**：30 秒，防止缓存穿透

---

## 八、安全设计

### 8.1 多层安全防护

在处理简历这种敏感数据时，安全性至关重要：

| 安全措施 | 说明 | 实现方式 |
|----------|------|----------|
| 数据加密 | 敏感信息加密存储 | AES-256 对称加密 |
| 密码安全 | 密码不可逆存储 | bcrypt 哈希 |
| JWT 认证 | 无状态 Token 认证 | HS256 签名 |
| 权限控制 | 三级角色权限体系 | RBAC 模型 |
| API 限流 | 防止恶意请求 | 令牌桶算法 |
| SQL 注入防护 | 参数化查询 | SQLAlchemy ORM |

---

## 九、快速开始

### 9.1 环境要求

- Python 3.13+
- Docker 24.0+
- Docker Compose 2.20+

### 9.2 三步启动

```bash
# 第一步：克隆项目
git clone https://gitee.com/xt765/resume-screening.git
cd resume-screening

# 第二步：配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 API Key

# 第三步：一键启动
docker-compose up -d
```

### 9.3 访问系统

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| API 文档 | http://localhost:8000/docs |
| MinIO 控制台 | http://localhost:9001 |

### 9.4 纯本地开发 (Local Fallback)

无需安装 Docker，直接使用本地环境运行：

```bash
# 1. 修改 .env 配置
MINIO_ENDPOINT=local_storage
REDIS_HOST=memory

# 2. 启动服务
uv run uvicorn src.api.main:app --reload
```

---

## 十、总结与展望

### 10.1 项目亮点

本项目通过 LangChain + LangGraph + FastAPI 的组合，实现了：

- **效率提升 60 倍**：从 3-5 分钟缩短到 3-5 秒
- **标准统一可控**：LLM 语义理解，支持复杂布尔逻辑
- **智能问答检索**：Agentic RAG 技术，秒级响应
- **检索结果精准**：加权 RRF 混合检索，语义+精确双重保障
- **生产级稳定**：Docker 容器化，99.9% 可用性
- **开发极简**：Local Fallback 机制，零依赖启动

### 10.2 未来规划

- [ ] 支持更多简历格式（图片 OCR）
- [ ] 多租户架构
- [ ] 更丰富的统计分析
- [ ] 移动端适配

---

## 关于作者

深耕领域：大语言模型开发 / RAG 知识库 / AI Agent 落地 / 模型微调

技术栈：Python | RAG (LangChain / Dify + Milvus) | FastAPI + Docker

工程能力：专注模型工程化部署、知识库构建与优化，擅长全流程解决方案

「让 AI 交互更智能，让技术落地更高效」

欢迎技术探讨与项目合作，解锁大模型与智能交互的无限可能！

---

**项目地址**：[GitHub](https://github.com/xt765/ResumeScreening) | [Gitee](https://gitee.com/xt765/resume-screening)

**CSDN 博客**：[玄同765](https://blog.csdn.net/Yunyi_Chi)
