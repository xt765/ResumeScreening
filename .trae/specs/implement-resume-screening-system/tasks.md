# Tasks

## Phase 1: 基础架构搭建

- [ ] Task 1.1: 项目初始化与依赖配置
  - [ ] 创建pyproject.toml，配置所有依赖（FastAPI, LangChain, LangGraph, ChromaDB, MinIO, Redis, Streamlit, loguru, pytest等）
  - [ ] 配置ruff、basedpyright、pytest工具
  - [ ] 创建.env环境变量文件
  - [ ] 使用uv安装依赖

- [ ] Task 1.2: 核心配置模块
  - [ ] 创建src/core/config.py：使用pydantic-settings管理配置
  - [ ] 创建src/core/logger.py：配置loguru日志系统
  - [ ] 创建src/core/exceptions.py：定义业务异常类
  - [ ] 创建src/core/security.py：AES加密工具

- [ ] Task 1.3: 数据库模型设计
  - [ ] 创建src/models/__init__.py：SQLAlchemy基类和会话管理
  - [ ] 创建src/models/condition.py：筛选条件表模型
  - [ ] 创建src/models/talent.py：人才信息表模型
  - [ ] 创建数据库迁移脚本

- [ ] Task 1.4: 存储客户端
  - [ ] 创建src/storage/minio_client.py：MinIO客户端封装
  - [ ] 创建src/storage/redis_client.py：Redis客户端封装
  - [ ] 创建src/storage/chroma_client.py：ChromaDB客户端封装
  - [ ] 测试所有存储连接

- [ ] Task 1.5: Pydantic Schema
  - [ ] 创建src/schemas/common.py：通用响应模型（PaginatedResponse, APIResponse）
  - [ ] 创建src/schemas/condition.py：筛选条件Schema
  - [ ] 创建src/schemas/talent.py：人才信息Schema和CandidateInfo

## Phase 2: 核心模块开发

- [ ] Task 2.1: 筛选条件管理模块 (25分)
  - [ ] 创建src/api/deps.py：依赖注入（数据库会话）
  - [ ] 创建src/api/v1/conditions.py：筛选条件CRUD API
    - POST /api/v1/conditions：新增筛选条件
    - PUT /api/v1/conditions/{id}：修改筛选条件
    - DELETE /api/v1/conditions/{id}：逻辑删除
    - GET /api/v1/conditions：分页查询（支持多状态、多条件）
  - [ ] 编写单元测试

- [ ] Task 2.2: 简历解析模块 (15分)
  - [ ] 创建src/parsers/document_parser.py：文档解析器
    - PDF解析：使用pymupdf提取文本和图片
    - Word解析：使用python-docx提取文本和图片
  - [ ] 编写单元测试

- [ ] Task 2.3: LangGraph工作流实现 (20分)
  - [ ] 创建src/workflows/parse_extract_node.py：解析提取节点
    - 解析文档文本和图片
    - LLM实体信息提取
  - [ ] 创建src/workflows/filter_node.py：筛选节点
    - LLM条件筛选判断
  - [ ] 创建src/workflows/store_node.py：入库节点
    - MySQL数据入库
    - MinIO图片存储
    - ChromaDB向量存储
  - [ ] 创建src/workflows/cache_node.py：缓存节点
    - Redis缓存结果
  - [ ] 创建src/workflows/resume_workflow.py：工作流编排
  - [ ] 编写单元测试

- [ ] Task 2.4: 人才管理API
  - [ ] 创建src/api/v1/talents.py：人才管理API
    - POST /api/v1/talents/upload-screen：上传简历并执行智能筛选
    - GET /api/v1/talents：分页查询（按姓名、专业、院校、选拔日期）
    - GET /api/v1/talents/{id}：获取人才详情
    - POST /api/v1/talents/{id}/vectorize：向量化指定人才
    - POST /api/v1/talents/batch-vectorize：批量向量化
  - [ ] 编写集成测试

## Phase 3: 向量与检索

- [ ] Task 3.1: 向量化存储实现
  - [ ] 实现LangChain Embedding集成（DashScope Embedding API）
  - [ ] 实现ChromaDB向量存储
  - [ ] 实现批量向量化功能
  - [ ] 编写单元测试

- [ ] Task 3.2: RAG查询实现 (20分)
  - [ ] 创建src/api/v1/analysis.py：数据分析API
    - POST /api/v1/analysis/query：RAG智能查询
    - GET /api/v1/analysis/statistics：统计数据
  - [ ] 实现RAG查询流程：向量化→检索→上下文构建→LLM生成
  - [ ] 编写集成测试

## Phase 4: 前端开发（Streamlit）

- [ ] Task 4.1: 主应用框架
  - [ ] 创建frontend/app.py：主应用入口和首页
    - 系统统计数据展示
    - 最近筛选记录
    - 快捷操作入口
  - [ ] 创建frontend/components/sidebar.py：侧边栏组件

- [ ] Task 4.2: 筛选条件管理页面
  - [ ] 创建frontend/pages/conditions.py
    - 条件列表展示（分页）
    - 新增/编辑条件表单
    - 逻辑删除确认
    - 多状态筛选

- [ ] Task 4.3: 简历上传筛选页面
  - [ ] 创建frontend/pages/resume_upload.py
    - PDF/Word文件上传组件
    - 筛选条件选择
    - 筛选进度展示
    - 结果预览

- [ ] Task 4.4: 人才信息查询页面
  - [ ] 创建frontend/pages/talent_query.py
    - 数据表格展示
    - 多条件筛选（姓名、专业、院校、选拔日期）
    - 详情查看弹窗
    - 照片展示

- [ ] Task 4.5: 数据分析页面
  - [ ] 创建frontend/pages/analysis.py
    - RAG智能问答界面
    - 按学校/学历/专业统计图表
    - 数据看板
    - 数据导出功能
  - [ ] 创建frontend/components/charts.py：图表组件

## Phase 5: 测试与优化

- [ ] Task 5.1: 单元测试（覆盖率≥95%）
  - [ ] 创建tests/conftest.py：pytest配置和fixtures
  - [ ] 创建tests/unit/test_parsers.py：解析器单元测试
  - [ ] 创建tests/unit/test_models.py：模型单元测试
  - [ ] 创建tests/unit/test_utils.py：工具函数单元测试
  - [ ] 复制测试简历到tests/test_data/resumes/

- [ ] Task 5.2: 集成测试
  - [ ] 创建tests/integration/test_api.py：API集成测试
  - [ ] 创建tests/integration/test_storage.py：存储集成测试
  - [ ] 创建tests/integration/test_workflow.py：工作流集成测试

- [ ] Task 5.3: 端对端测试
  - [ ] 创建tests/e2e/test_resume_flow.py：完整业务流程测试
    - PDF简历处理流程
    - Word简历处理流程
    - 批量简历处理

- [ ] Task 5.4: 回归测试
  - [ ] 创建tests/regression/test_all.py：全量回归测试

- [ ] Task 5.5: FastAPI主应用
  - [ ] 创建src/api/main.py：FastAPI应用入口
  - [ ] 创建src/api/health.py：健康检查端点
  - [ ] 配置全局异常处理
  - [ ] 配置CORS

## Phase 6: 部署配置

- [ ] Task 6.1: Docker配置
  - [ ] 创建Dockerfile
  - [ ] 创建docker-compose.yml

# Task Dependencies
- Task 1.2 depends on Task 1.1
- Task 1.3 depends on Task 1.1
- Task 1.4 depends on Task 1.1
- Task 1.5 depends on Task 1.1
- Task 2.1 depends on Task 1.2, Task 1.3, Task 1.5
- Task 2.2 depends on Task 1.1
- Task 2.3 depends on Task 1.2, Task 1.3, Task 1.4, Task 2.2
- Task 2.4 depends on Task 2.3
- Task 3.1 depends on Task 1.4
- Task 3.2 depends on Task 3.1
- Task 4.1 depends on Task 2.1, Task 2.4, Task 3.2
- Task 4.2 depends on Task 4.1
- Task 4.3 depends on Task 4.1
- Task 4.4 depends on Task 4.1
- Task 4.5 depends on Task 4.1
- Task 5.1 depends on Task 2.1, Task 2.2
- Task 5.2 depends on Task 2.1, Task 2.4, Task 3.1
- Task 5.3 depends on Task 2.4, Task 3.2
- Task 5.5 depends on Task 2.1, Task 2.4, Task 3.2
- Task 6.1 depends on Task 5.5
