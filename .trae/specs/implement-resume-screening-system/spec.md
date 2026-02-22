# 人才简历智能筛选与管理系统 Spec

## Why

构建一个轻量级、高性能的智能化人才简历筛选与管理平台，实现对简历的自动化解析、智能筛选、信息提取、向量化存储与多维度查询分析，满足项目答辩评分要求（100分）。

## What Changes

- 新增项目基础架构（FastAPI + LangChain + LangGraph）
- 新增筛选条件管理模块（CRUD + 分页查询）- 25分
- 新增简历解析模块（PDF/Word解析 + MinIO存储）- 15分
- 新增智能信息提取模块（LLM实体提取 + 入库）- 20分
- 新增向量化存储模块（ChromaDB）- 20分
- 新增多维度数据分析模块（RAG查询）- 20分
- 新增Streamlit前端界面
- 新增完整测试套件（覆盖率≥95%）

## Impact

- 新增代码: src/, frontend/, tests/ 目录
- 新增依赖: FastAPI, LangChain, LangGraph, ChromaDB, MinIO, Redis, Streamlit
- 外部服务: MySQL, MinIO, Redis, ChromaDB, DeepSeek(LLM)/DashScope(Embedding) API

**重要约束**:

- **禁止使用** `langchain_classic` 包内容
- 使用最新的 LangChain API 和最佳实践
- Embedding 服务使用 **DashScope Embedding API**

---

## ADDED Requirements

### Requirement: 项目基础架构

系统 SHALL 提供完整的项目基础架构，包括配置管理、日志系统、异常处理、数据库连接等。

#### Scenario: 配置管理

- **WHEN** 应用启动时
- **THEN** 从环境变量加载所有配置（MySQL、MinIO、Redis、LLM API）

#### Scenario: 日志系统

- **WHEN** 应用运行时
- **THEN** 使用loguru记录所有操作日志和异常信息（JSON格式，按日轮转，保留30天）

#### Scenario: 异常处理

- **WHEN** 发生异常时
- **THEN** 全局异常处理器捕获并记录完整上下文信息

---

### Requirement: 筛选条件管理模块 (25分)

系统 SHALL 提供筛选条件的完整CRUD操作和分页查询功能。

#### Scenario: 新增筛选条件 (5分)

- **WHEN** 用户提交新的筛选条件（name, description, conditions）
- **THEN** 系统创建筛选条件记录，状态为active，返回创建成功

#### Scenario: 修改筛选条件 (5分)

- **WHEN** 用户修改已有筛选条件
- **THEN** 系统更新筛选条件记录的name、description、conditions字段，更新updated_at时间戳

#### Scenario: 逻辑删除筛选条件 (5分)

- **WHEN** 用户删除筛选条件
- **THEN** 系统将状态标记为deleted（软删除），不物理删除数据

#### Scenario: 分页查询筛选条件 (10分)

- **WHEN** 用户查询筛选条件列表
- **THEN** 系统返回支持多状态、多条件组合的分页结果
- **AND** 支持按status、name等条件筛选
- **AND** 支持分页参数page、page_size

---

### Requirement: 简历解析与存储模块 (15分)

系统 SHALL 支持PDF/Word简历文件的解析和图片存储。

#### Scenario: PDF/Word解析 (10分)

- **WHEN** 用户上传PDF简历文件
- **THEN** 系统使用pymupdf提取文本内容和个人图片
- **WHEN** 用户上传Word简历文件
- **THEN** 系统使用python-docx提取文本内容和个人图片

#### Scenario: 图片存储 (5分)

- **WHEN** 提取到个人图片
- **THEN** 系统将图片存储至MinIO（bucket: resume-images）
- **AND** 将图片地址关联到人才信息表的photo_url字段

---

### Requirement: 智能信息提取与入库模块 (20分)

系统 SHALL 使用LLM进行条件筛选和实体信息提取。

#### Scenario: 大模型条件筛选 (5分)

- **WHEN** 简历文本解析完成
- **THEN** 系统使用LangGraph工作流调用LLM判断候选人是否符合筛选条件
- **AND** 支持异步调用和超时重试（最大3次，超时30秒）

#### Scenario: 实体信息提取 (5分)

- **WHEN** 候选人符合筛选条件
- **THEN** 系统使用LLM提取实体信息：姓名、技能、毕业院校、联系方式、学历、专业、工作年限
- **AND** 使用CandidateInfo Schema结构化输出

#### Scenario: 入库与查询 (10分)

- **WHEN** 实体信息提取完成
- **THEN** 系统将人才信息保存到MySQL数据库
- **AND** 敏感信息（phone、email）使用AES加密存储
- **AND** 支持按姓名、专业、毕业院校、选拔日期分页查询

---

### Requirement: 向量化存储模块 (20分)

系统 SHALL 使用LangChain将人才信息向量化存储至ChromaDB。

#### Scenario: 向量存储

- **WHEN** 人才信息入库完成
- **THEN** 系统使用DashScope Embedding API将简历文本向量化
- **AND** 存储至ChromaDB（collection: talent_resumes）
- **AND** 支持批量向量化插入

---

### Requirement: 多维度数据分析模块 (20分)

系统 SHALL 支持基于RAG的智能问答和数据分析。

#### Scenario: RAG查询

- **WHEN** 用户提交自然语言查询（如"有哪些Python开发经验的候选人"）
- **THEN** 系统通过向量检索从ChromaDB获取相关文档
- **AND** 构建上下文并调用LLM生成回答
- **AND** 支持按学校、学历、专业维度分析

#### Scenario: 统计数据

- **WHEN** 用户请求统计数据
- **THEN** 系统返回人才分布统计（按学校、学历、专业）

---

### Requirement: LangGraph工作流

系统 SHALL 使用LangGraph实现4节点工作流。

#### Scenario: 工作流节点

- **ParseExtractNode**: 解析文档、提取文本和图片、LLM实体提取
- **FilterNode**: LLM条件筛选判断
- **StoreNode**: 数据入库MySQL、图片存储MinIO、向量存储ChromaDB
- **CacheNode**: 缓存结果至Redis

#### Scenario: 工作流状态

- pending → parsing → filtering → storing → caching → completed
- 任意节点失败时状态变为failed，记录error_message

---

### Requirement: 前端界面

系统 SHALL 提供Streamlit前端界面。

#### Scenario: 首页

- 展示系统统计数据
- 展示最近筛选记录
- 提供快捷操作入口

#### Scenario: 筛选条件管理页面

- 条件列表展示（分页）
- 新增/编辑条件表单
- 逻辑删除确认
- 多状态筛选

#### Scenario: 简历上传筛选页面

- PDF/Word文件上传组件
- 筛选条件选择
- 筛选进度展示
- 结果预览

#### Scenario: 人才信息查询页面

- 数据表格展示
- 多条件筛选（姓名、专业、院校、选拔日期）
- 详情查看弹窗
- 照片展示

#### Scenario: 数据分析页面

- RAG智能问答界面
- 按学校/学历/专业统计图表
- 数据导出功能（CSV/Excel）

---

### Requirement: 测试覆盖

系统 SHALL 提供完整的测试套件，测试覆盖率≥95%。

#### Scenario: 单元测试

- 测试单个函数/方法/类的正确性
- 包括解析器、模型、工具函数测试

#### Scenario: 集成测试

- 测试模块间交互（API + 数据库 + 存储）
- 包括API、存储、工作流测试

#### Scenario: 端对端测试

- 测试完整业务流程（上传简历 → 筛选 → 入库 → 查询）
- 使用真实测试简历数据

#### Scenario: 回归测试

- 每次代码变更后自动运行全量测试

---

### Requirement: 非功能性需求

#### Scenario: 性能要求

- 系统响应时间 ≤ 3秒（除大模型调用外）
- 并发处理能力 ≥ 50份/分钟
- 向量检索延迟 ≤ 500ms

#### Scenario: 安全要求

- 敏感信息（phone、email）使用AES加密存储
- 文件校验：上传文件类型限制（PDF/Word），大小限制（最大10MB）
- SQL注入防护：使用ORM参数化查询

#### Scenario: LLM接口要求

- 异步调用：所有LLM调用使用async/await
- 超时重试：最大重试3次，超时时间30秒
- 降级方案：DeepSeek失败时自动切换DashScope

---

### Requirement: 部署配置

系统 SHALL 支持Docker容器化部署。

#### Scenario: Dockerfile

- 基于python:3.13-slim镜像
- 使用uv安装依赖
- 暴露端口8000（API）、8501（前端）

#### Scenario: docker-compose

- 编排api、frontend、mysql、minio、redis服务
- 配置服务依赖和数据卷

#### Scenario: 健康检查

- 提供/health端点
- 返回各服务连接状态
