"""人才信息查询页面。

提供人才信息的搜索、浏览和详情查看功能。
"""

import asyncio
from typing import Any

import pandas as pd
import streamlit as st

from frontend.components import (
    APIError,
    create_tag_html,
    get_talent_api,
)


async def fetch_talents(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    screening_status: str | None = None,
) -> dict[str, Any]:
    """获取人才列表。

    Args:
        page: 页码
        page_size: 每页数量
        keyword: 搜索关键词
        screening_status: 筛选状态

    Returns:
        人才数据
    """
    try:
        api = get_talent_api()
        result = await api.list(
            page=page,
            page_size=page_size,
            keyword=keyword,
            screening_status=screening_status,
        )
        if result.get("success"):
            return result.get("data", {})
    except APIError as e:
        st.error(e.message)
    except Exception as e:
        st.error(f"获取数据失败: {e}")
    return {}


async def fetch_talent_detail(talent_id: int) -> dict[str, Any] | None:
    """获取人才详情。

    Args:
        talent_id: 人才 ID

    Returns:
        人才详情
    """
    try:
        api = get_talent_api()
        result = await api.get(talent_id)
        if result.get("success"):
            return result.get("data", {})
    except Exception:
        pass
    return None


def render_search_section() -> dict[str, Any]:
    """渲染搜索区域。

    Returns:
        搜索参数
    """
    st.markdown("### 搜索条件")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        keyword = st.text_input(
            "关键词",
            placeholder="姓名、学校、专业...",
            key="talent_keyword",
            label_visibility="collapsed",
        )

    with col2:
        status_options = {"全部": None, "合格": "qualified", "不合格": "disqualified"}
        status_label = st.selectbox(
            "筛选状态",
            options=list(status_options.keys()),
            key="talent_status",
            label_visibility="collapsed",
        )
        screening_status = status_options.get(status_label)

    with col3:
        page_size = st.selectbox(
            "每页显示",
            options=[10, 20, 50],
            index=0,
            key="talent_page_size",
            label_visibility="collapsed",
        )

    return {
        "keyword": keyword if keyword else None,
        "screening_status": screening_status,
        "page_size": page_size,
    }


def render_talent_table(talents: list[dict[str, Any]]) -> None:
    """渲染人才表格。

    Args:
        talents: 人才列表
    """
    if not talents:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div>暂无数据</div>
                <div style="font-size: 14px; margin-top: 8px;">调整搜索条件或上传简历</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # 构建表格数据
    table_data = []
    for t in talents:
        status = t.get("screening_status", "")
        status_text = "合格" if status == "qualified" else "不合格"

        table_data.append(
            {
                "ID": t.get("id"),
                "姓名": t.get("name", "-"),
                "学历": t.get("education", "-"),
                "学校": t.get("school", "-"),
                "专业": t.get("major", "-"),
                "状态": status_text,
            }
        )

    df = pd.DataFrame(table_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "姓名": st.column_config.TextColumn("姓名", width="medium"),
            "学历": st.column_config.TextColumn("学历", width="small"),
            "学校": st.column_config.TextColumn("学校", width="medium"),
            "专业": st.column_config.TextColumn("专业", width="medium"),
            "状态": st.column_config.TextColumn("状态", width="small"),
        },
    )

    # 选择查看详情
    selected_id = st.selectbox(
        "选择人才查看详情",
        options=[t.get("id") for t in talents],
        format_func=lambda x: next(
            (t.get("name", str(x)) for t in talents if t.get("id") == x), str(x)
        ),
        key="talent_select",
    )

    if selected_id:
        st.session_state.selected_talent_id = selected_id


def render_talent_detail(talent: dict[str, Any]) -> None:
    """渲染人才详情。

    Args:
        talent: 人才详情数据
    """
    if not talent:
        return

    name = talent.get("name", "未知")
    email = talent.get("email", "-")
    phone = talent.get("phone", "-")
    education = talent.get("education", "-")
    school = talent.get("school", "-")
    major = talent.get("major", "-")
    skills = talent.get("skills", [])
    screening_status = talent.get("screening_status", "")
    screening_reason = talent.get("screening_reason", "")

    # 状态
    is_qualified = screening_status == "qualified"
    status_text = "合格" if is_qualified else "不合格"
    status_tag = create_tag_html(
        status_text,
        "success" if is_qualified else "danger",
    )

    st.markdown("### 人才详情")

    st.markdown(
        f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div style="font-size: 18px; font-weight: 600; color: #303133;">{name}</div>
                {status_tag}
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; color: #606266; font-size: 14px;">
                <div><span style="color: #909399;">邮箱：</span>{email}</div>
                <div><span style="color: #909399;">电话：</span>{phone}</div>
                <div><span style="color: #909399;">学历：</span>{education}</div>
                <div><span style="color: #909399;">学校：</span>{school}</div>
                <div><span style="color: #909399;">专业：</span>{major}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 技能标签
    if skills:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-header">技能标签</div>
                <div>{"".join([create_tag_html(s, "primary") for s in skills])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 筛选说明
    if screening_reason:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-header">筛选说明</div>
                <div style="color: #606266; font-size: 14px;">{screening_reason}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_talent_query_page() -> None:
    """渲染人才信息查询页面。"""
    # 搜索区域
    search_params = render_search_section()

    # 分页控制
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1
        page = st.session_state.current_page

    # 获取数据
    with st.spinner("加载中..."):
        data = asyncio.run(
            fetch_talents(
                page=page,
                page_size=search_params["page_size"],
                keyword=search_params["keyword"],
                screening_status=search_params["screening_status"],
            )
        )

    talents = data.get("items", [])
    total = data.get("total", 0)
    total_pages = data.get("total_pages", 1)

    # 分页信息
    st.markdown(
        f"<div style='color: #909399; font-size: 14px; margin: 8px 0;'>共 {total} 条记录，第 {page}/{total_pages} 页</div>",
        unsafe_allow_html=True,
    )

    # 人才列表
    render_talent_table(talents)

    # 分页按钮
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])

    with col1:
        if st.button("上一页", disabled=page <= 1, key="prev_page"):
            st.session_state.current_page = page - 1
            st.rerun()

    with col2:
        if st.button("下一页", disabled=page >= total_pages, key="next_page"):
            st.session_state.current_page = page + 1
            st.rerun()

    # 人才详情
    if st.session_state.get("selected_talent_id"):
        talent = asyncio.run(fetch_talent_detail(st.session_state.selected_talent_id))
        if talent:
            render_talent_detail(talent)
