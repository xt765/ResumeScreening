"""缓存节点模块。

负责将工作流结果缓存到 Redis，支持：
- 筛选结果缓存
- 候选人信息缓存
- 工作流状态缓存
"""

from datetime import datetime
import time
from typing import Any

from loguru import logger

from src.core.exceptions import CacheException, WorkflowException
from src.storage.redis_client import redis_client
from src.workflows.state import ResumeState

# 缓存键前缀
CACHE_PREFIX = "resume:workflow:"

# 缓存过期时间（秒）
DEFAULT_EXPIRE = 3600 * 24  # 24 小时
RESULT_EXPIRE = 3600 * 72  # 72 小时（筛选结果缓存更久）


def _generate_cache_key(file_path: str) -> str:
    """生成缓存键。

    使用文件路径的哈希作为缓存键。

    Args:
        file_path: 文件路径

    Returns:
        str: 缓存键
    """
    import hashlib

    file_hash = hashlib.md5(file_path.encode()).hexdigest()
    return f"{CACHE_PREFIX}{file_hash}"


def _build_cache_data(state: ResumeState) -> dict[str, Any]:
    """构建缓存数据。

    将工作流状态转换为可缓存的字典格式。

    Args:
        state: 工作流状态

    Returns:
        dict[str, Any]: 缓存数据
    """
    return {
        "file_path": state.file_path,
        "file_type": state.file_type,
        "talent_id": state.talent_id,
        "candidate_info": state.candidate_info,
        "condition_id": state.condition_id,
        "is_qualified": state.is_qualified,
        "qualification_reason": state.qualification_reason,
        "photo_urls": state.photo_urls,
        "workflow_status": state.workflow_status,
        "cached_at": datetime.now().isoformat(),
    }


async def _check_existing_cache(file_path: str) -> dict[str, Any] | None:
    """检查是否存在缓存。

    Args:
        file_path: 文件路径

    Returns:
        dict[str, Any] | None: 缓存数据，不存在返回 None
    """
    try:
        cache_key = _generate_cache_key(file_path)
        cached_data = await redis_client.get_json(cache_key)

        if cached_data:
            logger.info(f"发现已有缓存: key={cache_key}")
            return cached_data  # type: ignore

        return None

    except Exception as e:
        logger.warning(f"检查缓存失败: {e}")
        return None


async def _save_to_cache(
    file_path: str,
    data: dict[str, Any],
    expire: int = DEFAULT_EXPIRE,
) -> bool:
    """保存数据到缓存。

    Args:
        file_path: 文件路径（用于生成缓存键）
        data: 缓存数据
        expire: 过期时间（秒）

    Returns:
        bool: 保存成功返回 True

    Raises:
        CacheException: 缓存操作失败
    """
    try:
        cache_key = _generate_cache_key(file_path)
        await redis_client.set_json(cache_key, data, expire=expire)

        logger.info(f"缓存保存成功: key={cache_key}, expire={expire}s")
        return True

    except Exception as e:
        logger.exception(f"缓存保存失败: {e}")
        raise CacheException(
            message=f"缓存保存失败: {e}",
            operation="set",
            details={"file_path": file_path, "error": str(e)},
        ) from e


async def _cache_candidate_info(talent_id: str, info: dict[str, Any]) -> bool:
    """缓存候选人信息。

    将候选人信息单独缓存，便于后续查询。

    Args:
        talent_id: 人才 ID
        info: 候选人信息

    Returns:
        bool: 缓存成功返回 True
    """
    try:
        cache_key = f"resume:candidate:{talent_id}"
        await redis_client.set_json(cache_key, info, expire=RESULT_EXPIRE)

        logger.debug(f"候选人信息缓存成功: talent_id={talent_id}")
        return True

    except Exception as e:
        logger.warning(f"候选人信息缓存失败: {e}")
        return False


async def _cache_screening_result(
    talent_id: str,
    condition_id: str,
    is_qualified: bool,
    reason: str,
) -> bool:
    """缓存筛选结果。

    将筛选结果按条件 ID 缓存，便于统计和查询。

    Args:
        talent_id: 人才 ID
        condition_id: 筛选条件 ID
        is_qualified: 是否通过筛选
        reason: 筛选原因

    Returns:
        bool: 缓存成功返回 True
    """
    try:
        # 缓存筛选结果
        result_key = f"resume:screening:{condition_id}:{talent_id}"
        result_data = {
            "talent_id": talent_id,
            "is_qualified": is_qualified,
            "reason": reason,
            "screened_at": datetime.now().isoformat(),
        }
        await redis_client.set_json(result_key, result_data, expire=RESULT_EXPIRE)

        # 更新条件的筛选统计
        stats_key = f"resume:stats:{condition_id}"
        raw_stats = await redis_client.get_json(stats_key)

        stats_data: dict[str, int]
        if raw_stats is None or not isinstance(raw_stats, dict):
            stats_data = {"total": 0, "qualified": 0, "disqualified": 0}
        else:
            stats_data = raw_stats  # type: ignore[assignment]

        stats_data["total"] = stats_data.get("total", 0) + 1
        if is_qualified:
            stats_data["qualified"] = stats_data.get("qualified", 0) + 1
        else:
            stats_data["disqualified"] = stats_data.get("disqualified", 0) + 1

        await redis_client.set_json(stats_key, stats_data, expire=RESULT_EXPIRE)

        logger.debug(
            f"筛选结果缓存成功: talent_id={talent_id}, "
            f"condition_id={condition_id}, qualified={is_qualified}"
        )
        return True

    except Exception as e:
        logger.warning(f"筛选结果缓存失败: {e}")
        return False


async def cache_node(state: ResumeState) -> dict[str, Any]:
    """缓存节点。

    将工作流结果缓存到 Redis：
    1. 缓存完整的工作流结果
    2. 缓存候选人信息（按 talent_id）
    3. 缓存筛选结果（按 condition_id）
    4. 更新筛选统计
    5. 更新数据库中的工作流状态

    Args:
        state: 当前工作流状态

    Returns:
        dict[str, Any]: 状态更新字典

    Raises:
        WorkflowException: 工作流执行失败
    """
    start_time = time.time()
    logger.info("开始缓存节点")

    try:
        # 验证必要数据
        if not state.talent_id:
            raise WorkflowException(
                message="人才 ID 为空，无法缓存",
                node="cache_node",
                state=state.workflow_status,
            )

        # 1. 缓存完整工作流结果
        cache_data = _build_cache_data(state)
        await _save_to_cache(state.file_path, cache_data, expire=RESULT_EXPIRE)

        # 2. 缓存候选人信息
        if state.candidate_info:
            await _cache_candidate_info(state.talent_id, state.candidate_info)

        # 3. 缓存筛选结果
        if state.condition_id:
            await _cache_screening_result(
                state.talent_id,
                state.condition_id,
                state.is_qualified or False,
                state.qualification_reason or "",
            )

        # 4. 更新数据库中的工作流状态
        from src.models import TalentInfo, WorkflowStatusEnum, async_session_factory
        from sqlalchemy import update

        if async_session_factory is not None:
            async with async_session_factory() as session:
                stmt = (
                    update(TalentInfo)
                    .where(TalentInfo.id == state.talent_id)
                    .values(workflow_status=WorkflowStatusEnum.COMPLETED)
                )
                await session.execute(stmt)
                await session.commit()
                logger.info(f"更新工作流状态为 completed: talent_id={state.talent_id}")

        elapsed_time = int((time.time() - start_time) * 1000)
        logger.info(f"缓存节点完成: talent_id={state.talent_id}, elapsed_time={elapsed_time}ms")

        return {
            "workflow_status": "completed",
            "processing_time": elapsed_time,
        }

    except (WorkflowException, CacheException):
        raise
    except Exception as e:
        logger.exception(f"缓存节点执行失败: {e}")
        raise WorkflowException(
            message=f"缓存节点执行失败: {e}",
            node="cache_node",
            state=state.workflow_status,
            details={"error": str(e)},
        ) from e


async def get_cached_result(file_path: str) -> dict[str, Any] | None:
    """获取缓存的工作流结果。

    用于在重新处理同一文件时跳过已处理的结果。

    Args:
        file_path: 文件路径

    Returns:
        dict[str, Any] | None: 缓存的结果，不存在返回 None
    """
    return await _check_existing_cache(file_path)


async def get_cached_candidate(talent_id: str) -> dict[str, Any] | None:
    """获取缓存的候选人信息。

    Args:
        talent_id: 人才 ID

    Returns:
        dict[str, Any] | None: 候选人信息
    """
    try:
        cache_key = f"resume:candidate:{talent_id}"
        return await redis_client.get_json(cache_key)  # type: ignore
    except Exception as e:
        logger.warning(f"获取候选人缓存失败: {e}")
        return None


async def get_screening_stats(condition_id: str) -> dict[str, int] | None:
    """获取筛选统计。

    Args:
        condition_id: 筛选条件 ID

    Returns:
        dict[str, int] | None: 统计数据
    """
    try:
        stats_key = f"resume:stats:{condition_id}"
        stats = await redis_client.get_json(stats_key)
        return stats if stats else None  # type: ignore
    except Exception as e:
        logger.warning(f"获取筛选统计失败: {e}")
        return None


async def invalidate_cache(file_path: str) -> bool:
    """使缓存失效。

    删除指定文件的缓存数据。

    Args:
        file_path: 文件路径

    Returns:
        bool: 删除成功返回 True
    """
    try:
        cache_key = _generate_cache_key(file_path)
        await redis_client.delete_cache(cache_key)
        logger.info(f"缓存已失效: key={cache_key}")
        return True
    except Exception as e:
        logger.warning(f"缓存失效操作失败: {e}")
        return False
