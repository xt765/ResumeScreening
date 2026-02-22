"""Pydantic Schema 模块。

提供所有数据模型的统一导出。

Example:
    from schemas import (
        APIResponse,
        PaginatedResponse,
        ConditionCreate,
        ConditionUpdate,
        ConditionResponse,
        ConditionQuery,
        CandidateInfo,
        TalentCreate,
        TalentResponse,
        TalentQuery,
        TalentListResponse,
    )
"""

from .common import APIResponse, PaginatedResponse
from .condition import (
    ConditionConfig,
    ConditionCreate,
    ConditionQuery,
    ConditionResponse,
    ConditionUpdate,
    EducationLevel,
    SchoolTier,
)
from .talent import (
    CandidateInfo,
    TalentCreate,
    TalentListResponse,
    TalentQuery,
    TalentResponse,
)

__all__ = [
    "APIResponse",
    "CandidateInfo",
    "ConditionConfig",
    "ConditionCreate",
    "ConditionQuery",
    "ConditionResponse",
    "ConditionUpdate",
    "EducationLevel",
    "PaginatedResponse",
    "SchoolTier",
    "TalentCreate",
    "TalentListResponse",
    "TalentQuery",
    "TalentResponse",
]
