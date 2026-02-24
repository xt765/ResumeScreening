"""统计工具模块。

提供数据库统计查询功能，用于回答关于人才库数量、状态分布等问题。
"""

from contextlib import asynccontextmanager
from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from src.models import async_session_factory
import src.models as models
from src.models.talent import TalentInfo, ScreeningStatusEnum


@asynccontextmanager
async def get_session_context():
    """获取数据库会话上下文管理器。"""
    if async_session_factory is None:
        if models.async_session_factory is None:
            raise RuntimeError("数据库未初始化")
        async with models.async_session_factory() as session:
            yield session
    else:
        async with async_session_factory() as session:
            yield session


# 映射字典
EDUCATION_MAPPING = {
    "bachelor": "本科",
    "master": "硕士",
    "doctor": "博士",
    "college": "大专",
    "high_school": "高中及以下",
    "phd": "博士",
    "undergraduate": "本科",
    "graduate": "硕士",
}

STATUS_MAPPING = {
    "qualified": "qualified",  # 保持原值或映射到中文
    "unqualified": "unqualified",
    "pending": "pending",
    "passed": "qualified",
    "failed": "unqualified",
    "通过": "qualified",
    "淘汰": "unqualified",
    "待筛选": "pending",
}


class CountTalentsInput(BaseModel):
    status: Optional[str] = Field(
        default=None, 
        description="筛选状态，可选值: pending(待筛选), qualified(合格), unqualified(不合格), archived(归档)"
    )
    education: Optional[str] = Field(
        default=None,
        description="学历要求，例如: bachelor, master, doctor"
    )
    min_work_years: Optional[int] = Field(
        default=None,
        description="最小工作年限"
    )


class CountTalentsTool(BaseTool):
    name: str = "count_talents"
    description: str = (
        "统计符合条件的人才数量。当用户询问'有多少人'、'人才库统计'、'通过率'等问题时使用。"
        "支持按状态、学历、工作年限筛选。"
    )
    args_schema: Type[BaseModel] = CountTalentsInput

    def _run(self, **kwargs):
        raise NotImplementedError("CountTalentsTool 仅支持异步调用")

    async def _arun(
        self, 
        status: Optional[str] = None, 
        education: Optional[str] = None, 
        min_work_years: Optional[int] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行统计查询。"""
        async with get_session_context() as session:
            try:
                query = select(func.count()).select_from(TalentInfo).where(TalentInfo.is_deleted.is_(False))
                
                conditions = []
                if status:
                    # 映射状态
                    mapped_status = STATUS_MAPPING.get(status.lower(), status.lower())
                    
                    # 尝试匹配枚举
                    try:
                        # 注意：ScreeningStatusEnum 的值可能是 'pending' 等
                        # 这里做一个简单的映射或直接尝试
                        status_enum = None
                        for s in ScreeningStatusEnum:
                            if s.value == mapped_status:
                                status_enum = s
                                break
                        
                        if status_enum:
                            query = query.where(TalentInfo.screening_status == status_enum)
                            conditions.append(f"状态为 {status}")
                    except ValueError:
                        pass
                        
                if education:
                    # 映射学历
                    mapped_edu = EDUCATION_MAPPING.get(education.lower(), education)
                    # 模糊匹配或精确匹配？数据库存的是中文，这里使用精确匹配
                    query = query.where(TalentInfo.education_level == mapped_edu)
                    conditions.append(f"学历为 {mapped_edu}")
                    
                if min_work_years is not None:
                    query = query.where(TalentInfo.work_years >= min_work_years)
                    conditions.append(f"工作年限 >= {min_work_years}年")
                
                result = await session.execute(query)
                count = result.scalar() or 0
                
                cond_str = "，".join(conditions) if conditions else "所有"
                return f"统计结果：{cond_str} 的候选人共有 {count} 人。"
                
            except Exception as e:
                return f"统计查询失败: {e}"
