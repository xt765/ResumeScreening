"""检索工具模块。

封装混合检索器，提供给 LangGraph Agent 使用。
"""

from typing import Any, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.retriever import get_hybrid_retriever


class SearchInput(BaseModel):
    """检索工具输入参数。"""
    query: str = Field(description="查询关键词或问题，例如'Python 工程师'或'寻找会 Vue.js 的候选人'")
    top_k: int = Field(default=5, description="返回结果数量")
    filters: dict[str, Any] | None = Field(default=None, description="元数据过滤条件")


class SearchTool(BaseTool):
    """候选人简历检索工具。"""
    name: str = "search_resumes"
    description: str = (
        "用于检索候选人简历。当用户需要查找特定技能、背景、学历或职位的候选人时使用此工具。"
        "该工具结合了语义搜索和关键词匹配，能精确找到相关候选人。"
        "注意：此工具会自动过滤已删除的候选人记录。"
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(
        self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """同步执行（不支持，请使用 invoke/ainvoke）。"""
        raise NotImplementedError("SearchTool 仅支持异步调用")

    async def _arun(
        self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行检索。"""
        retriever = get_hybrid_retriever()
        
        if not retriever._initialized:
            retriever.initialize()
        
        if filters is None:
            filters = {}
        filters["is_deleted"] = False
        
        docs = await retriever.retrieve(query, top_k=top_k, filters=filters)
        
        if not docs:
            return "未找到相关候选人简历。"
            
        results = []
        for i, doc in enumerate(docs, 1):
            metadata = doc.metadata
            content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            
            info = (
                f"【候选人 {i}】\n"
                f"姓名: {metadata.get('name', '未知')}\n"
                f"学校: {metadata.get('school', '未知')}\n"
                f"学历: {metadata.get('education_level', '未知')}\n"
                f"专业: {metadata.get('major', '未知')}\n"
                f"工作年限: {metadata.get('work_years', '未知')}年\n"
                f"技能: {metadata.get('skills', '未知')}\n"
                f"ID: {metadata.get('id', '未知')}\n"
                f"简历摘要: {content}\n"
            )
            results.append(info)
            
        return "\n".join(results)
