"""现代化主题配置模块。

提供统一的主题配置、颜色方案和自定义 CSS 样式。
采用简洁专业的设计风格。
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ColorScheme:
    """颜色方案配置类。

    定义应用的整体颜色风格，支持亮色和暗色主题。

    Attributes:
        name: 主题名称
        primary: 主色调
        primary_light: 主色调浅色
        primary_bg: 主色调背景
        success: 成功状态颜色
        warning: 警告状态颜色
        danger: 危险/错误状态颜色
        info: 信息状态颜色
        background: 背景色
        surface: 表面色（卡片等）
        text: 文本颜色
        text_secondary: 次要文本颜色
        border: 边框颜色
    """

    name: str
    primary: str
    primary_light: str
    primary_bg: str
    success: str
    warning: str
    danger: str
    info: str
    background: str
    surface: str
    text: str
    text_secondary: str
    border: str


# 亮色主题配置 - 简洁专业风格
LIGHT_THEME = ColorScheme(
    name="light",
    primary="#3370ff",
    primary_light="#e6f0ff",
    primary_bg="#f2f6fc",
    success="#67c23a",
    warning="#e6a23c",
    danger="#f56c6c",
    info="#909399",
    background="#f5f5f5",
    surface="#ffffff",
    text="#303133",
    text_secondary="#909399",
    border="#dcdfe6",
)

# 暗色主题配置
DARK_THEME = ColorScheme(
    name="dark",
    primary="#409eff",
    primary_light="#1a3a5c",
    primary_bg="#1a1a1a",
    success="#67c23a",
    warning="#e6a23c",
    danger="#f56c6c",
    info="#909399",
    background="#141414",
    surface="#1f1f1f",
    text="#e5eaf3",
    text_secondary="#a3a6ad",
    border="#4c4d4f",
)

# 图表专用颜色
CHART_COLORS = {
    "primary": "#3370ff",
    "secondary": "#67c23a",
    "tertiary": "#e6a23c",
    "success": "#67c23a",
    "warning": "#e6a23c",
    "danger": "#f56c6c",
    "info": "#909399",
    "cyan": "#06b6d4",
    "teal": "#14b8a6",
    "indigo": "#3370ff",
}

# 学历颜色映射
EDUCATION_COLORS = {
    "doctor": "#3370ff",
    "master": "#67c23a",
    "bachelor": "#e6a23c",
    "college": "#909399",
    "high_school": "#f56c6c",
}

# 筛选状态颜色映射
STATUS_COLORS = {
    "qualified": "#67c23a",
    "disqualified": "#f56c6c",
    "pending": "#e6a23c",
}


def get_theme(mode: Literal["light", "dark"] = "light") -> ColorScheme:
    """获取主题配置。

    Args:
        mode: 主题模式，'light' 或 'dark'

    Returns:
        颜色方案配置对象
    """
    return LIGHT_THEME if mode == "light" else DARK_THEME


def get_custom_css(theme: ColorScheme | None = None) -> str:
    """获取自定义 CSS 样式。

    Args:
        theme: 颜色方案，默认使用亮色主题

    Returns:
        CSS 样式字符串
    """
    if theme is None:
        theme = LIGHT_THEME

    return f"""
    <style>
        /* 隐藏 Streamlit 默认元素 */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        [data-testid="stStatusWidget"],
        .stDeployButton,
        button[kind="header"] {{
            display: none !important;
        }}
        header[data-testid="stHeader"] {{
            display: none !important;
        }}

        /* 全局样式 */
        .main {{
            background-color: {theme.background};
            padding: 16px;
        }}

        /* 侧边栏样式 */
        [data-testid="stSidebar"] {{
            background-color: {theme.surface} !important;
            border-right: 1px solid {theme.border};
        }}

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            color: {theme.text_secondary};
        }}

        /* 卡片样式 */
        .card {{
            background-color: {theme.surface};
            border-radius: 8px;
            padding: 20px;
            border: 1px solid {theme.border};
            margin-bottom: 16px;
        }}

        .card-header {{
            font-size: 16px;
            font-weight: 600;
            color: {theme.text};
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid {theme.border};
        }}

        /* 统计卡片 */
        .stat-card {{
            background-color: {theme.surface};
            border-radius: 8px;
            padding: 20px;
            border: 1px solid {theme.border};
            text-align: center;
        }}

        .stat-card .stat-value {{
            font-size: 32px;
            font-weight: 600;
            color: {theme.primary};
            margin: 8px 0;
        }}

        .stat-card .stat-label {{
            font-size: 14px;
            color: {theme.text_secondary};
        }}

        /* 按钮样式 */
        .stButton > button {{
            border-radius: 6px;
            font-weight: 500;
            border: 1px solid {theme.border};
            background-color: {theme.surface};
            color: {theme.text};
            padding: 8px 16px;
            transition: all 0.2s;
        }}

        .stButton > button:hover {{
            border-color: {theme.primary};
            color: {theme.primary};
        }}

        .stButton > button[kind="primary"] {{
            background-color: {theme.primary};
            border-color: {theme.primary};
            color: white;
        }}

        .stButton > button[kind="primary"]:hover {{
            background-color: #5a8bff;
            border-color: #5a8bff;
        }}

        /* 输入框样式 */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            border-radius: 6px;
            border: 1px solid {theme.border};
            background-color: {theme.surface};
        }}

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {theme.primary};
            box-shadow: 0 0 0 2px {theme.primary_light};
        }}

        /* 表格样式 */
        .stDataFrame {{
            border-radius: 8px;
            border: 1px solid {theme.border};
            overflow: hidden;
        }}

        /* 标签页样式 */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            background-color: transparent;
            border-bottom: 1px solid {theme.border};
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 0;
            padding: 12px 20px;
            background-color: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            color: {theme.text_secondary};
            font-weight: 500;
        }}

        .stTabs [aria-selected="true"] {{
            color: {theme.primary};
            border-bottom-color: {theme.primary};
            background-color: transparent;
        }}

        /* 消息提示样式 */
        .stSuccess {{
            background-color: #f0f9eb;
            border: 1px solid #e1f3d8;
            border-radius: 6px;
            color: #67c23a;
        }}

        .stError {{
            background-color: #fef0f0;
            border: 1px solid #fde2e2;
            border-radius: 6px;
            color: #f56c6c;
        }}

        .stWarning {{
            background-color: #fdf6ec;
            border: 1px solid #faecd8;
            border-radius: 6px;
            color: #e6a23c;
        }}

        .stInfo {{
            background-color: #f4f4f5;
            border: 1px solid #e9e9eb;
            border-radius: 6px;
            color: #909399;
        }}

        /* 文件上传区域 */
        .stFileUploader {{
            background-color: {theme.surface};
            border-radius: 8px;
            padding: 16px;
            border: 1px dashed {theme.border};
        }}

        /* 标题样式 */
        h1 {{
            color: {theme.text};
            font-weight: 600;
            font-size: 22px;
            margin-bottom: 16px;
        }}

        h2, h3 {{
            color: {theme.text};
            font-weight: 600;
        }}

        h4 {{
            color: {theme.text};
            font-weight: 600;
            font-size: 16px;
        }}

        /* 分隔线 */
        hr {{
            border: none;
            height: 1px;
            background-color: {theme.border};
            margin: 16px 0;
        }}

        /* 滚动条样式 */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}

        ::-webkit-scrollbar-track {{
            background: {theme.background};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {theme.border};
            border-radius: 3px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {theme.text_secondary};
        }}

        /* 标签样式 */
        .tag {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            margin: 2px;
        }}

        .tag-primary {{
            background-color: {theme.primary_light};
            color: {theme.primary};
        }}

        .tag-success {{
            background-color: #f0f9eb;
            color: #67c23a;
        }}

        .tag-warning {{
            background-color: #fdf6ec;
            color: #e6a23c;
        }}

        .tag-danger {{
            background-color: #fef0f0;
            color: #f56c6c;
        }}

        .tag-info {{
            background-color: #f4f4f5;
            color: #909399;
        }}

        /* 空状态 */
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            color: {theme.text_secondary};
        }}

        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}

        /* 表单样式 */
        .stForm {{
            background-color: {theme.surface};
            border-radius: 8px;
            padding: 20px;
            border: 1px solid {theme.border};
        }}

        /* Expander 样式 */
        .streamlit-expanderHeader {{
            background-color: {theme.surface};
            border-radius: 6px;
            border: 1px solid {theme.border};
        }}

        /* 响应式调整 */
        @media (max-width: 768px) {{
            .stat-card .stat-value {{
                font-size: 24px;
            }}

            .card {{
                padding: 16px;
            }}
        }}
    </style>
    """


def create_stat_card_html(
    label: str,
    value: str | int,
    color: str = "#3370ff",
    subtitle: str = "",
) -> str:
    """创建统计卡片 HTML。

    Args:
        label: 标签文本
        value: 数值
        color: 数值颜色
        subtitle: 副标题文本

    Returns:
        HTML 字符串
    """
    subtitle_html = f'<div style="font-size: 12px; color: #909399; margin-top: 4px;">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="stat-card">
        <div class="stat-label">{label}</div>
        <div class="stat-value" style="color: {color};">{value}</div>
        {subtitle_html}
    </div>
    """


def create_card_html(content: str, title: str = "") -> str:
    """创建卡片 HTML。

    Args:
        content: 卡片内容
        title: 卡片标题

    Returns:
        HTML 字符串
    """
    title_html = f'<div class="card-header">{title}</div>' if title else ""
    return f"""
    <div class="card">
        {title_html}
        {content}
    </div>
    """


def create_tag_html(text: str, tag_type: str = "primary") -> str:
    """创建标签 HTML。

    Args:
        text: 标签文本
        tag_type: 标签类型 (primary, success, warning, danger, info)

    Returns:
        HTML 字符串
    """
    return f'<span class="tag tag-{tag_type}">{text}</span>'


__all__ = [
    "CHART_COLORS",
    "DARK_THEME",
    "EDUCATION_COLORS",
    "LIGHT_THEME",
    "STATUS_COLORS",
    "ColorScheme",
    "create_card_html",
    "create_stat_card_html",
    "create_tag_html",
    "get_custom_css",
    "get_theme",
]
