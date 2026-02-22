"""筛选节点模块。

负责使用 LLM 根据筛选条件判断候选人是否符合要求。
支持技能匹配、学历要求、工作年限等多维度筛选。
"""

import json
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from src.core.config import get_settings
from src.core.exceptions import LLMException, WorkflowException
from src.workflows.state import FilterResult, ResumeState


def _build_filter_prompt(
    candidate_info: dict[str, Any],
    condition_config: dict[str, Any],
) -> tuple[str, str]:
    """构建筛选提示词。

    Args:
        candidate_info: 候选人信息
        condition_config: 筛选条件配置

    Returns:
        tuple[str, str]: 系统提示词和用户提示词
    """
    system_prompt = """你是一个专业的简历筛选助手。请根据给定的筛选条件，判断候选人是否符合要求。

你需要：
1. 仔细分析候选人的各项信息
2. 与筛选条件逐一对比
3. 给出综合评分（0-100分）
4. 判断是否通过筛选（符合条件返回 true）
5. 说明判断理由

请以 JSON 格式返回结果，包含以下字段：
- is_qualified: 布尔值，是否通过筛选
- score: 整数，综合评分（0-100）
- reason: 字符串，判断理由的简要说明
- matched_criteria: 数组，匹配的条件列表
- unmatched_criteria: 数组，不匹配的条件列表

注意：只要候选人满足核心条件（学历、工作年限、关键技能），就应该通过筛选。"""

    # 构建条件描述
    conditions_desc = []
    if condition_config.get("skills"):
        conditions_desc.append(f"技能要求: {', '.join(condition_config['skills'])}")
    if condition_config.get("education_level"):
        conditions_desc.append(f"学历要求: {condition_config['education_level']}")
    if condition_config.get("experience_years"):
        conditions_desc.append(f"工作年限要求: {condition_config['experience_years']} 年及以上")
    if condition_config.get("major"):
        conditions_desc.append(f"专业要求: {', '.join(condition_config['major'])}")
    if condition_config.get("school_tier"):
        conditions_desc.append(f"院校层次要求: {', '.join(condition_config['school_tier'])}")

    conditions_text = "\n".join(f"- {c}" for c in conditions_desc)

    human_prompt = f"""请根据以下信息进行筛选判断：

【筛选条件】
{conditions_text}

【候选人信息】
姓名: {candidate_info.get("name", "未知")}
学历: {candidate_info.get("education_level", "未知")}
毕业院校: {candidate_info.get("school", "未知")}
专业: {candidate_info.get("major", "未知")}
工作年限: {candidate_info.get("work_years", 0)} 年
技能: {", ".join(candidate_info.get("skills", []))}

请返回 JSON 格式的筛选结果。"""

    return system_prompt, human_prompt


def _parse_filter_response(content: str) -> FilterResult:
    """解析 LLM 筛选响应。

    Args:
        content: LLM 响应内容

    Returns:
        FilterResult: 筛选结果

    Raises:
        LLMException: 响应解析失败
    """
    try:
        # 清理可能的 markdown 代码块标记
        cleaned_content = content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:]
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()

        result = json.loads(cleaned_content)

        return FilterResult(
            is_qualified=bool(result.get("is_qualified", False)),
            score=int(result.get("score", 0)),
            reason=str(result.get("reason", "")),
            matched_criteria=list(result.get("matched_criteria", [])),
            unmatched_criteria=list(result.get("unmatched_criteria", [])),
        )

    except Exception as e:
        logger.exception(f"解析筛选响应失败: {e}")
        raise LLMException(
            message=f"筛选结果解析失败: {e}",
            provider="deepseek",
            model="unknown",
            details={"raw_content": content[:500]},
        ) from e


def _call_llm_filter(
    candidate_info: dict[str, Any],
    condition_config: dict[str, Any],
) -> FilterResult:
    """调用 LLM 进行筛选判断。

    Args:
        candidate_info: 候选人信息
        condition_config: 筛选条件配置

    Returns:
        FilterResult: 筛选结果

    Raises:
        LLMException: LLM 调用失败
    """
    settings = get_settings()

    if not settings.deepseek.api_key:
        logger.warning("DeepSeek API Key 未配置，默认通过筛选")
        return FilterResult(
            is_qualified=True,
            score=60,
            reason="API Key 未配置，默认通过",
            matched_criteria=[],
            unmatched_criteria=[],
        )

    try:
        from pydantic import SecretStr

        llm = ChatOpenAI(
            api_key=SecretStr(settings.deepseek.api_key),
            base_url=settings.deepseek.base_url,
            model=settings.deepseek.model,
            temperature=0,
            timeout=settings.app.llm_timeout,
            max_retries=settings.app.llm_max_retries,
        )

        system_prompt, human_prompt = _build_filter_prompt(candidate_info, condition_config)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        logger.info(f"调用 LLM 进行筛选: candidate={candidate_info.get('name', 'unknown')}")
        response = llm.invoke(messages)

        content = response.content
        if not isinstance(content, str):
            raise LLMException(
                message="LLM 响应格式错误",
                provider="deepseek",
                model=settings.deepseek.model,
            )

        return _parse_filter_response(content)

    except LLMException:
        raise
    except Exception as e:
        logger.exception(f"LLM 筛选调用失败: {e}")
        raise LLMException(
            message=f"LLM 筛选调用失败: {e}",
            provider="deepseek",
            model=settings.deepseek.model,
            details={"error": str(e)},
        ) from e


def _quick_filter(
    candidate_info: dict[str, Any],
    condition_config: dict[str, Any],
) -> FilterResult | None:
    """快速预筛选。

    在调用 LLM 之前进行简单的规则匹配，可以快速过滤明显不符合条件的候选人。

    Args:
        candidate_info: 候选人信息
        condition_config: 筛选条件配置

    Returns:
        FilterResult | None: 如果可以快速判断则返回结果，否则返回 None
    """
    unmatched: list[str] = []
    matched: list[str] = []

    # 学历快速筛选
    required_education = condition_config.get("education_level", "")
    if required_education:
        candidate_education = candidate_info.get("education_level", "")
        education_levels = ["高中", "大专", "本科", "硕士", "博士"]
        try:
            req_idx = education_levels.index(required_education)
            cand_idx = (
                education_levels.index(candidate_education)
                if candidate_education in education_levels
                else -1
            )
            if cand_idx >= req_idx:
                matched.append(f"学历符合: {candidate_education}")
            else:
                unmatched.append(f"学历不足: 要求{required_education}，实际{candidate_education}")
        except ValueError:
            pass  # 无法比较的学历，交给 LLM 判断

    # 工作年限快速筛选
    required_years = condition_config.get("experience_years", 0)
    if required_years > 0:
        candidate_years = candidate_info.get("work_years", 0)
        if candidate_years >= required_years:
            matched.append(f"工作年限符合: {candidate_years}年")
        else:
            unmatched.append(f"工作年限不足: 要求{required_years}年，实际{candidate_years}年")

    # 如果有明确的硬性条件不满足，快速拒绝
    if unmatched and not matched:
        return FilterResult(
            is_qualified=False,
            score=30,
            reason="快速筛选: 不满足基本条件",
            matched_criteria=matched,
            unmatched_criteria=unmatched,
        )

    # 无法快速判断，返回 None 让 LLM 处理
    return None


async def filter_node(state: ResumeState) -> dict[str, Any]:
    """筛选节点。

    根据筛选条件判断候选人是否符合要求：
    1. 快速预筛选（规则匹配）
    2. LLM 深度筛选
    3. 返回筛选结果

    Args:
        state: 当前工作流状态

    Returns:
        dict[str, Any]: 状态更新字典

    Raises:
        WorkflowException: 工作流执行失败
        LLMException: LLM 调用失败
    """
    start_time = time.time()
    logger.info("开始筛选节点")

    try:
        # 验证必要数据
        if not state.candidate_info:
            raise WorkflowException(
                message="候选人信息为空，无法进行筛选",
                node="filter_node",
                state=state.workflow_status,
            )

        if not state.condition_config:
            logger.warning("筛选条件为空，默认通过筛选")
            return {
                "is_qualified": True,
                "qualification_reason": "无筛选条件，默认通过",
                "workflow_status": "filtered",
            }

        candidate_info = state.candidate_info
        condition_config = state.condition_config

        # 1. 快速预筛选
        quick_result = _quick_filter(candidate_info, condition_config)

        if quick_result:
            logger.info(
                f"快速筛选完成: is_qualified={quick_result.is_qualified}, "
                f"score={quick_result.score}"
            )
            filter_result = quick_result
        else:
            # 2. LLM 深度筛选
            filter_result = _call_llm_filter(candidate_info, condition_config)

        elapsed_time = int((time.time() - start_time) * 1000)
        logger.info(
            f"筛选节点完成: is_qualified={filter_result.is_qualified}, "
            f"score={filter_result.score}, elapsed_time={elapsed_time}ms"
        )

        return {
            "is_qualified": filter_result.is_qualified,
            "qualification_reason": filter_result.reason,
            "workflow_status": "filtered",
        }

    except (WorkflowException, LLMException):
        raise
    except Exception as e:
        logger.exception(f"筛选节点执行失败: {e}")
        raise WorkflowException(
            message=f"筛选节点执行失败: {e}",
            node="filter_node",
            state=state.workflow_status,
            details={"error": str(e)},
        ) from e
