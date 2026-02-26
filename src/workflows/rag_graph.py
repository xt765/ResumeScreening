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
        self.system_message = """你是一个专业的简历筛选与分析助手。
你的职责是帮助 HR 用户查询候选人信息、统计人才库数据，并提供专业的招聘建议。

你拥有以下工具：
1. search_resumes: 用于检索候选人简历。当用户询问具体的候选人、技能匹配、职位匹配时使用。
2. count_talents: 用于统计人才数量。当用户询问"有多少人"、"通过率"、"分布情况"时使用。

工作流程：
- 首先分析用户的意图。
- 如果需要查询数据，请调用相应的工具。
- 如果工具返回了结果，请基于结果生成专业的回答。
- 如果是闲聊或不需要查库的问题，请直接礼貌回答。

## 报告格式要求

### 结构要求
1. **概述**：简要说明查询目的和匹配结果概况（1-2句话）
2. **核心分析**：深入分析候选人的整体特征、优势和匹配度
3. **推荐建议**：基于分析给出招聘建议

### 内容要求
- **侧重分析而非罗列**：不要逐个详细列出候选人的所有信息，而是提炼关键特征和趋势
- **使用姓名引用**：提及具体候选人时，直接使用姓名。评分格式为：**姓名：XX分**（例如：**李明：85分**）
- **禁止末尾问句**：报告末尾不要添加"您需要了解更多信息吗？"等问句
- **数据驱动**：分析结论要有数据支撑

### 评分标准
为每位候选人给出推荐指数（0-100分），综合考虑：
1. 职位匹配度（技能、经验是否符合要求）
2. 候选人素质（学历、工作年限、项目经验）
3. 简历完整度与专业性

评分格式示例：
**李明：85分** - 拥有6年Java经验，具备金融行业背景，技能匹配度高。
**王华：78分** - 5年Python开发经验，熟悉Django框架。

## 注意事项
- 回答要客观、准确，基于工具返回的数据
- 如果没有找到相关信息，请明确告知用户
- 分析要有深度，提供有价值的招聘洞察
- **禁止输出思考过程**：不要输出"基于搜索结果..."、"让我分析..."、"我发现..."等思考过程，直接输出最终的分析报告
"""

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
