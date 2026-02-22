"""Streamlit 组件模块。

提供可复用的 UI 组件、API 客户端和主题配置。
"""

from frontend.components.api_client import (
    AnalysisAPI,
    APIClient,
    APIError,
    ConditionAPI,
    RetryConfig,
    RetryStrategy,
    TalentAPI,
    get_analysis_api,
    get_api_client,
    get_condition_api,
    get_talent_api,
)
from frontend.components.charts import (
    CHART_COLORS,
    DEFAULT_LAYOUT,
    EDUCATION_COLORS,
    STATUS_COLORS,
    create_bar_chart,
    create_comparison_chart,
    create_education_distribution_chart,
    create_gauge_chart,
    create_line_chart,
    create_major_distribution_chart,
    create_pie_chart,
    create_school_distribution_chart,
    create_screening_status_chart,
    create_statistics_cards,
    create_trend_chart,
)
from frontend.components.theme import (
    CHART_COLORS as THEME_CHART_COLORS,
)
from frontend.components.theme import (
    DARK_THEME,
    LIGHT_THEME,
    ColorScheme,
    create_card_html,
    create_stat_card_html,
    get_custom_css,
    get_theme,
)
from frontend.components.theme import (
    EDUCATION_COLORS as THEME_EDUCATION_COLORS,
)
from frontend.components.theme import (
    STATUS_COLORS as THEME_STATUS_COLORS,
)

__all__ = [
    "CHART_COLORS",
    "DARK_THEME",
    "DEFAULT_LAYOUT",
    "EDUCATION_COLORS",
    "LIGHT_THEME",
    "STATUS_COLORS",
    "THEME_CHART_COLORS",
    "THEME_EDUCATION_COLORS",
    "THEME_STATUS_COLORS",
    "APIClient",
    "APIError",
    "AnalysisAPI",
    "ColorScheme",
    "ConditionAPI",
    "RetryConfig",
    "RetryStrategy",
    "TalentAPI",
    "create_bar_chart",
    "create_card_html",
    "create_comparison_chart",
    "create_education_distribution_chart",
    "create_gauge_chart",
    "create_line_chart",
    "create_major_distribution_chart",
    "create_pie_chart",
    "create_school_distribution_chart",
    "create_screening_status_chart",
    "create_stat_card_html",
    "create_statistics_cards",
    "create_trend_chart",
    "get_analysis_api",
    "get_api_client",
    "get_condition_api",
    "get_custom_css",
    "get_talent_api",
    "get_theme",
]
