"""自然语言解析服务模块。

使用 LLM 将自然语言描述转换为结构化筛选条件。
"""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import SecretStr

from src.core.config import get_settings
from src.schemas.condition import (
    ConditionConfig,
    EducationLevel,
    NLParseResponse,
    SchoolTier,
)


class NLPParserService:
    """自然语言解析服务。

    使用 LLM 将用户的自然语言描述转换为结构化的筛选条件配置。

    Attributes:
        llm: LangChain ChatOpenAI 实例。
    """

    def __init__(self) -> None:
        """初始化解析服务。"""
        settings = get_settings()
        self._api_key = settings.deepseek.api_key
        self._base_url = settings.deepseek.base_url
        self._model = settings.deepseek.model
        self._timeout = settings.app.llm_timeout
        self._max_retries = settings.app.llm_max_retries

    def _create_llm(self) -> ChatOpenAI:
        """创建 LLM 实例。

        Returns:
            ChatOpenAI: LangChain ChatOpenAI 实例。
        """
        return ChatOpenAI(
            api_key=SecretStr(self._api_key),
            base_url=self._base_url,
            model=self._model,
            temperature=0,
            timeout=self._timeout,
            max_retries=self._max_retries,
        )

    def _create_parse_prompt(self, text: str) -> list:
        """创建解析提示词。

        Args:
            text: 用户输入的自然语言描述。

        Returns:
            list: 消息列表。
        """
        system_prompt = """你是一个简历筛选条件解析助手。请将用户的自然语言描述转换为结构化的筛选条件。

请提取以下信息（如果用户描述中包含）：
1. 条件名称（name）：根据描述自动生成一个简洁的名称
2. 条件描述（description）：对筛选条件的简要说明
3. 学历要求（education_level）：可选值为 doctor(博士)/master(硕士)/bachelor(本科)/college(大专)/high_school(高中及以下)
4. 工作年限（experience_years）：最低工作年限（数字）
5. 学校层次（school_tier）：可选值为 top(985/C9)/key(211)/ordinary(普通)/overseas(海外)
6. 技能要求（skills）：技能名称列表
7. 专业要求（major）：专业名称列表

请以 JSON 格式返回结果，格式如下：
{
    "name": "条件名称",
    "description": "条件描述",
    "education_level": "bachelor",
    "experience_years": 3,
    "school_tier": "top",
    "skills": ["Python", "Java"],
    "major": ["计算机科学与技术"]
}

注意：
- 只返回 JSON，不要添加任何其他文字说明
- 如果某项信息用户未提及，则不要包含该字段
- 学历、学校层次等字段使用英文枚举值"""

        human_prompt = f"""请解析以下筛选条件描述：

{text}

请返回 JSON 格式的结果。"""

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

    def _map_education_level(self, value: str | None) -> EducationLevel | None:
        """映射学历值。

        Args:
            value: 原始学历值。

        Returns:
            EducationLevel | None: 学历枚举值。
        """
        if not value:
            return None

        mapping = {
            "doctor": EducationLevel.DOCTOR,
            "博士": EducationLevel.DOCTOR,
            "master": EducationLevel.MASTER,
            "硕士": EducationLevel.MASTER,
            "bachelor": EducationLevel.BACHELOR,
            "本科": EducationLevel.BACHELOR,
            "college": EducationLevel.COLLEGE,
            "大专": EducationLevel.COLLEGE,
            "high_school": EducationLevel.HIGH_SCHOOL,
            "高中": EducationLevel.HIGH_SCHOOL,
        }
        return mapping.get(value.lower() if isinstance(value, str) else value)

    def _map_school_tier(self, value: str | None) -> SchoolTier | None:
        """映射学校层次值。

        Args:
            value: 原始学校层次值。

        Returns:
            SchoolTier | None: 学校层次枚举值。
        """
        if not value:
            return None

        mapping = {
            "top": SchoolTier.TOP,
            "985": SchoolTier.TOP,
            "c9": SchoolTier.TOP,
            "key": SchoolTier.KEY,
            "211": SchoolTier.KEY,
            "ordinary": SchoolTier.ORDINARY,
            "普通": SchoolTier.ORDINARY,
            "overseas": SchoolTier.OVERSEAS,
            "海外": SchoolTier.OVERSEAS,
            "国外": SchoolTier.OVERSEAS,
        }
        return mapping.get(value.lower() if isinstance(value, str) else value)

    async def parse(self, text: str) -> NLParseResponse:
        """解析自然语言描述。

        Args:
            text: 用户输入的自然语言描述。

        Returns:
            NLParseResponse: 解析后的结构化筛选条件。

        Raises:
            ValueError: 解析失败或结果无效。
        """
        if not self._api_key:
            raise ValueError("LLM API Key 未配置，无法使用智能解析功能")

        try:
            llm = self._create_llm()
            messages = self._create_parse_prompt(text)
            response = await llm.ainvoke(messages)

            content = response.content
            if isinstance(content, str):
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                result: dict[str, Any] = json.loads(content)
            else:
                result = {}

            name = result.get("name", "智能筛选条件")
            description = result.get("description")

            config = ConditionConfig(
                education_level=self._map_education_level(result.get("education_level")),
                experience_years=result.get("experience_years"),
                school_tier=self._map_school_tier(result.get("school_tier")),
                skills=result.get("skills", []),
                major=result.get("major", []),
            )

            logger.info(
                f"自然语言解析完成: name={name}, "
                f"education_level={config.education_level}, "
                f"experience_years={config.experience_years}, "
                f"skills={config.skills}"
            )

            return NLParseResponse(
                name=name,
                description=description,
                config=config,
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise ValueError(f"解析结果格式错误: {e}") from e
        except Exception as e:
            logger.exception(f"自然语言解析失败: {e}")
            raise ValueError(f"解析失败: {e}") from e


nlp_parser = NLPParserService()
