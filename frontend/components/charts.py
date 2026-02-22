"""Plotly 图表组件模块。

提供数据可视化图表组件，使用现代化配色方案和优雅的视觉风格。
"""

from typing import Any

import plotly.graph_objects as go

from frontend.components.theme import CHART_COLORS, EDUCATION_COLORS, STATUS_COLORS

# 图表布局默认配置
DEFAULT_LAYOUT = {
    "font": {"family": "system-ui, -apple-system, sans-serif", "size": 12},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": {"t": 60, "b": 40, "l": 40, "r": 20},
    "height": 400,
}

# 动画配置
ANIMATION_CONFIG = {"duration": 500, "easing": "cubic-in-out"}


def create_pie_chart(
    data: dict[str, int],
    title: str,
    colors: dict[str, str] | None = None,
    hole: float = 0.5,
) -> go.Figure:
    """创建现代化饼图。

    Args:
        data: 数据字典，键为标签，值为数值
        title: 图表标题
        colors: 颜色映射字典
        hole: 中心空洞比例（环形图）

    Returns:
        Plotly Figure 对象
    """
    labels = list(data.keys())
    values = list(data.values())

    # 获取颜色列表
    if colors:
        color_list = [colors.get(label, CHART_COLORS["primary"]) for label in labels]
    else:
        color_list = list(CHART_COLORS.values())[: len(labels)]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=hole,
                marker_colors=color_list,
                textinfo="label+percent",
                textposition="outside",
                textfont={"size": 12},
                marker={
                    "line": {"color": "white", "width": 2},
                    "colors": color_list,
                },
                hovertemplate="<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            "text": f"<b>{title}</b>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "color": "#1E293B"},
        },
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
        },
    )

    return fig


def create_bar_chart(
    data: dict[str, int],
    title: str,
    x_label: str = "",
    y_label: str = "数量",
    color: str = CHART_COLORS["primary"],
    horizontal: bool = False,
    show_values: bool = True,
) -> go.Figure:
    """创建现代化柱状图。

    Args:
        data: 数据字典，键为标签，值为数值
        title: 图表标题
        x_label: X 轴标签
        y_label: Y 轴标签
        color: 柱子颜色
        horizontal: 是否为水平柱状图
        show_values: 是否显示数值标签

    Returns:
        Plotly Figure 对象
    """
    labels = list(data.keys())
    values = list(data.values())

    if horizontal:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=values,
                    y=labels,
                    orientation="h",
                    marker={
                        "color": values,
                        "colorscale": [[0, color], [1, color]],
                        "line": {"color": "white", "width": 1},
                    },
                    text=values if show_values else None,
                    textposition="auto",
                    textfont={"size": 11},
                    hovertemplate="<b>%{y}</b><br>数量: %{x}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            xaxis_title=y_label,
            yaxis_title=x_label,
        )
    else:
        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=values,
                    marker={
                        "color": values,
                        "colorscale": [[0, color], [1, color]],
                        "line": {"color": "white", "width": 1},
                    },
                    text=values if show_values else None,
                    textposition="auto",
                    textfont={"size": 11},
                    hovertemplate="<b>%{x}</b><br>数量: %{y}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            xaxis_title=x_label,
            yaxis_title=y_label,
        )

    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            "text": f"<b>{title}</b>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "color": "#1E293B"},
        },
        xaxis={"showgrid": False, "showline": False},
        yaxis={"showgrid": True, "gridcolor": "#E2E8F0", "showline": False},
    )

    return fig


def create_line_chart(
    x_data: list[Any],
    y_data: list[int],
    title: str,
    x_label: str = "",
    y_label: str = "数量",
    color: str = CHART_COLORS["primary"],
    fill: bool = True,
) -> go.Figure:
    """创建现代化折线图。

    Args:
        x_data: X 轴数据
        y_data: Y 轴数据
        title: 图表标题
        x_label: X 轴标签
        y_label: Y 轴标签
        color: 线条颜色
        fill: 是否填充区域

    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_data,
            mode="lines+markers",
            line={"color": color, "width": 3},
            marker={"size": 8, "color": color, "line": {"color": "white", "width": 2}},
            fill="tozeroy" if fill else None,
            fillcolor=f"{color}20",
            hovertemplate="<b>%{x}</b><br>数量: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            "text": f"<b>{title}</b>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "color": "#1E293B"},
        },
        xaxis_title=x_label,
        yaxis_title=y_label,
        xaxis={"showgrid": False, "showline": False},
        yaxis={"showgrid": True, "gridcolor": "#E2E8F0", "showline": False},
    )

    return fig


def create_education_distribution_chart(data: dict[str, int]) -> go.Figure:
    """创建学历分布饼图。

    Args:
        data: 学历分布数据

    Returns:
        Plotly Figure 对象
    """
    # 学历中文映射
    education_labels = {
        "doctor": "博士",
        "master": "硕士",
        "bachelor": "本科",
        "college": "大专",
        "high_school": "高中及以下",
    }

    # 转换标签
    display_data = {education_labels.get(k, k): v for k, v in data.items()}

    # 对应颜色映射
    display_colors = {education_labels.get(k, k): v for k, v in EDUCATION_COLORS.items()}

    return create_pie_chart(display_data, "学历分布", display_colors)


def create_screening_status_chart(data: dict[str, int]) -> go.Figure:
    """创建筛选状态分布图。

    Args:
        data: 筛选状态数据

    Returns:
        Plotly Figure 对象
    """
    # 状态中文映射
    status_labels = {
        "qualified": "合格",
        "disqualified": "不合格",
        "pending": "待处理",
    }

    # 转换标签
    display_data = {status_labels.get(k, k): v for k, v in data.items()}

    # 对应颜色映射
    display_colors = {status_labels.get(k, k): v for k, v in STATUS_COLORS.items()}

    return create_pie_chart(display_data, "筛选状态分布", display_colors)


def create_school_distribution_chart(data: dict[str, int], top_n: int = 10) -> go.Figure:
    """创建学校分布柱状图。

    Args:
        data: 学校分布数据
        top_n: 显示前 N 个学校

    Returns:
        Plotly Figure 对象
    """
    # 按数量排序，取前 N 个
    sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:top_n])

    return create_bar_chart(
        sorted_data,
        f"院校分布（前 {top_n} 名）",
        x_label="院校",
        y_label="人数",
        color=CHART_COLORS["primary"],
        horizontal=True,
    )


def create_major_distribution_chart(data: dict[str, int], top_n: int = 10) -> go.Figure:
    """创建专业分布柱状图。

    Args:
        data: 专业分布数据
        top_n: 显示前 N 个专业

    Returns:
        Plotly Figure 对象
    """
    # 按数量排序，取前 N 个
    sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:top_n])

    return create_bar_chart(
        sorted_data,
        f"专业分布（前 {top_n} 名）",
        x_label="专业",
        y_label="人数",
        color=CHART_COLORS["secondary"],
        horizontal=True,
    )


def create_trend_chart(
    dates: list[str],
    counts: list[int],
    title: str = "筛选趋势",
) -> go.Figure:
    """创建筛选趋势折线图。

    Args:
        dates: 日期列表
        counts: 数量列表
        title: 图表标题

    Returns:
        Plotly Figure 对象
    """
    return create_line_chart(
        dates,
        counts,
        title,
        x_label="日期",
        y_label="筛选数量",
        color=CHART_COLORS["info"],
    )


def create_statistics_cards(
    total: int,
    qualified: int,
    disqualified: int,
    recent_7_days: int,
) -> str:
    """创建统计卡片 HTML。

    使用现代化渐变配色和优雅的卡片设计。

    Args:
        total: 总数
        qualified: 合格数
        disqualified: 不合格数
        recent_7_days: 近 7 天新增

    Returns:
        HTML 字符串
    """
    qualified_rate = (qualified / total * 100) if total > 0 else 0

    return f"""
    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin: -10px;">
        <div style="
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            color: white;
            padding: 24px;
            border-radius: 16px;
            min-width: 180px;
            flex: 1;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        ">
            <div style="position: absolute; top: -20px; right: -20px; width: 80px; height: 80px;
                background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px; font-weight: 500;">
                人才总数
            </div>
            <div style="font-size: 36px; font-weight: 700; line-height: 1.2;">
                {total:,}
            </div>
        </div>
        <div style="
            background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
            color: white;
            padding: 24px;
            border-radius: 16px;
            min-width: 180px;
            flex: 1;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
        ">
            <div style="position: absolute; top: -20px; right: -20px; width: 80px; height: 80px;
                background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px; font-weight: 500;">
                合格人数
            </div>
            <div style="font-size: 36px; font-weight: 700; line-height: 1.2;">
                {qualified:,}
            </div>
            <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">
                通过率 {qualified_rate:.1f}%
            </div>
        </div>
        <div style="
            background: linear-gradient(135deg, #EF4444 0%, #F87171 100%);
            color: white;
            padding: 24px;
            border-radius: 16px;
            min-width: 180px;
            flex: 1;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3);
        ">
            <div style="position: absolute; top: -20px; right: -20px; width: 80px; height: 80px;
                background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px; font-weight: 500;">
                不合格人数
            </div>
            <div style="font-size: 36px; font-weight: 700; line-height: 1.2;">
                {disqualified:,}
            </div>
        </div>
        <div style="
            background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
            color: white;
            padding: 24px;
            border-radius: 16px;
            min-width: 180px;
            flex: 1;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
        ">
            <div style="position: absolute; top: -20px; right: -20px; width: 80px; height: 80px;
                background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px; font-weight: 500;">
                近 7 天新增
            </div>
            <div style="font-size: 36px; font-weight: 700; line-height: 1.2;">
                {recent_7_days:,}
            </div>
        </div>
    </div>
    """


def create_comparison_chart(
    data: dict[str, dict[str, int]],
    title: str,
    colors: list[str] | None = None,
) -> go.Figure:
    """创建分组柱状图用于对比分析。

    Args:
        data: 数据字典，格式为 {类别: {子类别: 值}}
        title: 图表标题
        colors: 颜色列表

    Returns:
        Plotly Figure 对象
    """
    if colors is None:
        colors = [CHART_COLORS["primary"], CHART_COLORS["secondary"]]

    categories = list(data.keys())
    sub_categories = set()
    for cat_data in data.values():
        sub_categories.update(cat_data.keys())
    sub_categories = sorted(sub_categories)

    fig = go.Figure()

    for i, sub_cat in enumerate(sub_categories):
        values = [data[cat].get(sub_cat, 0) for cat in categories]
        color = colors[i % len(colors)]

        fig.add_trace(
            go.Bar(
                name=sub_cat,
                x=categories,
                y=values,
                marker_color=color,
                marker_line={"color": "white", "width": 1},
                hovertemplate=f"<b>{sub_cat}</b><br>%{{x}}: %{{y}}<extra></extra>",
            )
        )

    fig.update_layout(
        **DEFAULT_LAYOUT,
        title={
            "text": f"<b>{title}</b>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16, "color": "#1E293B"},
        },
        barmode="group",
        bargap=0.15,
        bargroupgap=0.1,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"showgrid": False, "showline": False},
        yaxis={"showgrid": True, "gridcolor": "#E2E8F0", "showline": False},
    )

    return fig


def create_gauge_chart(
    value: float,
    title: str,
    max_value: float = 100,
    color: str = CHART_COLORS["primary"],
) -> go.Figure:
    """创建仪表盘图表。

    Args:
        value: 当前值
        title: 图表标题
        max_value: 最大值
        color: 仪表颜色

    Returns:
        Plotly Figure 对象
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title, "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, max_value], "tickwidth": 1},
                "bar": {"color": color},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "#E2E8F0",
                "steps": [
                    {"range": [0, max_value * 0.5], "color": "#F1F5F9"},
                    {"range": [max_value * 0.5, max_value * 0.8], "color": "#E2E8F0"},
                    {"range": [max_value * 0.8, max_value], "color": "#CBD5E1"},
                ],
            },
            number={"font": {"size": 24, "color": "#1E293B"}},
        )
    )

    fig.update_layout(
        height=300,
        margin={"t": 60, "b": 20, "l": 20, "r": 20},
    )

    return fig


__all__ = [
    "ANIMATION_CONFIG",
    "CHART_COLORS",
    "DEFAULT_LAYOUT",
    "EDUCATION_COLORS",
    "STATUS_COLORS",
    "create_bar_chart",
    "create_comparison_chart",
    "create_education_distribution_chart",
    "create_gauge_chart",
    "create_line_chart",
    "create_major_distribution_chart",
    "create_pie_chart",
    "create_school_distribution_chart",
    "create_screening_status_chart",
    "create_statistics_cards",
    "create_trend_chart",
]
