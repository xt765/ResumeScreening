"""RAG 检索服务模块。

结合 Agentic RAG 工作流，支持基于简历数据的智能问答与分析。
"""

import time
import asyncio
import json
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from loguru import logger

from src.core.config import get_settings
from src.core.exceptions import LLMException
from src.utils.retriever import get_hybrid_retriever
from src.workflows.rag_graph import get_agent_workflow


class RAGService:
    """RAG 服务类。

    使用 LangGraph Agentic RAG 架构。
    
    Attributes:
        agent_workflow: LangGraph 编译后的工作流
    """

    def __init__(self) -> None:
        """初始化 RAG 服务。"""
        self._workflow = get_agent_workflow()
        
        # 初始化 LLM 用于评分
        settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=SecretStr(settings.deepseek.api_key),
            base_url=settings.deepseek.base_url,
            model=settings.deepseek.model,
            temperature=0,
        )

    async def _evaluate_candidates(self, query: str, docs: list[Any]) -> dict[str, dict]:
        """使用 LLM 评估候选人与查询的匹配度。
        
        Args:
            query: 用户查询
            docs: 候选人文档列表
            
        Returns:
            dict: {doc_id: {"score": float, "reason": str}}
        """
        if not docs:
            return {}
            
        try:
            # 构建评估 Prompt
            candidates_text = ""
            for i, doc in enumerate(docs):
                doc_id = doc.metadata.get("id", str(i))
                content = doc.page_content[:500]  # 截取前500字符避免超长
                candidates_text += f"ID: {doc_id}\nContent: {content}\n---\n"
                
            prompt = f"""你是一个专业的招聘专家。请根据职位要求评估以下候选人。

职位要求: {query}

候选人列表:
{candidates_text}

请对每位候选人进行评分（0-100分）并给出简短理由（不超过50字）。
必须返回合法的 JSON 格式，不要包含 Markdown 代码块标记。
格式如下：
{{
    "candidate_id_1": {{"score": 85, "reason": "匹配度高..."}},
    "candidate_id_2": {{"score": 60, "reason": "经验不足..."}}
}}
"""
            # 调用 LLM
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a helpful assistant that outputs JSON."),
                HumanMessage(content=prompt)
            ])
            
            # 解析 JSON
            content = response.content.strip()
            # 移除可能的 markdown 标记
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"AI 评分失败: {e}")
            return {}

    async def query(
        self,
        question: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行 RAG 查询。

        Args:
            question: 用户问题
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            包含答案和来源的字典。
        """
        start_time = time.time()
        logger.info(f"开始 Agentic RAG 查询: question={question[:50]}...")

        try:
            # 并行执行 Agent 工作流（生成回答）和 检索+评估（生成列表）
            
            # 任务 1: Agent 工作流
            async def run_agent():
                inputs = {"messages": [HumanMessage(content=question)]}
                final_state = await self._workflow.ainvoke(inputs)
                return final_state["messages"][-1].content

            # 任务 2: 检索 + AI 评分
            async def run_retrieval_and_eval():
                retriever = get_hybrid_retriever()
                docs = await retriever.retrieve(question, top_k=top_k, filters=filters)
                
                # AI 评分
                scores = await self._evaluate_candidates(question, docs)
                
                return docs, scores

            # 并行等待
            answer, (docs, scores) = await asyncio.gather(run_agent(), run_retrieval_and_eval())
            
            # 组装结果
            structured_sources = []
            for doc in docs:
                doc_id = doc.metadata.get("id")
                
                # 获取 AI 评分
                ai_result = scores.get(doc_id, {})
                # 优先使用 AI 评分，归一化到 0-1
                similarity_score = ai_result.get("score", 0) / 100.0
                ai_reason = ai_result.get("reason", "")
                
                # 如果 AI 评分失败（为0），兜底使用向量距离
                if similarity_score == 0:
                     dist = doc.metadata.get("distance", 2.0)
                     similarity_score = max(0.0, 1.0 - dist / 2.0)

                # 更新 metadata
                doc.metadata["similarity_score"] = similarity_score
                doc.metadata["ai_reason"] = ai_reason

                structured_sources.append({
                    "id": doc_id,
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": doc.metadata.get("distance"),
                    "similarity_score": similarity_score,
                    "ai_reason": ai_reason
                })

            elapsed_time = int((time.time() - start_time) * 1000)
            logger.info(f"Agentic RAG 查询完成: elapsed_time={elapsed_time}ms")

            return {
                "answer": answer,
                "sources": structured_sources,
                "elapsed_time_ms": elapsed_time,
            }

        except Exception as e:
            logger.exception(f"RAG 查询失败: {e}")
            raise LLMException(
                message=f"RAG 查询失败: {e}",
                provider="agentic_rag",
                model="unknown",
                details={"error": str(e)},
            ) from e

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """仅执行向量检索（兼容旧接口）。"""
        retriever = get_hybrid_retriever()
        docs = await retriever.retrieve(query, top_k=top_k, filters=filters)
        
        return [
            {
                "id": doc.metadata.get("id"),
                "content": doc.page_content,
                "metadata": doc.metadata,
                "distance": doc.metadata.get("distance"),
            }
            for doc in docs
        ]


# 单例实例
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例实例。"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
