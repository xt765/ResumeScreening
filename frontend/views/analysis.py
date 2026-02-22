"""数据分析页面。

提供 RAG 智能查询、统计分析和数据导出功能。
"""

import asyncio
import json
from typing import Any

import streamlit as st

from frontend.components import (
    APIError,
    create_tag_html,
    get_analysis_api,
    get_talent_api,
)


async def fetch_statistics() -> dict[str, Any]:
    """获取统计数据。

    Returns:
        统计数据
    """
    try:
        api = get_analysis_api()
        result = await api.statistics()
        if result.get("success"):
            return result.get("data", {})
    except Exception:
        pass
    return {}


async def fetch_all_talents_for_analysis(limit: int = 100) -> list[dict[str, Any]]:
    """获取所有人才数据用于分析。

    Args:
        limit: 最大数量（最大 100）

    Returns:
        人才列表
    """
    try:
        api = get_talent_api()
        actual_limit = min(limit, 100)
        result = await api.list(page=1, page_size=actual_limit)
        if result.get("success"):
            return result.get("data", {}).get("items", [])
    except APIError as e:
        st.error(f"获取人才数据失败: {e.message}")
    except Exception as e:
        st.error(f"获取人才数据失败: {e}")
    return []


async def rag_query(question: str) -> dict[str, Any]:
    """执行 RAG 查询。

    Args:
        question: 查询问题

    Returns:
        查询结果
    """
    try:
        api = get_analysis_api()
        result = await api.query(question)
        if result.get("success"):
            return result.get("data", {})
    except APIError as e:
        return {"error": e.message}
    except Exception as e:
        return {"error": str(e)}
    return {}


def render_rag_query_section() -> None:
    """渲染 RAG 查询区域。"""
    st.markdown("#### 智能查询")

    question = st.text_input(
        "输入问题",
        placeholder="例如：有多少候选人符合条件？本科学历的有多少人？",
        key="rag_question",
        label_visibility="collapsed",
    )

    if st.button("查询", key="rag_query_btn", type="primary"):
        if question:
            with st.spinner("正在查询..."):
                result = asyncio.run(rag_query(question))

                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.rag_result = result
                    st.rerun()
        else:
            st.warning("请输入问题")

    # 显示结果
    if st.session_state.get("rag_result"):
        result = st.session_state.rag_result
        answer = result.get("answer", "")
        sources = result.get("sources", [])

        st.markdown(
            f"""
            <div class="card">
                <div class="card-header">查询结果</div>
                <div style="color: #303133; font-size: 14px; line-height: 1.8;">{answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if sources:
            st.markdown(
                f"""
                <div class="card">
                    <div class="card-header">相关人才</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        {"".join([create_tag_html(s.get("name", "未知"), "primary") for s in sources[:10]])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_statistics_section(stats: dict[str, Any], talents: list[dict[str, Any]]) -> None:
    """渲染统计分析区域。

    Args:
        stats: 统计数据
        talents: 人才列表
    """
    st.markdown("#### 统计分析")

    # 基础统计
    total = stats.get("total_talents", 0)
    by_status = stats.get("by_screening_status", {})
    qualified = by_status.get("qualified", 0)
    disqualified = by_status.get("disqualified", 0)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">人才总数</div>
                <div class="stat-value">{total:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">合格人数</div>
                <div class="stat-value" style="color: #67c23a;">{qualified:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">不合格人数</div>
                <div class="stat-value" style="color: #f56c6c;">{disqualified:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 学历分布
    if talents:
        st.markdown("#### 学历分布")

        education_count: dict[str, int] = {}
        for t in talents:
            edu = t.get("education", "未知")
            education_count[edu] = education_count.get(edu, 0) + 1

        edu_data = sorted(education_count.items(), key=lambda x: x[1], reverse=True)

        for edu, count in edu_data:
            percentage = (count / len(talents) * 100) if talents else 0
            bar_width = int(percentage)

            st.markdown(
                f"""
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #303133; font-size: 14px;">{edu}</span>
                        <span style="color: #909399; font-size: 14px;">{count} ({percentage:.1f}%)</span>
                    </div>
                    <div style="background-color: #f0f0f0; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background-color: #3370ff; width: {bar_width}%; height: 100%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_data_export_section(talents: list[dict[str, Any]]) -> None:
    """渲染数据导出区域。

    Args:
        talents: 人才列表
    """
    st.markdown("#### 数据导出")

    if not talents:
        st.info("暂无数据可导出")
        return

    # 导出格式选择
    export_format = st.radio(
        "导出格式",
        options=["CSV", "JSON"],
        horizontal=True,
        key="export_format",
    )

    # 导出字段选择
    st.markdown("**导出字段**")

    col1, col2, col3 = st.columns(3)

    with col1:
        export_name = st.checkbox("姓名", value=True, key="export_name")
        export_email = st.checkbox("邮箱", value=True, key="export_email")
        export_phone = st.checkbox("电话", value=True, key="export_phone")

    with col2:
        export_education = st.checkbox("学历", value=True, key="export_education")
        export_school = st.checkbox("学校", value=True, key="export_school")
        export_major = st.checkbox("专业", value=True, key="export_major")

    with col3:
        export_status = st.checkbox("筛选状态", value=True, key="export_status")
        export_skills = st.checkbox("技能", value=True, key="export_skills")

    if st.button("导出", key="export_btn", type="primary"):
        # 构建导出数据
        export_data = []
        for t in talents:
            row = {}
            if export_name:
                row["姓名"] = t.get("name", "")
            if export_email:
                row["邮箱"] = t.get("email", "")
            if export_phone:
                row["电话"] = t.get("phone", "")
            if export_education:
                row["学历"] = t.get("education", "")
            if export_school:
                row["学校"] = t.get("school", "")
            if export_major:
                row["专业"] = t.get("major", "")
            if export_status:
                status = t.get("screening_status", "")
                row["筛选状态"] = "合格" if status == "qualified" else "不合格"
            if export_skills:
                row["技能"] = ", ".join(t.get("skills", []))
            export_data.append(row)

        if export_format == "CSV":
            import csv
            from io import StringIO

            output = StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)

            st.download_button(
                "下载 CSV",
                output.getvalue(),
                file_name="talents_export.csv",
                mime="text/csv",
                key="download_csv",
            )
        else:
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(
                "下载 JSON",
                json_str,
                file_name="talents_export.json",
                mime="application/json",
                key="download_json",
            )


def render_analysis_page() -> None:
    """渲染数据分析页面。"""
    # 初始化 session state
    if "rag_result" not in st.session_state:
        st.session_state.rag_result = None

    # 获取数据
    with st.spinner("加载数据..."):
        stats = asyncio.run(fetch_statistics())
        talents = asyncio.run(fetch_all_talents_for_analysis(limit=100))

    if not stats:
        st.error("无法加载统计数据，请检查 API 服务是否正常运行。")
        return

    # 标签页
    tab1, tab2, tab3 = st.tabs(["智能查询", "统计分析", "数据导出"])

    with tab1:
        render_rag_query_section()

    with tab2:
        render_statistics_section(stats, talents)

    with tab3:
        render_data_export_section(talents)
