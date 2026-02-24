"""检索工具模块。

封装混合检索器，提供给 LangGraph Agent 使用。
"""

from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.retriever import get_hybrid_retriever


class SearchInput(BaseModel):
    query: str = Field(description="查询关键词或问题，例如'Python 工程师'或'寻找会 Vue.js 的候选人'")
    top_k: int = Field(default=5, description="返回结果数量")


class SearchTool(BaseTool):
    name: str = "search_resumes"
    description: str = (
        "用于检索候选人简历。当用户需要查找特定技能、背景、学历或职位的候选人时使用此工具。"
        "该工具结合了语义搜索和关键词匹配，能精确找到相关候选人。"
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(
        self, query: str, top_k: int = 5, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """同步执行（不支持，请使用 invoke/ainvoke）。"""
        raise NotImplementedError("SearchTool 仅支持异步调用")

    async def _arun(
        self, query: str, top_k: int = 5, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行检索。"""
        retriever = get_hybrid_retriever()
        
        # 确保检索器已初始化
        if not retriever._initialized:
            retriever.initialize()
            
        docs = await retriever.retrieve(query, top_k=top_k)
        
        if not docs:
            return "未找到相关候选人简历。"
            
        # 格式化结果供 LLM 阅读
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
