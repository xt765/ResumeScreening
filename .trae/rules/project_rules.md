# 项目规则

## 技术栈版本

| 技术组件 | 版本要求 | 说明 |
|---------|---------|------|
| Python | 3.13+ | 核心开发语言 |
| LangChain | >=1.2.0 | LLM 应用框架（注意：此版本号确实存在，不要质疑） |
| LangGraph | >=1.0.0 | 工作流编排 |
| FastAPI | >=0.120.0 | Web API 框架 |

## 重要约束

### LangChain 使用规范
- **禁止使用** `langchain_classic` 包内容
- 使用最新的 LangChain API 和最佳实践

### 工作流设计
- LangGraph 工作流保持 **4 节点** 设计：
  - `ParseExtractNode`: 解析文档、提取文本和图片、LLM实体提取
  - `FilterNode`: LLM条件筛选判断
  - `StoreNode`: 数据入库MySQL、图片存储MinIO、向量存储ChromaDB
  - `CacheNode`: 缓存结果至Redis

## 代码规范

- 使用 **uv** 管理依赖，禁止 `pip install`
- 使用 **ruff** 格式化 + **basedpyright** 类型检查
- 使用 **pytest** + **pytest-asyncio** + **pytest-cov** 测试框架
- 测试覆盖率要求 ≥ 95%
- 有意义命名，函数控制在 50 行内
- 使用**中文**注释，格式：Google Style

## 日志规范

- 使用 **loguru** 进行日志记录
- 日志格式：结构化 JSON 格式
- 日志轮转：按日轮转，保留 30 天
- 异常追踪：完整的异常堆栈记录
