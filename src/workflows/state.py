"""工作流状态定义模块。

定义 LangGraph 工作流的状态数据结构，用于在节点间传递数据。
使用 Pydantic 模型确保类型安全和数据验证。
"""

from typing import Any

from pydantic import BaseModel, Field


class ResumeState(BaseModel):
    """简历处理工作流状态。

    在 LangGraph 节点间传递的状态数据，包含简历处理的完整生命周期数据。

    Attributes:
        file_path: 简历文件路径
        file_content: 文件二进制内容
        file_type: 文件类型（pdf, docx）
        text_content: 提取的文本内容
        images: 提取的图片列表
        candidate_info: LLM 提取的候选人信息
        condition_id: 筛选条件 ID
        condition_config: 筛选条件配置
        is_qualified: 是否符合筛选条件
        qualification_reason: 筛选结果原因
        talent_id: 入库后的人才 ID
        photo_urls: 照片存储 URL 列表
        error_message: 错误信息
        workflow_status: 工作流状态
        processing_time: 处理耗时（毫秒）
    """

    # 输入数据
    file_path: str = Field(..., description="简历文件路径")
    file_content: bytes | None = Field(default=None, description="文件二进制内容")
    file_type: str | None = Field(default=None, description="文件类型")
    content_hash: str | None = Field(default=None, description="简历内容哈希（SHA256，用于去重）")

    # 解析提取结果
    text_content: str | None = Field(default=None, description="提取的文本内容")
    images: list[bytes] | None = Field(default=None, description="提取的图片列表")

    # LLM 提取结果
    candidate_info: dict[str, Any] | None = Field(default=None, description="LLM 提取的候选人信息")

    # 筛选条件
    condition_id: str | None = Field(default=None, description="筛选条件 ID")
    condition_config: dict[str, Any] | None = Field(default=None, description="筛选条件配置")

    # 筛选结果
    is_qualified: bool | None = Field(default=None, description="是否符合筛选条件")
    qualification_reason: str | None = Field(default=None, description="筛选结果原因")

    # 存储结果
    talent_id: str | None = Field(default=None, description="入库后的人才 ID")
    photo_urls: list[str] | None = Field(default=None, description="照片存储 URL 列表")

    # 错误处理
    error_message: str | None = Field(default=None, description="错误信息")
    error_node: str | None = Field(default=None, description="发生错误的节点名称")

    # 工作流状态
    workflow_status: str = Field(default="pending", description="工作流状态")
    processing_time: int | None = Field(default=None, description="处理耗时（毫秒）")

    model_config = {"arbitrary_types_allowed": True}


class NodeResult(BaseModel):
    """节点执行结果。

    统一的节点返回格式，包含执行状态和数据更新。

    Attributes:
        success: 是否执行成功
        updates: 状态更新字典
        error: 错误信息（失败时）
        should_continue: 是否继续执行下一个节点
    """

    success: bool = Field(default=True, description="是否执行成功")
    updates: dict[str, Any] = Field(default_factory=dict, description="状态更新")
    error: str | None = Field(default=None, description="错误信息")
    should_continue: bool = Field(default=True, description="是否继续执行")

    model_config = {"arbitrary_types_allowed": True}


class ParseResult(BaseModel):
    """文档解析结果。

    包含从简历文档中提取的文本和图片。

    Attributes:
        text: 提取的文本内容
        images: 提取的图片字节列表
        page_count: 页数
        char_count: 字符数
    """

    text: str = Field(default="", description="提取的文本内容")
    images: list[bytes] = Field(default_factory=list, description="提取的图片列表")
    page_count: int = Field(default=0, description="页数")
    char_count: int = Field(default=0, description="字符数")


class CandidateInfo(BaseModel):
    """候选人信息模型。

    LLM 从简历中提取的结构化候选人信息。

    Attributes:
        name: 姓名
        phone: 电话
        email: 邮箱
        education_level: 学历
        school: 毕业院校
        major: 专业
        graduation_date: 毕业日期
        skills: 技能列表
        work_years: 工作年限
        work_experience: 工作经历
        projects: 项目经历
    """

    name: str = Field(default="", description="姓名")
    phone: str = Field(default="", description="电话")
    email: str = Field(default="", description="邮箱")
    education_level: str = Field(default="", description="学历")
    school: str = Field(default="", description="毕业院校")
    major: str = Field(default="", description="专业")
    graduation_date: str | None = Field(default=None, description="毕业日期")
    skills: list[str] = Field(default_factory=list, description="技能列表")
    work_years: int = Field(default=0, description="工作年限")
    work_experience: list[dict[str, Any]] = Field(default_factory=list, description="工作经历")
    projects: list[dict[str, Any]] = Field(default_factory=list, description="项目经历")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式。

        Returns:
            dict[str, Any]: 候选人信息字典
        """
        return self.model_dump()


class FilterResult(BaseModel):
    """筛选结果模型。

    LLM 筛选判断的结果。

    Attributes:
        is_qualified: 是否符合条件
        score: 匹配分数（0-100）
        reason: 筛选原因
        matched_criteria: 匹配的条件列表
        unmatched_criteria: 不匹配的条件列表
    """

    is_qualified: bool = Field(..., description="是否符合条件")
    score: int = Field(default=0, ge=0, le=100, description="匹配分数")
    reason: str = Field(default="", description="筛选原因")
    matched_criteria: list[str] = Field(default_factory=list, description="匹配的条件列表")
    unmatched_criteria: list[str] = Field(default_factory=list, description="不匹配的条件列表")
