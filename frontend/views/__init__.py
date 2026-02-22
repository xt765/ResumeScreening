"""Streamlit 页面模块。

包含各功能页面的实现。
"""

from frontend.views.analysis import render_analysis_page
from frontend.views.conditions import render_conditions_page
from frontend.views.resume_upload import render_resume_upload_page
from frontend.views.talent_query import render_talent_query_page

__all__ = [
    "render_analysis_page",
    "render_conditions_page",
    "render_resume_upload_page",
    "render_talent_query_page",
]
