"""简历上传筛选页面。

提供简历上传和智能筛选功能。
"""

import asyncio
from typing import Any

import streamlit as st

from frontend.components import (
    APIError,
    create_tag_html,
    get_condition_api,
    get_talent_api,
)


async def fetch_active_conditions() -> list[dict[str, Any]]:
    """获取启用的筛选条件列表。

    Returns:
        筛选条件列表
    """
    try:
        api = get_condition_api()
        result = await api.list(page=1, page_size=100, is_active=True)
        if result.get("success"):
            return result.get("data", {}).get("items", [])
    except Exception:
        pass
    return []


async def upload_and_screen(file_bytes: bytes, filename: str, condition_id: int) -> dict[str, Any]:
    """上传简历并执行筛选。

    Args:
        file_bytes: 文件字节
        filename: 文件名
        condition_id: 筛选条件 ID

    Returns:
        筛选结果
    """
    try:
        api = get_talent_api()
        result = await api.upload_screen(file_bytes, filename, condition_id)
        return result
    except APIError as e:
        return {"success": False, "message": e.message}
    except Exception as e:
        return {"success": False, "message": str(e)}


def render_upload_section(conditions: list[dict[str, Any]]) -> None:
    """渲染上传区域。

    Args:
        conditions: 筛选条件列表
    """
    st.markdown("### 上传简历")

    if not conditions:
        st.warning("暂无可用的筛选条件，请先创建筛选条件")
        return

    # 选择筛选条件
    condition_options = {c.get("name"): c.get("id") for c in conditions}
    selected_name = st.selectbox(
        "选择筛选条件",
        options=list(condition_options.keys()),
        key="upload_condition_select",
    )
    condition_id = condition_options.get(selected_name)

    # 文件上传
    uploaded_file = st.file_uploader(
        "选择简历文件",
        type=["pdf", "docx"],
        help="支持 PDF 和 DOCX 格式",
        key="resume_uploader",
    )

    if uploaded_file and condition_id:
        if st.button("开始筛选", key="start_screen_btn", type="primary"):
            with st.spinner("正在解析简历并执行筛选..."):
                file_bytes = uploaded_file.read()
                result = asyncio.run(
                    upload_and_screen(file_bytes, uploaded_file.name, condition_id)
                )

                if result.get("success"):
                    st.session_state.screen_result = result.get("data", {})
                    st.success("筛选完成")
                    st.rerun()
                else:
                    st.error(result.get("message", "筛选失败"))


def render_result_section() -> None:
    """渲染筛选结果。"""
    result = st.session_state.get("screen_result")

    if not result:
        return

    st.markdown("### 筛选结果")

    # 基本信息
    name = result.get("name", "")
    email = result.get("email", "")
    phone = result.get("phone", "")
    education = result.get("education", "")
    school = result.get("school", "")
    major = result.get("major", "")
    skills = result.get("skills", [])
    screening_status = result.get("screening_status", "")
    screening_reason = result.get("screening_reason", "")

    # 状态
    is_qualified = screening_status == "qualified"
    status_text = "合格" if is_qualified else "不合格"
    status_tag = create_tag_html(
        status_text,
        "success" if is_qualified else "danger",
    )

    st.markdown(
        f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div style="font-size: 18px; font-weight: 600; color: #303133;">{name or "未知"}</div>
                {status_tag}
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; color: #606266; font-size: 14px;">
                <div><span style="color: #909399;">邮箱：</span>{email or "-"}</div>
                <div><span style="color: #909399;">电话：</span>{phone or "-"}</div>
                <div><span style="color: #909399;">学历：</span>{education or "-"}</div>
                <div><span style="color: #909399;">学校：</span>{school or "-"}</div>
                <div><span style="color: #909399;">专业：</span>{major or "-"}</div>
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

    # 筛选原因
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

    # 清除结果按钮
    if st.button("继续上传", key="clear_result_btn"):
        st.session_state.screen_result = None
        st.rerun()


def render_resume_upload_page() -> None:
    """渲染简历上传筛选页面。"""
    # 获取筛选条件
    conditions = asyncio.run(fetch_active_conditions())

    # 两列布局
    col1, col2 = st.columns([2, 1])

    with col1:
        # 显示结果或上传区域
        if st.session_state.get("screen_result"):
            render_result_section()
        else:
            render_upload_section(conditions)

    with col2:
        # 使用说明
        st.markdown(
            """
            <div class="card">
                <div class="card-header">使用说明</div>
                <div style="color: #606266; font-size: 14px; line-height: 1.8;">
                    <p>1. 选择筛选条件</p>
                    <p>2. 上传简历文件（PDF/DOCX）</p>
                    <p>3. 点击「开始筛选」按钮</p>
                    <p>4. 查看筛选结果</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 可用条件数量
        st.markdown(
            f"""
            <div class="card">
                <div class="card-header">统计信息</div>
                <div style="color: #606266; font-size: 14px;">
                    <p>可用筛选条件：<strong>{len(conditions)}</strong> 个</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
