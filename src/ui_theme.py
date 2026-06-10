from __future__ import annotations

from typing import Literal


ThemeName = Literal["light", "dark"]


def normalize_theme(theme: str | None) -> ThemeName:
    return "dark" if theme == "dark" else "light"


def apply_plotly_theme(fig, theme: str | None):
    normalized = normalize_theme(theme)
    is_dark = normalized == "dark"
    grid_color = "rgba(255,255,255,0.10)" if is_dark else "rgba(15,23,42,0.10)"
    axis_color = "#C8DAE8" if is_dark else "#475569"
    font_color = "#FFFFFF" if is_dark else "#0F172A"
    plot_bg = "rgba(255,255,255,0.03)" if is_dark else "#FFFFFF"
    colorway = (
        ["#60A5FA", "#FCD34D", "#34D399", "#FC8181", "#A5B4FC", "#2DD4BF"]
        if is_dark
        else ["#1D4ED8", "#D97706", "#059669", "#DC2626", "#6366F1", "#0D9488"]
    )

    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=plot_bg,
        font={"color": font_color, "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif"},
        title={"font": {"color": font_color, "size": 18}},
        colorway=colorway,
        margin={"l": 24, "r": 24, "t": 56, "b": 42},
        legend={"font": {"color": font_color}},
    )
    fig.update_xaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        linecolor=grid_color,
        tickfont={"color": axis_color},
        title_font={"color": axis_color},
    )
    fig.update_yaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        linecolor=grid_color,
        tickfont={"color": axis_color},
        title_font={"color": axis_color},
    )
    return fig


def status_row_background(status: str, theme: str | None = None) -> str:
    normalized = normalize_theme(theme)
    if normalized == "dark":
        colors = {
            # attention-card statuses (kept for cards)
            "success": "rgba(52, 211, 153, 0.18)",
            "warning": "rgba(252, 211, 77, 0.18)",
            "danger":  "rgba(252, 129, 129, 0.18)",
            # action-based statuses (used by recommendation table rows)
            "increase": "rgba(52, 211, 153, 0.15)",
            "decrease": "rgba(252, 129, 129, 0.15)",
            "hold":     "rgba(96, 165, 250, 0.15)",
        }
    else:
        colors = {
            "success": "#DCFCE7",
            "warning": "#FEF3C7",
            "danger":  "#FEE2E2",
            "increase": "#F0FDF4",
            "decrease": "#FFF1F2",
            "hold":     "#EFF6FF",
        }
    return colors.get(status, "")


def status_row_border(status: str, theme: str | None = None) -> str:
    normalized = normalize_theme(theme)
    if normalized == "dark":
        colors = {
            "success": "rgba(52, 211, 153, 0.70)",
            "warning": "rgba(252, 211, 77, 0.72)",
            "danger":  "rgba(252, 129, 129, 0.76)",
            "increase": "rgba(52, 211, 153, 0.60)",
            "decrease": "rgba(252, 129, 129, 0.65)",
            "hold":     "rgba(96, 165, 250, 0.60)",
        }
    else:
        colors = {
            "success": "#16A34A",
            "warning": "#D97706",
            "danger":  "#DC2626",
            "increase": "#22C55E",
            "decrease": "#F43F5E",
            "hold":     "#3B82F6",
        }
    return colors.get(status, "transparent")
