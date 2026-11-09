"""Helpers for the standalone interactive L-curve explorer."""

from __future__ import annotations

from typing import Any

import pandas as pd


class _PlotlyGraphObjectsProxy:
    def __getattr__(self, name: str) -> Any:
        import plotly.graph_objects as graph_objects

        return getattr(graph_objects, name)


go = _PlotlyGraphObjectsProxy()


DEFAULT_EXPLORER_LCURVE_PARAMS: dict[str, float | int | bool] = {
    "t2_min_ms": 0.01,
    "t2_max_ms": 100000.0,
    "num_bins": 200,
    "alpha_min": 1e-3,
    "alpha_max": 1e4,
    "alpha_count": 300,
    "trim_from_peak": True,
    "time_to_ms_scale": 1.0,
}

FIGURE_FONT = {"family": "Arial, Helvetica, DejaVu Sans, sans-serif", "size": 12, "color": "#1f2937"}
GRID_COLOR = "#dbe7f6"
AXIS_COLOR = "#526176"
NEUTRAL_LINE = "#1d4ed8"
NEUTRAL_MARKER = "#38bdf8"
SELECTED_MARKER = "#f97316"
PLOT_BG = "#f8fbff"


def _marker_colors(count: int, selected_index: int | None) -> list[str]:
    if selected_index is None:
        return [NEUTRAL_MARKER] * count
    return [SELECTED_MARKER if idx == selected_index else NEUTRAL_MARKER for idx in range(count)]


def _marker_sizes(count: int, selected_index: int | None) -> list[int]:
    if selected_index is None:
        return [6] * count
    return [11 if idx == selected_index else 6 for idx in range(count)]


def _alpha_labels(values: pd.Series) -> list[str]:
    return [f"{float(value):.6e}" for value in values]


def _apply_compact_scientific_layout(
    figure: go.Figure,
    *,
    title: str,
    x_title: str,
    y_title: str,
    height: int,
    x_type: str | None = None,
    y_type: str | None = None,
) -> go.Figure:
    xaxis = {
        "title": {"text": x_title, "font": {"size": 12, "color": AXIS_COLOR}},
        "showgrid": True,
        "gridcolor": GRID_COLOR,
        "zeroline": False,
        "linecolor": GRID_COLOR,
        "tickfont": {"size": 11, "color": AXIS_COLOR},
    }
    yaxis = {
        "title": {"text": y_title, "font": {"size": 12, "color": AXIS_COLOR}},
        "showgrid": True,
        "gridcolor": GRID_COLOR,
        "zeroline": False,
        "linecolor": GRID_COLOR,
        "tickfont": {"size": 11, "color": AXIS_COLOR},
    }
    if x_type:
        xaxis["type"] = x_type
    if y_type:
        yaxis["type"] = y_type
    figure.update_layout(
        title={"text": title, "font": {"size": 15, "color": "#111827"}, "x": 0.02, "xanchor": "left"},
        xaxis=xaxis,
        yaxis=yaxis,
        height=height,
        template="plotly_white",
        plot_bgcolor=PLOT_BG,
        paper_bgcolor="#ffffff",
        font=FIGURE_FONT,
        showlegend=False,
        margin={"l": 58, "r": 18, "t": 46, "b": 50},
    )
    return figure


def lcurve_metric_figure(metrics: pd.DataFrame, selected_index: int | None = None) -> go.Figure:
    """Build the clickable L-curve metric figure without embedding spectra."""

    alpha_labels = _alpha_labels(metrics["alpha_regularization"])
    customdata = list(
        zip(
            range(len(metrics)),
            alpha_labels,
            metrics["slope_reciprocal"].astype(float),
        )
    )
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=metrics["residual_norm"],
            y=metrics["roughness_norm"],
            mode="lines+markers",
            customdata=customdata,
            line={"color": NEUTRAL_LINE, "width": 1.4},
            marker={
                "color": _marker_colors(len(metrics), selected_index),
                "size": _marker_sizes(len(metrics), selected_index),
                "line": {"color": "#ffffff", "width": 1},
                "opacity": 0.88,
            },
            hovertemplate=(
                "index=%{customdata[0]}<br>"
                "alpha=%{customdata[1]}<br>"
                "residual=%{x:.6g}<br>"
                "roughness=%{y:.6g}<br>"
                "slope reciprocal=%{customdata[2]:.6g}<extra></extra>"
            ),
            name="L-curve points",
        )
    )
    return _apply_compact_scientific_layout(
        figure,
        title="Interactive L-curve",
        x_title="Residual norm",
        y_title="Roughness norm",
        height=360,
        x_type="log",
        y_type="log",
    )


def alpha_path_figure(metrics: pd.DataFrame, selected_index: int | None = None) -> go.Figure:
    """Build a diagnostic plot showing how alpha changes across the search."""

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=list(range(len(metrics))),
            y=metrics["alpha_regularization"],
            mode="lines+markers",
            customdata=list(zip(range(len(metrics)), _alpha_labels(metrics["alpha_regularization"]))),
            line={"color": NEUTRAL_LINE, "width": 1.3},
            marker={
                "color": _marker_colors(len(metrics), selected_index),
                "size": _marker_sizes(len(metrics), selected_index),
                "line": {"color": "#ffffff", "width": 1},
                "opacity": 0.88,
            },
            hovertemplate="index=%{customdata[0]}<br>alpha=%{customdata[1]}<extra></extra>",
            name="Alpha path",
        )
    )
    return _apply_compact_scientific_layout(
        figure,
        title="Alpha search path",
        x_title="L-curve point index",
        y_title="alpha regularization",
        height=300,
        y_type="log",
    )


def t2_spectrum_figure(spectrum: pd.DataFrame, alpha: float, title_prefix: str = "T2 spectrum preview") -> go.Figure:
    """Build a compact T2 spectrum preview figure for a selected alpha."""

    t2_col = "t2_ms" if "t2_ms" in spectrum.columns else spectrum.columns[0]
    amp_col = "amplitude" if "amplitude" in spectrum.columns else spectrum.columns[1]
    t2 = pd.to_numeric(spectrum[t2_col], errors="coerce")
    amplitude = pd.to_numeric(spectrum[amp_col], errors="coerce")
    valid = t2.notna() & amplitude.notna() & (t2 > 0)
    t2 = t2[valid]
    amplitude = amplitude[valid]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=t2,
            y=amplitude,
            mode="lines",
            line={"color": "#0f766e", "width": 2.2},
            fill="tozeroy",
            fillcolor="rgba(15,118,110,0.18)",
            hovertemplate="T2=%{x:.6g} ms<br>amplitude=%{y:.6g}<extra></extra>",
            name="T2 spectrum",
        )
    )
    if len(amplitude):
        peak_idx = int(amplitude.to_numpy().argmax())
        figure.add_trace(
            go.Scatter(
                x=[float(t2.iloc[peak_idx])],
                y=[float(amplitude.iloc[peak_idx])],
                mode="markers",
                marker={"color": SELECTED_MARKER, "size": 9, "line": {"color": "#ffffff", "width": 1.4}},
                hovertemplate="Peak T2=%{x:.6g} ms<br>amplitude=%{y:.6g}<extra></extra>",
                name="Peak",
            )
        )
    return _apply_compact_scientific_layout(
        figure,
        title=f"{title_prefix} | alpha={alpha:.6e}",
        x_title="T2 (ms)",
        y_title="Amplitude (a.u.)",
        height=320,
        x_type="log",
    )


def selected_alpha_from_plotly_selection(selection: dict[str, Any] | None, metrics: pd.DataFrame) -> float | None:
    """Extract the clicked alpha from Streamlit's Plotly selection payload."""

    if not selection:
        return None
    points = (selection.get("selection") or {}).get("points") or []
    if not points:
        return None
    point = points[0]
    index = point.get("point_index", point.get("pointIndex"))
    if index is None:
        return None
    index_int = int(index)
    if index_int < 0 or index_int >= len(metrics):
        return None
    return float(metrics.iloc[index_int]["alpha_regularization"])
