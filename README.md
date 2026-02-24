<div align="center">

# Resume Intelligent Screening System

**An intelligent resume screening platform based on LangChain + LangGraph + FastAPI, with LLM for smart parsing, screening and RAG Q&A.**

🌐 **Language**: English | [中文](README_CN.md)

[![CSDN Blog](https://img.shields.io/badge/CSDN-玄同765-orange?style=flat-square&logo=csdn)](https://blog.csdn.net/Yunyi_Chi)
[![GitHub](https://img.shields.io/badge/GitHub-ResumeScreening-black?style=flat-square&logo=github)](https://github.com/xt765/ResumeScreening)
[![Gitee](https://img.shields.io/badge/Gitee-ResumeScreening-red?style=flat-square&logo=gitee)](https://gitee.com/xt765/resume-screening)

![Python](https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.12%20|%203.13-blue?style=flat-square&logo=python)
![Ruff](https://img.shields.io/badge/Ruff-Formatter-orange?style=flat-square&logo=ruff)
![Basedpyright](https://img.shields.io/badge/Basedpyright-TypeCheck-purple?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

## Background

In the recruitment process, HR needs to process a large number of resumes every day. Traditional manual screening methods have the following pain points:

| Pain Point | Description | Impact |
|------------|-------------|--------|
| Low Efficiency | Manual review of a resume takes 3-5 minutes on average | Long recruitment cycle, missing excellent candidates |
| Inconsistent Standards | Different HR screening standards vary subjectively | Uncontrollable screening results, uneven quality |
| Information Omission | Easy to miss key information or excellent candidates | Talent loss, increased recruitment costs |
| Difficult to Trace | Screening results lack data support and traceability | Cannot review and optimize screening standards |
| Difficult to Query | Hard to quickly retrieve and statistically analyze massive resumes | Data value cannot be mined |

This system uses Large Language Model (LLM) technology to achieve **intelligent parsing**, **automatic screening**, and **intelligent Q&A** of resumes, reducing traditional 3-5 minutes of manual screening to 3-5 seconds, improving efficiency by **more than 60 times**.

## Core Advantages

### 1. High Intelligence

Comparison between traditional manual screening and this system:

```mermaid
graph TB
    subgraph Traditional
        A1[Manual Reading] --> A2[Subjective Judgment]
        A2 --> A3[Manual Entry]
        A3 --> A4[Excel Storage]
    end
```

```mermaid
graph TB
    subgraph This System
        B1[AI Auto Parsing] --> B2[LLM Smart Screening]
        B2 --> B3[Structured Storage]
        B3 --> B4[Smart Q&A Retrieval]
    end
    style B1 fill:#ccffcc
```

| Dimension | Traditional | This System | Improvement |
|-----------|-------------|-------------|-------------|
| Processing Speed | 3-5 min/resume | 3-5 sec/resume | **60x** |
| Information Extraction | Manual entry, easy to miss | AI auto extracts 20+ fields | **100% coverage** |
| Screening Standards | Subjective judgment, varies by person | LLM semantic understanding, unified standards | **Consistency guaranteed** |
| Data Retrieval | Browse files or Excel | Natural language intelligent Q&A | **Second-level response** |

**Core Capabilities**:
- **Intelligent Parsing**: Auto extract name, education, skills, work experience, etc. (20+ fields), support PDF/DOCX formats
- **Intelligent Screening**: Based on LLM semantic understanding, support natural language screening conditions
- **Intelligent Q&A**: RAG technology for resume library intelligent Q&A

### 2. Advanced Technical Architecture

```mermaid
graph TB
    subgraph Frontend
        UI[Responsive Web Interface]
        WS[WebSocket Real-time Communication]
    end
    
    subgraph API Layer
        FastAPI[FastAPI Async Framework]
        Auth[JWT Authentication]
        Route[RESTful Routing]
    end
    
    subgraph Workflow Layer
        LG[LangGraph State Machine]
        Node1[Parse Node]
        Node2[Filter Node]
        Node3[Store Node]
        Node4[Cache Node]
    end
    
    subgraph AI Layer
        LLM[DeepSeek LLM]
        EMB[DashScope Embedding]
        RAG[RAG Retrieval Augmentation]
    end
    
    subgraph Storage Layer
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

### 3. Complete and Rich Features

| Feature Module | Description | Technical Highlights |
|----------------|-------------|---------------------|
| Resume Upload | Support PDF/DOCX batch upload | Async processing, real-time progress push |
| Intelligent Parsing | Auto extract structured information | LLM entity extraction, face detection |
| Condition Screening | Multi-dimensional intelligent screening | LLM semantic understanding, condition combination |
| Intelligent Q&A | Natural language query resume library | RAG + vector retrieval |
| System Monitoring | Real-time monitoring service status | Health check, log analysis |

### 4. Excellent Performance

| Metric | Value | Description |
|--------|-------|-------------|
| Single resume processing time | 3-5 sec | Full process including parsing, screening, storage |
| Batch upload support | 50+ files | Async background processing |
| Vector retrieval latency | <100ms | Thousand-level data volume |
| System availability | 99.9% | Docker containerized deployment |

## System Architecture

### Overall Architecture

```mermaid
graph TB
    subgraph User Layer
        User[User/HR]
    end
    
    subgraph Gateway Layer
        Nginx[Nginx Reverse Proxy]
    end
    
    subgraph Application Layer
        API[FastAPI Service]
        WSS[WebSocket Service]
    end
    
    subgraph Workflow Engine
        WF[LangGraph Workflow]
    end
    
    subgraph AI Services
        LLM[DeepSeek LLM]
        EMB[DashScope Embedding]
    end
    
    subgraph Data Layer
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

### Technology Stack

| Category | Technology | Version | Reason for Selection |
|----------|------------|---------|---------------------|
| Backend Framework | FastAPI | >=0.120.0 | Async high performance, auto API documentation |
| LLM Framework | LangChain | >=1.2.0 | Mature LLM application development framework |
| Workflow Engine | LangGraph | >=1.0.0 | State machine workflow, visual orchestration |
| LLM | DeepSeek | - | Domestic LLM, high cost-effectiveness |
| Embedding | DashScope | - | Alibaba Cloud service, good Chinese effect |
| Database | MySQL | 8.0 | Mature and stable, transaction support |
| Cache | Redis | 7 | High-performance cache, multiple data structures |
| Object Storage | MinIO | - | S3 compatible, private deployment |
| Vector Database | ChromaDB | >=0.5.0 | Lightweight vector storage |
| Frontend | HTML/CSS/JS | - | Native implementation, no framework dependency |

## Core Workflow

### Resume Processing Flow

```mermaid
graph TB
    A([User Upload Resume]) --> B[Parse Extract Node]
    B --> C[Filter Node]
    C --> D[Store Node]
    D --> E[Cache Node]
    E --> F([Return Result])
    
    B --> B1[Parse Document PDF/DOCX]
    B --> B2[Extract Text and Images]
    B --> B3[LLM Extract Info]
    B --> B4[Face Detection]
    
    C --> C1[Get Screening Conditions]
    C --> C2[Build Screening Prompt]
    C --> C3[LLM Judgment]
    C --> C4[Generate Screening Reason]
    
    D --> D1[Encrypt Sensitive Info]
    D --> D2[Save to MySQL]
    D --> D3[Upload to MinIO]
    D --> D4[Vector to ChromaDB]
```

### RAG Intelligent Q&A Flow

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant E as Embedding
    participant C as ChromaDB
    participant L as LLM
    
    U->>A: Submit Question
    A->>E: Question Vectorization
    E-->>A: Return Vector
    A->>C: Vector Similarity Search
    C-->>A: Return Related Resumes
    A->>L: Build Prompt + Context
    L-->>A: Generate Answer
    A-->>U: Return Result + Sources
```

## Data Model

### ER Diagram

```mermaid
erDiagram
    User ||--o{ TalentInfo : manages
    Condition ||--o{ TalentInfo : filters
    
    User {
        string id PK "User ID, UUID"
        string username UK "Username, unique"
        string password_hash "Password hash, bcrypt"
        string email "Email"
        string role "Role: admin/hr/viewer"
        boolean is_active "Is active"
    }
    
    TalentInfo {
        string id PK "Talent ID, UUID"
        string name "Name"
        string phone "Phone, AES encrypted"
        string email "Email, AES encrypted"
        string education_level "Education"
        string school "School"
        string major "Major"
        int work_years "Work years"
        json skills "Skills list, JSON"
        string screening_status "Screening status"
        string content_hash "Content hash, dedup"
    }
    
    Condition {
        string id PK "Condition ID, UUID"
        string name "Condition name"
        json conditions "Condition config, JSON"
        string description "Description"
    }
```

## Quick Start

### Requirements

| Software | Version | Description |
|----------|---------|-------------|
| Python | 3.10-3.13 | Core development language (Note: <3.14 due to pydantic v1 compatibility) |
| Docker | 24.0+ | Containerized deployment |
| Docker Compose | 2.20+ | Service orchestration |
| uv | Latest | Python package manager |

### Local Development

```bash
# 1. Clone project
git clone https://gitee.com/xt765/resume-screening.git
cd resume-screening

# 2. Install dependencies
uv sync

# 3. Configure environment variables
cp .env.example .env
# Edit .env file, configure necessary parameters

# 4. Start dependency services
docker-compose up -d mysql redis minio

# 5. Initialize database
uv run python scripts/init_db.py
uv run python scripts/init_admin.py

# 6. Start backend service
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Start frontend service (new terminal)
cd frontend-new && python -m http.server 3000
```

### Docker Deployment

```bash
# Start all services with one command
docker-compose up -d

# View service status
docker-compose ps
```

### Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | User interface |
| API Docs | http://localhost:8000/docs | Swagger interactive documentation |
| ReDoc | http://localhost:8000/redoc | ReDoc documentation |
| MinIO Console | http://localhost:9001 | Image storage management |

## Project Structure

```
ResumeScreening/
├── docs/                      # Documentation
│   ├── zh/                    # Chinese docs
│   └── en/                    # English docs
├── frontend-new/              # Frontend code
│   ├── index.html             # Entry page
│   ├── css/                   # Styles
│   └── js/                    # JavaScript
├── src/                       # Backend code
│   ├── api/                   # API routes
│   ├── core/                  # Core modules
│   ├── models/                # Data models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business services
│   ├── storage/               # Storage clients
│   ├── utils/                 # Utilities
│   └── workflows/             # LangGraph workflows
├── scripts/                   # Scripts
├── tests/                     # Tests
├── docker-compose.yml         # Docker compose
├── Dockerfile                 # Backend image
├── pyproject.toml             # Project config
├── README.md                  # English README
└── README_CN.md               # Chinese README
```

## Technical Highlights

### 1. LangGraph State Machine Workflow

- **State Persistence**: Each node state saved to database, supports checkpoint recovery
- **Visual Orchestration**: Workflow visualization, easy to understand and debug
- **Independent Testing**: Each node can be unit tested independently
- **Error Recovery**: Failed nodes can retry without re-executing the entire flow

### 2. RAG Retrieval Augmented Generation

- **Semantic Retrieval**: Vector similarity search, understands question intent
- **Traceable Sources**: Answers include source resume links, high credibility
- **Context Management**: Supports multi-turn dialogue, automatic context management
- **Real-time Update**: New resumes immediately searchable after storage

### 3. Multi-level Caching Strategy

- **Screening Condition Cache**: 5 min expiration, low change frequency
- **Task Status Cache**: 1 hour expiration after task completion
- **User Info Cache**: Valid during token period
- **Cache Penetration Protection**: Empty result cache for short time

### 4. Security Design

| Security Measure | Description | Implementation |
|------------------|-------------|----------------|
| Data Encryption | Sensitive info encrypted storage | AES-256 symmetric encryption |
| Password Security | Password irreversible storage | bcrypt hash |
| JWT Authentication | Stateless token authentication | HS256 signature |
| Permission Control | Three-level role permission system | RBAC model |

## Documentation

- [Architecture Design](docs/zh/architecture.md) - Detailed system architecture design
- [API Documentation](docs/zh/api.md) - Complete REST API documentation
- [Deployment Guide](docs/zh/deployment.md) - Docker deployment steps
- [Development Guide](docs/zh/development.md) - Development environment setup

## Changelog

### 2026-02-24
- **Frontend Optimization**:
  - Enhanced routing robustness: Fixed `Router.navigateTo` hash handling and initial redirect logic.
  - Improved UX: Hidden `app-container` by default to prevent "Flash of Unauthenticated Content".
  - Added error handling for `localStorage` to prevent crashes in restricted environments (e.g., privacy mode).
- **Documentation**:
  - Updated development and deployment guides.
  - Added frontend best practices section.

## License

MIT License
