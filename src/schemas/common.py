"""通用响应模型模块。

提供统一的 API 响应格式和分页响应模型。
"""

from pydantic import BaseModel, Field


class PaginatedResponse[T](BaseModel):
    """分页响应模型。

    用于返回分页数据的统一格式。

    Attributes:
        items: 当前页的数据列表。
        total: 总记录数。
        page: 当前页码（从 1 开始）。
        page_size: 每页记录数。
        total_pages: 总页数。
    """

    items: list[T] = Field(..., description="当前页的数据列表")
    total: int = Field(..., ge=0, description="总记录数")
    page: int = Field(..., ge=1, description="当前页码（从 1 开始）")
    page_size: int = Field(..., ge=1, le=100, description="每页记录数")
    total_pages: int = Field(..., ge=0, description="总页数")


class APIResponse[T](BaseModel):
    """统一 API 响应模型。

    提供统一的 API 响应格式，包含成功状态、消息和数据。

    Attributes:
        success: 操作是否成功。
        message: 响应消息。
        data: 响应数据。
    """

    success: bool = Field(default=True, description="操作是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")
