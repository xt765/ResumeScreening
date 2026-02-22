"""简历处理工作流编排模块。

使用 LangGraph 编排简历处理的完整工作流：
ParseExtractNode -> FilterNode -> StoreNode -> CacheNode

支持：
- 状态管理和节点间数据传递
- 错误处理和状态回滚
- 工作流可视化
"""

import time
from typing import Any, Literal

from langgraph.graph import END, StateGraph
from loguru import logger

from src.core.exceptions import WorkflowException
from src.workflows.cache_node import cache_node
from src.workflows.filter_node import filter_node
from src.workflows.parse_extract_node import parse_extract_node
from src.workflows.state import ResumeState
from src.workflows.store_node import store_node

# 节点名称常量
NODE_PARSE_EXTRACT = "parse_extract"
NODE_FILTER = "filter"
NODE_STORE = "store"
NODE_CACHE = "cache"


def _handle_error(state: ResumeState, error: Exception, node_name: str) -> dict[str, Any]:
    """处理节点错误。

    记录错误信息并更新状态。

    Args:
        state: 当前工作流状态
        error: 异常对象
        node_name: 发生错误的节点名称

    Returns:
        dict[str, Any]: 错误状态更新
    """
    error_message = f"{type(error).__name__}: {error}"
    logger.error(f"工作流节点错误: node={node_name}, error={error_message}")

    return {
        "error_message": error_message,
        "error_node": node_name,
        "workflow_status": "failed",
    }


async def _load_and_merge_conditions(filter_config: dict[str, Any]) -> dict[str, Any]:
    """加载并合并复杂筛选配置中的所有条件。

    Args:
        filter_config: 复杂筛选配置

    Returns:
        dict[str, Any]: 合并后的筛选条件配置
    """
    from sqlalchemy import select

    from src.models import async_session_factory
    from src.models.condition import ScreeningCondition

    groups = filter_config.get("groups", [])
    exclude_ids = filter_config.get("exclude_condition_ids", [])

    all_condition_ids: set[str] = set()
    for group in groups:
        all_condition_ids.update(group.get("condition_ids", []))
    all_condition_ids.update(exclude_ids)

    if not all_condition_ids:
        return {}

    conditions_map: dict[str, dict[str, Any]] = {}

    async with async_session_factory() as session:
        result = await session.execute(
            select(ScreeningCondition).where(ScreeningCondition.id.in_(all_condition_ids))
        )
        condition_records = result.scalars().all()

        for record in condition_records:
            if record.conditions:
                conditions_map[record.id] = record.conditions

    merged_config: dict[str, Any] = {
        "skills": [],
        "major": [],
        "school_tier": [],
        "locations": [],
        "certifications": [],
        "keywords": [],
    }

    for cond_id, cond_config in conditions_map.items():
        if cond_config.get("skills"):
            merged_config["skills"].extend(cond_config["skills"])
        if cond_config.get("major"):
            merged_config["major"].extend(cond_config["major"])
        if cond_config.get("school_tier"):
            if isinstance(cond_config["school_tier"], list):
                merged_config["school_tier"].extend(cond_config["school_tier"])
            else:
                merged_config["school_tier"].append(cond_config["school_tier"])
        if cond_config.get("locations"):
            merged_config["locations"].extend(cond_config["locations"])
        if cond_config.get("certifications"):
            merged_config["certifications"].extend(cond_config["certifications"])
        if cond_config.get("keywords"):
            merged_config["keywords"].extend(cond_config["keywords"])

        if cond_config.get("education_level") and "education_level" not in merged_config:
            merged_config["education_level"] = cond_config["education_level"]

        if cond_config.get("experience_years") and "experience_years" not in merged_config:
            merged_config["experience_years"] = cond_config["experience_years"]

        if cond_config.get("experience_years_max") and "experience_years_max" not in merged_config:
            merged_config["experience_years_max"] = cond_config["experience_years_max"]

    merged_config["skills"] = list(set(merged_config["skills"]))
    merged_config["major"] = list(set(merged_config["major"]))
    merged_config["school_tier"] = list(set(merged_config["school_tier"]))
    merged_config["locations"] = list(set(merged_config["locations"]))
    merged_config["certifications"] = list(set(merged_config["certifications"]))
    merged_config["keywords"] = list(set(merged_config["keywords"]))

    merged_config["_filter_config"] = filter_config

    logger.info(f"合并筛选条件配置: {merged_config}")
    return merged_config


async def parse_extract_wrapper(state: ResumeState) -> dict[str, Any]:
    """解析提取节点包装器。

    包装 parse_extract_node，处理状态转换和错误。

    Args:
        state: 当前状态

    Returns:
        dict[str, Any]: 状态更新
    """
    try:
        result = await parse_extract_node(state)
        return result
    except Exception as e:
        return _handle_error(state, e, NODE_PARSE_EXTRACT)


async def filter_wrapper(state: ResumeState) -> dict[str, Any]:
    """筛选节点包装器。

    包装 filter_node，处理状态转换和错误。

    Args:
        state: 当前状态

    Returns:
        dict[str, Any]: 状态更新
    """
    try:
        result = await filter_node(state)
        return result
    except Exception as e:
        return _handle_error(state, e, NODE_FILTER)


async def store_wrapper(state: ResumeState) -> dict[str, Any]:
    """入库节点包装器。

    包装 store_node，处理状态转换和错误。

    Args:
        state: 当前状态

    Returns:
        dict[str, Any]: 状态更新
    """
    try:
        result = await store_node(state)
        return result
    except Exception as e:
        return _handle_error(state, e, NODE_STORE)


async def cache_wrapper(state: ResumeState) -> dict[str, Any]:
    """缓存节点包装器。

    包装 cache_node，处理状态转换和错误。

    Args:
        state: 当前状态

    Returns:
        dict[str, Any]: 状态更新
    """
    try:
        result = await cache_node(state)
        return result
    except Exception as e:
        return _handle_error(state, e, NODE_CACHE)


def should_continue_after_parse(state: ResumeState) -> Literal["filter", "end"]:
    """解析后路由决策。

    如果解析失败，直接结束工作流。

    Args:
        state: 当前状态

    Returns:
        Literal["filter", "end"]: 下一个节点名称
    """
    if state.error_message or state.workflow_status == "failed":
        logger.warning(f"解析失败，终止工作流: {state.error_message}")
        return "end"
    return "filter"


def should_continue_after_filter(state: ResumeState) -> Literal["store", "end"]:
    """筛选后路由决策。

    如果筛选失败或不符合条件，可以选择是否继续存储。
    当前设计：不符合条件也存储（标记为不合格），便于后续分析。

    Args:
        state: 当前状态

    Returns:
        Literal["store", "end"]: 下一个节点名称
    """
    if state.error_message or state.workflow_status == "failed":
        logger.warning(f"筛选失败，终止工作流: {state.error_message}")
        return "end"

    # 即使不符合条件也继续存储
    return "store"


def should_continue_after_store(state: ResumeState) -> Literal["cache", "end"]:
    """存储后路由决策。

    如果存储失败，直接结束工作流。

    Args:
        state: 当前状态

    Returns:
        Literal["cache", "end"]: 下一个节点名称
    """
    if state.error_message or state.workflow_status == "failed":
        logger.warning(f"存储失败，终止工作流: {state.error_message}")
        return "end"
    return "cache"


def build_resume_workflow() -> Any:
    """构建简历处理工作流图。

    创建并编译 LangGraph 状态图：
    - 添加节点
    - 添加边
    - 设置条件路由
    - 设置入口点

    Returns:
        CompiledGraph: 编译后的工作流图
    """
    logger.info("开始构建简历处理工作流")

    # 创建状态图
    workflow = StateGraph(ResumeState)

    # 添加节点
    workflow.add_node(NODE_PARSE_EXTRACT, parse_extract_wrapper)
    workflow.add_node(NODE_FILTER, filter_wrapper)
    workflow.add_node(NODE_STORE, store_wrapper)
    workflow.add_node(NODE_CACHE, cache_wrapper)

    # 设置入口点
    workflow.set_entry_point(NODE_PARSE_EXTRACT)

    # 添加条件边
    workflow.add_conditional_edges(
        NODE_PARSE_EXTRACT,
        should_continue_after_parse,
        {
            "filter": NODE_FILTER,
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        NODE_FILTER,
        should_continue_after_filter,
        {
            "store": NODE_STORE,
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        NODE_STORE,
        should_continue_after_store,
        {
            "cache": NODE_CACHE,
            "end": END,
        },
    )

    # 缓存节点后结束
    workflow.add_edge(NODE_CACHE, END)

    # 编译工作流
    compiled_workflow = workflow.compile()

    logger.success("简历处理工作流构建完成")
    return compiled_workflow


# 创建全局工作流实例
_resume_workflow: Any = None


def get_resume_workflow() -> Any:
    """获取简历处理工作流实例。

    使用单例模式确保只有一个工作流实例。

    Returns:
        CompiledGraph: 编译后的工作流图
    """
    global _resume_workflow
    if _resume_workflow is None:
        _resume_workflow = build_resume_workflow()
    return _resume_workflow


async def run_resume_workflow(
    file_path: str,
    condition_id: str | None = None,
    condition_config: dict[str, Any] | None = None,
    filter_config: dict[str, Any] | None = None,
    content_hash: str | None = None,
) -> dict[str, Any]:
    """运行简历处理工作流。

    执行完整的简历处理流程，返回处理结果。

    Args:
        file_path: 简历文件路径
        condition_id: 筛选条件 ID（向后兼容）
        condition_config: 筛选条件配置（向后兼容）
        filter_config: 复杂筛选配置（新格式）
        content_hash: 简历内容哈希（用于去重）

    Returns:
        dict[str, Any]: 工作流执行结果

    Raises:
        WorkflowException: 工作流执行失败

    Example:
        ```python
        # 简单模式
        result = await run_resume_workflow(
            file_path="/path/to/resume.pdf",
            condition_id="xxx-xxx-xxx",
        )

        # 复杂模式
        result = await run_resume_workflow(
            file_path="/path/to/resume.pdf",
            filter_config={
                "groups": [{"logic": "and", "condition_ids": ["id1", "id2"]}],
                "group_logic": "and",
                "exclude_condition_ids": ["id3"],
            },
        )
        ```
    """
    start_time = time.time()
    logger.info(
        f"开始运行简历处理工作流: file_path={file_path}, "
        f"condition_id={condition_id}, filter_config={filter_config}"
    )

    try:
        # 处理复杂筛选配置
        if filter_config and "groups" in filter_config:
            # 复杂筛选配置：加载所有条件并合并
            condition_config = await _load_and_merge_conditions(filter_config)
        elif not condition_config and condition_id:
            # 向后兼容：单个条件 ID
            from sqlalchemy import select

            from src.models import async_session_factory
            from src.models.condition import ScreeningCondition

            async with async_session_factory() as session:
                result = await session.execute(
                    select(ScreeningCondition).where(ScreeningCondition.id == condition_id)
                )
                condition_record = result.scalar_one_or_none()
                if condition_record and condition_record.conditions:
                    condition_config = condition_record.conditions
                    logger.info(f"从数据库加载筛选条件配置: {condition_config}")

        workflow = get_resume_workflow()

        initial_state = ResumeState(
            file_path=file_path,
            condition_id=condition_id,
            condition_config=condition_config,
            filter_config=filter_config,
            content_hash=content_hash,
        )

        # 执行工作流
        result = await workflow.ainvoke(initial_state.model_dump())

        # 计算总耗时
        total_time = int((time.time() - start_time) * 1000)
        result["total_processing_time"] = total_time

        # 记录结果
        if result.get("error_message"):
            logger.error(
                f"工作流执行失败: error={result['error_message']}, "
                f"node={result.get('error_node')}, time={total_time}ms"
            )
        else:
            logger.success(
                f"工作流执行成功: talent_id={result.get('talent_id')}, "
                f"qualified={result.get('is_qualified')}, time={total_time}ms"
            )

        return result

    except Exception as e:
        logger.exception(f"工作流执行异常: {e}")
        raise WorkflowException(
            message=f"工作流执行异常: {e}",
            node="workflow",
            state="running",
            details={"file_path": file_path, "error": str(e)},
        ) from e


async def run_workflow_batch(
    file_paths: list[str],
    condition_id: str | None = None,
    condition_config: dict[str, Any] | None = None,
    max_concurrency: int = 3,
) -> list[dict[str, Any]]:
    """批量运行简历处理工作流。

    并发处理多个简历文件，限制最大并发数。

    Args:
        file_paths: 简历文件路径列表
        condition_id: 筛选条件 ID
        condition_config: 筛选条件配置
        max_concurrency: 最大并发数，默认 3

    Returns:
        list[dict[str, Any]]: 工作流执行结果列表
    """
    import asyncio

    logger.info(f"开始批量处理简历: count={len(file_paths)}, max_concurrency={max_concurrency}")

    # 使用信号量限制并发数
    semaphore = asyncio.Semaphore(max_concurrency)

    async def run_with_semaphore(file_path: str) -> dict[str, Any]:
        """带并发限制的工作流执行。"""
        async with semaphore:
            return await run_resume_workflow(file_path, condition_id, condition_config)

    tasks = [run_with_semaphore(file_path) for file_path in file_paths]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理异常结果
    processed_results: list[dict[str, Any]] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(
                {
                    "file_path": file_paths[i],
                    "error_message": str(result),
                    "workflow_status": "failed",
                }
            )
        else:
            processed_results.append(result)  # type: ignore

    # 统计结果
    success_count = sum(1 for r in processed_results if not r.get("error_message"))
    qualified_count = sum(1 for r in processed_results if r.get("is_qualified"))

    logger.info(
        f"批量处理完成: total={len(file_paths)}, "
        f"success={success_count}, qualified={qualified_count}"
    )

    return processed_results


def get_workflow_graph() -> str:
    """获取工作流图的可视化表示。

    返回 Mermaid 格式的流程图。

    Returns:
        str: Mermaid 格式的流程图代码
    """
    return """
```mermaid
graph TD
    A[开始] --> B[ParseExtractNode]
    B --> C{解析成功?}
    C -->|是| D[FilterNode]
    C -->|否| Z[结束]
    D --> E{筛选成功?}
    E -->|是| F[StoreNode]
    E -->|否| Z
    F --> G{存储成功?}
    G -->|是| H[CacheNode]
    G -->|否| Z
    H --> Z

    B --> B1[文档解析]
    B --> B2[文本提取]
    B --> B3[LLM信息提取]

    D --> D1[快速预筛选]
    D --> D2[LLM深度筛选]

    F --> F1[MySQL存储]
    F --> F2[MinIO图片上传]
    F --> F3[ChromaDB向量存储]

    H --> H1[结果缓存]
    H --> H2[统计更新]
```
"""
