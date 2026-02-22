"""LangGraph 工作流模块。

定义简历处理的四节点工作流：
- ParseExtractNode: 解析文档、提取文本和图片、LLM 实体提取
- FilterNode: LLM 条件筛选判断
- StoreNode: 数据入库 MySQL、图片存储 MinIO、向量存储 ChromaDB
- CacheNode: 缓存结果至 Redis

使用示例：
    ```python
    from src.workflows import run_resume_workflow

    result = await run_resume_workflow(
        file_path="/path/to/resume.pdf",
        condition_id="xxx-xxx-xxx",
        condition_config={
            "skills": ["Python", "FastAPI"],
            "education_level": "本科",
            "experience_years": 3,
        },
    )
    ```
"""

from src.workflows.cache_node import (
    cache_node,
    get_cached_candidate,
    get_cached_result,
    get_screening_stats,
    invalidate_cache,
)
from src.workflows.filter_node import filter_node
from src.workflows.parse_extract_node import parse_extract_node
from src.workflows.resume_workflow import (
    build_resume_workflow,
    get_resume_workflow,
    get_workflow_graph,
    run_resume_workflow,
    run_workflow_batch,
)
from src.workflows.state import (
    CandidateInfo,
    FilterResult,
    NodeResult,
    ParseResult,
    ResumeState,
)
from src.workflows.store_node import store_node

__all__ = [
    "CandidateInfo",
    "FilterResult",
    "NodeResult",
    "ParseResult",
    "ResumeState",
    "build_resume_workflow",
    "cache_node",
    "filter_node",
    "get_cached_candidate",
    "get_cached_result",
    "get_resume_workflow",
    "get_screening_stats",
    "get_workflow_graph",
    "invalidate_cache",
    "parse_extract_node",
    "run_resume_workflow",
    "run_workflow_batch",
    "store_node",
]
