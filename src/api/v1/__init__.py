"""API v1 版本模块。

包含所有 v1 版本的 API 路由定义。
"""

from src.api.v1.analysis import router as analysis_router
from src.api.v1.conditions import router as conditions_router

__all__ = [
    "analysis_router",
    "conditions_router",
]
