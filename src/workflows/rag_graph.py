"""LangGraph Agentic RAG 工作流。

定义了简历筛选系统的智能体工作流，包括：
1. Agent: 负责理解意图、调用工具、生成回答
2. Tools: 执行具体任务（检索、统计）
"""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import SecretStr

from src.core.config import get_settings
from src.tools.search_tool import SearchTool
from src.tools.stats_tool import CountTalentsTool


# --- State Definition ---
class AgentState(TypedDict):
    # 使用 add_messages reducer 来自动追加消息
    messages: Annotated[list[BaseMessage], add_messages]


# --- Nodes ---

class AgentWorkflow:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=SecretStr(settings.deepseek.api_key),
            base_url=settings.deepseek.base_url,
            model=settings.deepseek.model,
            temperature=0,
        )
        self.tools = [SearchTool(), CountTalentsTool()]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System Prompt
        self.system_message = SystemMessage(content="""你是一个专业的简历筛选与分析助手。
你的职责是帮助 HR 用户查询候选人信息、统计人才库数据，并提供专业的招聘建议。

你拥有以下工具：
1. search_resumes: 用于检索候选人简历。当用户询问具体的候选人、技能匹配、职位匹配时使用。
   - 请根据用户的具体要求（如学历、工作年限、技能）提取关键信息作为查询参数。
2. count_talents: 用于统计人才数量。当用户询问“有多少人”、“通过率”、“分布情况”时使用。

工作流程：
- 首先分析用户的意图。
- 如果需要查询数据，请调用相应的工具。
- 如果工具返回了结果，请基于结果生成专业的回答。
- 如果是闲聊或不需要查库的问题，请直接礼貌回答。

注意事项：
- 回答要客观、准确，基于事实（工具返回的数据）。
- 如果没有找到相关信息，请明确告知用户。
- 对于简历检索结果，请总结候选人的核心优势。
""")

    async def agent_node(self, state: AgentState):
        """Agent 节点：调用 LLM 决策。"""
        # 将 system message 放在最前面
        messages = [self.system_message] + state["messages"]
        response = await self.llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def build_graph(self):
        """构建 LangGraph 图。"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        # 添加边
        workflow.add_edge(START, "agent")
        
        # 条件边：Agent -> Tools 或 End
        workflow.add_conditional_edges(
            "agent",
            tools_condition,
            {
                "tools": "tools",
                END: END,
            }
        )

        # Tools -> Agent (ReAct 循环)
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()


# 单例
_agent_workflow = None

def get_agent_workflow():
    global _agent_workflow
    if _agent_workflow is None:
        _agent_workflow = AgentWorkflow().build_graph()
    return _agent_workflow
