"""筛选条件管理页面。

提供筛选条件的创建、编辑、删除和查询功能。
"""

import asyncio

import streamlit as st

from frontend.components import (
    APIError,
    create_tag_html,
    get_condition_api,
)


def render_conditions_list() -> None:
    """渲染筛选条件列表。"""
    # 搜索和筛选
    col1, col2 = st.columns([3, 1])

    with col1:
        search_keyword = st.text_input(
            "搜索条件名称",
            placeholder="输入条件名称搜索...",
            key="condition_search",
            label_visibility="collapsed",
        )

    with col2:
        page_size = st.selectbox(
            "每页显示",
            options=[10, 20, 50],
            index=0,
            key="condition_page_size",
            label_visibility="collapsed",
        )

    # 获取数据
    async def fetch_conditions():
        try:
            api = get_condition_api()
            result = await api.list(
                page=1,
                page_size=page_size,
                keyword=search_keyword if search_keyword else None,
            )
            if result.get("success"):
                return result.get("data", {})
        except APIError as e:
            st.error(e.message)
        except Exception as e:
            st.error(f"获取数据失败: {e}")
        return {}

    data = asyncio.run(fetch_conditions())
    conditions = data.get("items", [])
    total = data.get("total", 0)

    # 新增按钮
    if st.button("新增条件", key="add_condition_btn", type="primary"):
        st.session_state.show_condition_form = True
        st.session_state.editing_condition = None
        st.rerun()

    st.markdown(f"<div style='color: #909399; font-size: 14px; margin: 8px 0;'>共 {total} 条记录</div>", unsafe_allow_html=True)

    # 条件列表
    if conditions:
        for condition in conditions:
            condition_id = condition.get("id")
            name = condition.get("name", "")
            education = condition.get("education_requirement", "")
            skills = condition.get("skill_requirements", [])
            majors = condition.get("major_requirements", [])
            is_active = condition.get("is_active", True)

            # 状态标签
            status_tag = create_tag_html(
                "启用" if is_active else "禁用",
                "success" if is_active else "info",
            )

            with st.container():
                st.markdown(
                    f"""
                    <div class="card" style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-weight: 600; color: #303133;">{name}</div>
                            {status_tag}
                        </div>
                        <div style="margin-top: 12px; color: #606266; font-size: 14px;">
                            <div style="margin-bottom: 8px;">
                                <span style="color: #909399;">学历要求：</span>
                                <span>{education or "不限"}</span>
                            </div>
                            <div style="margin-bottom: 8px;">
                                <span style="color: #909399;">技能要求：</span>
                                {"".join([create_tag_html(s, "primary") for s in skills]) if skills else "<span>不限</span>"}
                            </div>
                            <div>
                                <span style="color: #909399;">专业要求：</span>
                                {"".join([create_tag_html(m, "warning") for m in majors]) if majors else "<span>不限</span>"}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # 操作按钮
                col1, col2, col3 = st.columns([1, 1, 4])

                with col1:
                    if st.button("编辑", key=f"edit_{condition_id}"):
                        st.session_state.show_condition_form = True
                        st.session_state.editing_condition = condition
                        st.rerun()

                with col2:
                    if st.button("删除", key=f"delete_{condition_id}"):
                        st.session_state.delete_condition_id = condition_id
                        st.rerun()
    else:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <div>暂无筛选条件</div>
                <div style="font-size: 14px; margin-top: 8px;">点击「新增条件」创建第一个筛选条件</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_condition_form() -> None:
    """渲染筛选条件表单。"""
    editing = st.session_state.get("editing_condition")
    is_edit = editing is not None

    st.markdown(f"### {'编辑' if is_edit else '新增'}筛选条件")

    with st.form("condition_form", clear_on_submit=True):
        # 基本信息
        name = st.text_input(
            "条件名称",
            value=editing.get("name", "") if is_edit else "",
            placeholder="请输入条件名称",
        )

        # 学历要求
        education_options = ["", "博士", "硕士", "本科", "大专", "高中"]
        education = st.selectbox(
            "学历要求",
            options=education_options,
            index=education_options.index(editing.get("education_requirement", "")) if is_edit and editing.get("education_requirement") in education_options else 0,
        )

        # 技能要求
        skills_text = st.text_area(
            "技能要求",
            value="\n".join(editing.get("skill_requirements", [])) if is_edit else "",
            placeholder="每行一个技能，例如：\nPython\nJava\nMySQL",
            height=100,
        )

        # 专业要求
        majors_text = st.text_area(
            "专业要求",
            value="\n".join(editing.get("major_requirements", [])) if is_edit else "",
            placeholder="每行一个专业，例如：\n计算机科学\n软件工程",
            height=100,
        )

        # 是否启用
        is_active = st.checkbox(
            "启用此条件",
            value=editing.get("is_active", True) if is_edit else True,
        )

        # 提交按钮
        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("保存", type="primary", use_container_width=True)

        with col2:
            cancelled = st.form_submit_button("取消", use_container_width=True)

        if cancelled:
            st.session_state.show_condition_form = False
            st.session_state.editing_condition = None
            st.rerun()

        if submitted:
            if not name:
                st.error("请输入条件名称")
            else:
                skills = [s.strip() for s in skills_text.split("\n") if s.strip()]
                majors = [m.strip() for m in majors_text.split("\n") if m.strip()]

                async def save_condition():
                    try:
                        api = get_condition_api()
                        data = {
                            "name": name,
                            "education_requirement": education if education else None,
                            "skill_requirements": skills if skills else None,
                            "major_requirements": majors if majors else None,
                            "is_active": is_active,
                        }

                        if is_edit:
                            result = await api.update(editing.get("id"), data)
                        else:
                            result = await api.create(data)

                        if result.get("success"):
                            return True, "保存成功"
                        return False, result.get("message", "保存失败")
                    except APIError as e:
                        return False, e.message
                    except Exception as e:
                        return False, str(e)

                success, message = asyncio.run(save_condition())
                if success:
                    st.success(message)
                    st.session_state.show_condition_form = False
                    st.session_state.editing_condition = None
                    st.rerun()
                else:
                    st.error(message)


def render_delete_confirm() -> None:
    """渲染删除确认对话框。"""
    condition_id = st.session_state.get("delete_condition_id")

    if condition_id:
        st.warning("确定要删除此筛选条件吗？")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("确认删除", key="confirm_delete", type="primary"):
                async def delete_condition():
                    try:
                        api = get_condition_api()
                        result = await api.delete(condition_id)
                        return result.get("success", False)
                    except Exception:
                        return False

                if asyncio.run(delete_condition()):
                    st.success("删除成功")
                else:
                    st.error("删除失败")
                st.session_state.delete_condition_id = None
                st.rerun()

        with col2:
            if st.button("取消", key="cancel_delete"):
                st.session_state.delete_condition_id = None
                st.rerun()


def render_conditions_page() -> None:
    """渲染筛选条件管理页面。"""
    # 初始化状态
    if "show_condition_form" not in st.session_state:
        st.session_state.show_condition_form = False

    # 显示表单或列表
    if st.session_state.get("show_condition_form"):
        render_condition_form()
    elif st.session_state.get("delete_condition_id"):
        render_delete_confirm()
    else:
        render_conditions_list()
