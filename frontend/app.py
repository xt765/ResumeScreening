"""Streamlit 主应用入口。

提供页面导航和主页面渲染功能。
"""

import asyncio

import streamlit as st

from frontend.components import (
    get_api_client,
    get_custom_css,
    get_theme,
)


def render_sidebar() -> None:
    """渲染侧边栏导航。"""
    theme = get_theme("light")

    # 系统标题
    st.markdown(
        f"""
        <div style="
            padding: 16px 0;
            border-bottom: 1px solid {theme.border};
            margin-bottom: 16px;
        ">
            <div style="font-size: 18px; font-weight: 600; color: {theme.text};">
                简历筛选系统
            </div>
            <div style="font-size: 13px; color: {theme.text_secondary}; margin-top: 4px;">
                智能筛选 · 精准匹配
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 导航菜单
    nav_items = [
        ("首页", "home"),
        ("筛选条件", "conditions"),
        ("简历上传", "upload"),
        ("人才查询", "query"),
        ("数据分析", "analysis"),
    ]

    for label, key in nav_items:
        is_active = st.session_state.get("page", "首页") == label
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{key}", type=btn_type, use_container_width=True):
            st.session_state.page = label
            st.rerun()


def render_home_page() -> None:
    """渲染首页内容。"""
    # 获取统计数据
    async def fetch_stats():
        try:
            client = get_api_client()
            result = await client.get("/api/v1/analysis/statistics")
            if result.get("success"):
                return result.get("data", {})
        except Exception:
            pass
        return {}

    stats = asyncio.run(fetch_stats())

    # 统计数据
    total = stats.get("total_talents", 0)
    by_status = stats.get("by_screening_status", {})
    qualified = by_status.get("qualified", 0)
    disqualified = by_status.get("disqualified", 0)
    recent_7_days = stats.get("recent_7_days", 0)
    pass_rate = (qualified / total * 100) if total > 0 else 0

    # 页面标题
    st.markdown("### 概览")

    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)

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
                <div style="font-size: 12px; color: #909399;">通过率 {pass_rate:.1f}%</div>
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

    with col4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">近 7 天新增</div>
                <div class="stat-value" style="color: #e6a23c;">{recent_7_days:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 快捷操作
    st.markdown("### 快捷操作")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("筛选条件", key="quick_conditions", use_container_width=True):
            st.session_state.page = "筛选条件"
            st.rerun()

    with col2:
        if st.button("上传简历", key="quick_upload", use_container_width=True):
            st.session_state.page = "简历上传"
            st.rerun()

    with col3:
        if st.button("人才查询", key="quick_query", use_container_width=True):
            st.session_state.page = "人才查询"
            st.rerun()

    with col4:
        if st.button("数据分析", key="quick_analysis", use_container_width=True):
            st.session_state.page = "数据分析"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 功能说明
    st.markdown("### 功能说明")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="card">
                <div class="card-header">筛选条件管理</div>
                <p style="color: #909399; font-size: 14px; margin: 0;">
                    配置学历、技能、专业等筛选条件，支持多条件组合筛选。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="card">
                <div class="card-header">简历上传筛选</div>
                <p style="color: #909399; font-size: 14px; margin: 0;">
                    支持 PDF/DOCX 格式简历上传，自动解析并执行智能筛选。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="card">
                <div class="card-header">人才信息查询</div>
                <p style="color: #909399; font-size: 14px; margin: 0;">
                    多条件组合查询人才信息，支持分页浏览和详情查看。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="card">
                <div class="card-header">数据分析</div>
                <p style="color: #909399; font-size: 14px; margin: 0;">
                    RAG 智能问答、多维度统计分析、可视化图表展示。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    """主函数。"""
    # 页面配置
    st.set_page_config(
        page_title="简历筛选系统",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 加载自定义样式
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # 初始化页面状态
    if "page" not in st.session_state:
        st.session_state.page = "首页"

    # 渲染侧边栏
    with st.sidebar:
        render_sidebar()

    # 根据页面状态渲染内容
    page = st.session_state.page

    if page == "首页":
        render_home_page()
    elif page == "筛选条件":
        from frontend.views.conditions import render_conditions_page

        render_conditions_page()
    elif page == "简历上传":
        from frontend.views.resume_upload import render_resume_upload_page

        render_resume_upload_page()
    elif page == "人才查询":
        from frontend.views.talent_query import render_talent_query_page

        render_talent_query_page()
    elif page == "数据分析":
        from frontend.views.analysis import render_analysis_page

        render_analysis_page()


if __name__ == "__main__":
    main()
