# 开发指南

## 开发环境搭建

### 1. 安装依赖工具

```bash
# 安装 Python 3.13+
# Windows: 从 python.org 下载安装
# macOS: brew install python@3.13
# Linux: sudo apt install python3.13

# 安装 uv 包管理器
pip install uv

# 安装 Docker Desktop
# 从 docker.com 下载安装
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd ResumeScreening
```

### 3. 安装项目依赖

```bash
# 创建虚拟环境并安装依赖
uv sync

# 安装开发依赖
uv sync --group dev
```

### 4. 配置开发环境

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，配置本地开发参数
```

### 5. 启动依赖服务

```bash
# 启动 MySQL、Redis、MinIO
docker-compose up -d mysql redis minio
```

### 6. 初始化数据库

```bash
# 创建数据库表
uv run python scripts/init_db.py

# 创建管理员账户
uv run python scripts/init_admin.py
```

### 7. 启动开发服务

```bash
# 终端 1: 启动后端
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2: 启动前端
cd frontend-new && python -m http.server 3000
```

## 项目结构详解

```
ResumeScreening/
├── docs/                      # 项目文档
├── frontend-new/              # 前端代码
│   ├── index.html             # 入口页面
│   ├── css/                   # 样式文件
│   │   ├── style.css          # 主样式
│   │   └── users.css          # 用户管理样式
│   └── js/                    # JavaScript
│       ├── app.js             # 应用入口、路由
│       ├── api.js             # API 封装
│       └── pages/             # 页面模块
│           ├── login.js       # 登录页
│           ├── dashboard.js   # 仪表盘
│           ├── upload.js      # 上传筛选
│           ├── talents.js     # 人才管理
│           ├── conditions.js  # 条件管理
│           ├── analysis.js    # 智能分析
│           ├── monitor.js     # 系统监控
│           └── users.js       # 用户管理
├── src/                       # 后端代码
│   ├── api/                   # API 层
│   │   ├── main.py            # FastAPI 应用
│   │   ├── deps.py            # 依赖注入
│   │   └── v1/                # v1 版本
│   ├── core/                  # 核心模块
│   │   ├── config.py          # 配置管理
│   │   ├── security.py        # 安全加密
│   │   ├── auth.py            # 认证逻辑
│   │   ├── exceptions.py      # 异常定义
│   │   ├── logger.py          # 日志配置
│   │   └── tasks.py           # 任务管理
│   ├── models/                # SQLAlchemy 模型
│   │   ├── base.py            # 基础模型
│   │   ├── user.py            # 用户模型
│   │   ├── talent.py          # 人才模型
│   │   └── condition.py       # 条件模型
│   ├── schemas/               # Pydantic 模式
│   ├── services/              # 业务服务
│   │   ├── nlp_parser.py      # NLP 解析
│   │   ├── log_service.py     # 日志服务
│   │   └── metrics_service.py # 指标服务
│   ├── storage/               # 存储客户端
│   │   ├── chroma_client.py   # ChromaDB
│   │   ├── minio_client.py    # MinIO
│   │   └── redis_client.py    # Redis
│   ├── utils/                 # 工具函数
│   │   ├── embedding.py       # Embedding 服务
│   │   ├── rag_service.py     # RAG 服务
│   │   ├── face_detector.py   # 人脸检测
│   │   └── school_tier_data.py# 学校层级
│   ├── parsers/               # 文档解析
│   │   └── document_parser.py # 解析器
│   └── workflows/             # LangGraph 工作流
│       ├── state.py           # 状态定义
│       ├── resume_workflow.py # 工作流编排
│       ├── parse_extract_node.py
│       ├── filter_node.py
│       ├── store_node.py
│       └── cache_node.py
├── scripts/                   # 脚本工具
│   ├── init_db.py             # 初始化数据库
│   ├── init_admin.py          # 创建管理员
│   └── clear_all_databases.py # 清理数据
├── tests/                     # 测试代码
│   └── test_data/             # 测试数据
├── pyproject.toml             # 项目配置
└── docker-compose.yml         # Docker 编排
```

## 代码规范

### Python 代码规范

#### 1. 命名规范

```python
# 模块名：小写下划线
# my_module.py

# 类名：大驼峰
class TalentInfo:
    pass

# 函数名：小写下划线
def get_talent_by_id(talent_id: str) -> TalentInfo | None:
    pass

# 常量：大写下划线
MAX_FILE_SIZE = 10 * 1024 * 1024

# 私有属性：单下划线前缀
self._internal_value = None
```

#### 2. 类型注解

```python
from typing import Any

# 函数参数和返回值类型注解
def process_resume(
    file_path: str,
    condition_id: str | None = None,
) -> dict[str, Any]:
    pass

# 类属性类型注解
class ResumeState(BaseModel):
    file_path: str
    text_content: str | None = None
    skills: list[str] = Field(default_factory=list)
```

#### 3. 文档字符串

```python
def extract_candidate_info(text: str) -> dict[str, Any]:
    """从简历文本中提取候选人信息。

    使用 LLM 从非结构化简历文本中提取结构化信息，
    包括姓名、联系方式、教育背景、工作经历等。

    Args:
        text: 简历文本内容。

    Returns:
        dict[str, Any]: 提取的候选人信息字典。

    Raises:
        LLMException: LLM 调用失败时抛出。

    Example:
        >>> info = extract_candidate_info("张三，清华大学...")
        >>> print(info["name"])
        '张三'
    """
    pass
```

#### 4. 函数长度限制

- 单个函数不超过 50 行
- 复杂逻辑拆分为多个小函数
- 使用早返回减少嵌套

```python
# 好的实践
def process_file(file_path: str) -> dict[str, Any]:
    if not file_path:
        return {"error": "文件路径为空"}

    if not Path(file_path).exists():
        return {"error": "文件不存在"}

    content = read_file(file_path)
    result = parse_content(content)

    return result
```

### JavaScript 代码规范

#### 1. 命名规范

```javascript
// 变量名：小驼峰
const talentList = [];

// 函数名：小驼峰
function getTalentById(id) {
    // ...
}

// 常量：大写下划线
const MAX_FILES = 50;

// 类名：大驼峰
class TalentManager {
    // ...
}

// 私有方法：下划线前缀
_internalMethod() {
    // ...
}
```

#### 2. 注释规范

```javascript
/**
 * 处理文件选择事件
 * @param {FileList} files - 选择的文件列表
 * @returns {void}
 */
handleFilesSelect(files) {
    // 验证文件类型
    const allowedTypes = ['pdf', 'docx', 'doc'];
    // ...
}
```

## 测试指南

### 测试框架

- **pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 覆盖率报告

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_workflows.py

# 运行特定测试用例
uv run pytest tests/test_workflows.py::test_parse_extract_node

# 显示详细输出
uv run pytest -v

# 带覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 测试示例

```python
import pytest
from src.workflows.state import ResumeState

@pytest.fixture
def sample_state() -> ResumeState:
    """创建测试用状态实例。"""
    return ResumeState(
        file_path="/tmp/test.pdf",
        file_type="pdf",
    )

@pytest.mark.asyncio
async def test_parse_extract_node(sample_state: ResumeState):
    """测试解析提取节点。"""
    from src.workflows.parse_extract_node import ParseExtractNode

    node = ParseExtractNode()
    result = await node.execute(sample_state)

    assert result.success
    assert result.updates.get("text_content") is not None
```

### 测试覆盖率

项目要求测试覆盖率 >= 95%。

```bash
# 生成覆盖率报告
uv run pytest --cov=src --cov-report=html

# 查看 HTML 报告
# 打开 htmlcov/index.html
```

## 代码检查

### Ruff 格式化

```bash
# 格式化代码
uv run ruff format src/

# 检查代码风格
uv run ruff check src/

# 自动修复
uv run ruff check src/ --fix
```

### 类型检查

```bash
# 运行类型检查
uv run basedpyright src/
```

## 添加新功能

### 1. 添加新的 API 端点

```python
# src/api/v1/talents.py

@router.get(
    "/{talent_id}/resume",
    summary="获取简历原文",
)
async def get_resume_content(
    talent_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> APIResponse[dict[str, Any]]:
    """获取人才简历原文内容。"""
    # 实现逻辑
    pass
```

### 2. 添加新的工作流节点

```python
# src/workflows/custom_node.py

from src.workflows.state import ResumeState, NodeResult

class CustomNode:
    """自定义处理节点。"""

    async def execute(self, state: ResumeState) -> NodeResult:
        """执行节点逻辑。

        Args:
            state: 工作流状态

        Returns:
            NodeResult: 节点执行结果
        """
        try:
            # 处理逻辑
            return NodeResult(
                success=True,
                updates={"custom_field": "value"},
            )
        except Exception as e:
            return NodeResult(
                success=False,
                error=str(e),
            )
```

### 3. 添加新的数据模型

```python
# src/models/custom.py

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin

class CustomModel(Base, TimestampMixin):
    """自定义数据模型。"""

    __tablename__ = "custom_table"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### 4. 添加前端页面

```javascript
// frontend-new/js/pages/custom.js

const CustomPage = {
    async render() {
        return `
            <div class="custom-page">
                <h2>自定义页面</h2>
                <!-- 页面内容 -->
            </div>
        `;
    },

    async init() {
        // 初始化逻辑
    },

    async loadData() {
        // 加载数据
    }
};
```

## 调试技巧

### 1. 后端调试

```python
from loguru import logger

# 使用 logger 调试
logger.debug(f"处理文件: {file_path}")
logger.info(f"提取到 {len(skills)} 个技能")
logger.warning(f"未找到匹配条件: {condition_id}")
logger.error(f"处理失败: {error}")
```

### 2. 前端调试

```javascript
// 使用 console 调试
console.log('处理数据:', data);
console.warn('警告信息');
console.error('错误信息');

// 使用 debugger 断点
debugger;
```

### 3. 数据库调试

```bash
# 进入 MySQL 容器
docker-compose exec mysql mysql -u root -p

# 查询数据
SELECT * FROM talent_info LIMIT 10;

# 查看执行计划
EXPLAIN SELECT * FROM talent_info WHERE name = '张三';
```

## 常见问题

### 1. 依赖安装失败

```bash
# 清理缓存重新安装
uv cache clean
uv sync
```

### 2. 数据库连接失败

```bash
# 检查 MySQL 是否运行
docker-compose ps mysql

# 查看日志
docker-compose logs mysql
```

### 3. LLM 调用失败

- 检查 API Key 是否正确
- 检查网络连接
- 检查 API 配额

### 4. 前端跨域问题

开发环境已在后端配置 CORS，生产环境需通过 Nginx 配置。

## Git 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复 Bug |
| docs | 文档更新 |
| style | 代码格式调整 |
| refactor | 重构代码 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### 示例

```
feat(api): 添加简历批量导出功能

- 支持 PDF/Excel 格式导出
- 支持按筛选条件批量导出
- 添加导出进度显示

Closes #123
```
