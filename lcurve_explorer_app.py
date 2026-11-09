from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from t2_agent.interactive_lcurve import (
    AXIS_COLOR,
    DEFAULT_EXPLORER_LCURVE_PARAMS,
    FIGURE_FONT,
    GRID_COLOR,
    alpha_path_figure,
    lcurve_metric_figure,
    selected_alpha_from_plotly_selection,
)
from t2_agent.tools import repair_workbook, validate_workbook

from T2process.nmr_t2.config import LCurveConfig, NnlsConfig
from T2process.nmr_t2.io_utils import safe_token
from T2process.nmr_t2.pipelines import run_lcurve_workbook, run_nnls_workbook


APP_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = APP_ROOT / "testData" / "standard 30%.1.pea"
RUN_ROOT = APP_ROOT / "runs" / "interactive_lcurve_explorer"


def _page_css() -> str:
    return """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
    }
    h1 {
        letter-spacing: 0;
        font-size: 1.65rem !important;
    }
    div[data-testid="stVerticalBlock"] > div:has(> div.t2-explorer-card) {
        background: #f7faff;
        border: 1px solid #c9d8ee;
        border-radius: 8px;
        padding: 0.9rem 1rem 0.55rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }
    .t2-explorer-card {
        display: none;
    }
    .t2-section-label {
        color: #475569;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0;
        margin-bottom: 0.2rem;
    }
    .t2-muted-note {
        color: #64748b;
        font-size: 0.82rem;
        margin: -0.2rem 0 0.55rem;
    }
    </style>
    """


def _read_first_sheet(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None)
    if not sheets:
        raise ValueError(f"No sheets found in {path}.")
    return next(iter(sheets.values()))


def _selected_index(metrics: pd.DataFrame, alpha: float | None) -> int | None:
    if alpha is None:
        if "is_best" in metrics and bool(metrics["is_best"].any()):
            return int(metrics.index[metrics["is_best"].astype(bool)][0])
        return None
    differences = (metrics["alpha_regularization"].astype(float) - float(alpha)).abs()
    return int(differences.idxmin())


def _spectrum_figure(spectrum: pd.DataFrame, alpha: float) -> go.Figure:
    peak_idx = int(spectrum["amplitude"].astype(float).idxmax())
    peak_t2 = float(spectrum.loc[peak_idx, "t2_ms"])
    peak_amp = float(spectrum.loc[peak_idx, "amplitude"])
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=spectrum["t2_ms"],
            y=spectrum["amplitude"],
            mode="lines",
            line={"color": "#0f766e", "width": 2.2},
            fill="tozeroy",
            fillcolor="rgba(15, 118, 110, 0.18)",
            hovertemplate="T2=%{x:.6g} ms<br>amplitude=%{y:.6g}<extra></extra>",
            name="T2 spectrum",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[peak_t2],
            y=[peak_amp],
            mode="markers",
            marker={"color": "#f97316", "size": 9, "line": {"color": "#ffffff", "width": 1.4}},
            hovertemplate="Peak T2=%{x:.6g} ms<br>amplitude=%{y:.6g}<extra></extra>",
            name="Peak",
        )
    )
    figure.update_layout(
        title={"text": f"T2 spectrum | alpha={alpha:.6e}", "font": {"size": 15, "color": "#111827"}, "x": 0.02, "xanchor": "left"},
        xaxis={
            "title": {"text": "T2 (ms)", "font": {"size": 12, "color": AXIS_COLOR}},
            "type": "log",
            "showgrid": True,
            "gridcolor": GRID_COLOR,
            "zeroline": False,
            "linecolor": GRID_COLOR,
            "tickfont": {"size": 11, "color": AXIS_COLOR},
        },
        yaxis={
            "title": {"text": "Amplitude (a.u.)", "font": {"size": 12, "color": AXIS_COLOR}},
            "showgrid": True,
            "gridcolor": GRID_COLOR,
            "zeroline": False,
            "linecolor": GRID_COLOR,
            "tickfont": {"size": 11, "color": AXIS_COLOR},
        },
        height=360,
        template="plotly_white",
        plot_bgcolor="#f8fbff",
        paper_bgcolor="#ffffff",
        font=FIGURE_FONT,
        showlegend=False,
        margin={"l": 58, "r": 18, "t": 46, "b": 50},
    )
    return figure


def _visible_spectrum_source(
    outputs: dict[str, str],
    confirmed: dict[str, str] | None,
    selected_alpha: float | None,
    confirmed_alpha: float | None,
) -> tuple[Path, float, str] | None:
    """Return the spectrum workbook currently visible at the bottom of the page."""

    if confirmed and confirmed.get("spectrum_xlsx") and confirmed_alpha is not None:
        return Path(confirmed["spectrum_xlsx"]), float(confirmed_alpha), "Confirmed fixed-alpha"
    if outputs.get("spectrum_xlsx") and selected_alpha is not None:
        return Path(outputs["spectrum_xlsx"]), float(selected_alpha), "L-curve selected"
    return None


def _run_lcurve(input_path: Path, params: dict[str, float | int | bool]) -> dict[str, str]:
    validation = validate_workbook(input_path)
    if validation.status != "success":
        raise RuntimeError(validation.error or validation.message)

    standardized = repair_workbook(
        input_path,
        RUN_ROOT / "standardized",
        float(validation.summary.get("recommended_time_to_ms_scale", 1.0)),
    )
    if standardized.status != "success" or not standardized.artifacts:
        raise RuntimeError(standardized.error or standardized.message)

    cfg = LCurveConfig(
        num_bins=int(params["num_bins"]),
        t2_min_ms=float(params["t2_min_ms"]),
        t2_max_ms=float(params["t2_max_ms"]),
        alpha_min=float(params["alpha_min"]),
        alpha_max=float(params["alpha_max"]),
        alpha_count=int(params["alpha_count"]),
    )
    result = run_lcurve_workbook(
        Path(standardized.artifacts[0]),
        RUN_ROOT / "lcurve",
        config=cfg,
        time_to_ms_scale=1.0,
        trim_from_peak=bool(params["trim_from_peak"]),
    )
    return {key: str(value) for key, value in result.items()} | {"standardized_workbook": standardized.artifacts[0]}


def _run_confirmed_inversion(standardized_workbook: Path, selected_alpha: float, params: dict[str, float | int | bool]) -> dict[str, str]:
    token = safe_token(f"alpha_{selected_alpha:.6g}")
    cfg = NnlsConfig(
        regularization=float(selected_alpha),
        num_bins=int(params["num_bins"]),
        t2_min_ms=float(params["t2_min_ms"]),
        t2_max_ms=float(params["t2_max_ms"]),
    )
    result = run_nnls_workbook(
        standardized_workbook,
        RUN_ROOT / "confirmed_inversion" / token,
        config=cfg,
        time_to_ms_scale=1.0,
        trim_from_peak=bool(params["trim_from_peak"]),
    )
    return {key: str(value) for key, value in result.items()}


def main() -> None:
    st.set_page_config(page_title="Interactive L-curve Explorer", layout="wide")
    st.markdown(_page_css(), unsafe_allow_html=True)
    st.title("Interactive L-curve Explorer")
    st.caption("Run L-curve first. Click a smoothing factor point. Confirm only when you want to run and visualize that fixed-alpha T2 inversion.")

    with st.sidebar:
        input_text = st.text_input("Decay data file", value=str(DEFAULT_INPUT))
        params = dict(DEFAULT_EXPLORER_LCURVE_PARAMS)
        params["alpha_min"] = st.number_input("L-curve alpha min", value=float(params["alpha_min"]), format="%.6g")
        params["alpha_max"] = st.number_input("L-curve alpha max", value=float(params["alpha_max"]), format="%.6g")
        params["alpha_count"] = st.number_input("L-curve alpha point count", value=int(params["alpha_count"]), min_value=3, step=1)
        params["num_bins"] = st.number_input("T2 bins", value=int(params["num_bins"]), min_value=20, step=10)
        params["t2_min_ms"] = st.number_input("T2 min (ms)", value=float(params["t2_min_ms"]), format="%.6g")
        params["t2_max_ms"] = st.number_input("T2 max (ms)", value=float(params["t2_max_ms"]), format="%.6g")
        params["trim_from_peak"] = st.checkbox("Trim from global peak", value=bool(params["trim_from_peak"]))
        run_lcurve = st.button("Run L-curve", type="primary", width="stretch")

    input_path = Path(input_text)
    if run_lcurve:
        st.session_state.pop("confirmed_result", None)
        st.session_state.pop("selected_alpha", None)
        with st.status("Running L-curve search...", expanded=True) as status:
            outputs = _run_lcurve(input_path, params)
            st.session_state.lcurve_outputs = outputs
            st.session_state.explorer_params = params
            status.update(label="L-curve search complete", state="complete")

    outputs = st.session_state.get("lcurve_outputs")
    if not outputs:
        st.info("Click Run L-curve to generate the interactive search plots.")
        return

    metrics = _read_first_sheet(Path(outputs["metrics_xlsx"]))
    params = st.session_state.get("explorer_params", params)
    selected_alpha = st.session_state.get("selected_alpha")
    selected_index = _selected_index(metrics, selected_alpha)

    left, right = st.columns([0.6, 0.4], gap="medium")
    with left:
        st.markdown("<div class='t2-explorer-card'></div>", unsafe_allow_html=True)
        st.markdown("<div class='t2-section-label'>L-curve trade-off</div>", unsafe_allow_html=True)
        selection = st.plotly_chart(
            lcurve_metric_figure(metrics, selected_index=selected_index),
            key="lcurve_metric_selection",
            on_select="rerun",
            selection_mode="points",
            width="stretch",
        )
    clicked_alpha = selected_alpha_from_plotly_selection(selection, metrics)
    if clicked_alpha is not None:
        st.session_state.selected_alpha = clicked_alpha
        selected_alpha = clicked_alpha
        selected_index = _selected_index(metrics, selected_alpha)

    with right:
        st.markdown("<div class='t2-explorer-card'></div>", unsafe_allow_html=True)
        st.markdown("<div class='t2-section-label'>Smoothing-factor path</div>", unsafe_allow_html=True)
        st.plotly_chart(
            alpha_path_figure(metrics, selected_index=selected_index),
            key="alpha_path_selection",
            on_select="ignore",
            width="stretch",
        )

    if selected_alpha is None and selected_index is not None:
        selected_alpha = float(metrics.iloc[selected_index]["alpha_regularization"])
        st.session_state.selected_alpha = selected_alpha

    if selected_alpha is not None:
        st.success(f"Selected alpha: {selected_alpha:.6e}")
        if st.button("Confirm analysis with selected alpha", type="primary"):
            with st.status("Running fixed-alpha NNLS inversion...", expanded=True) as status:
                confirmed = _run_confirmed_inversion(Path(outputs["standardized_workbook"]), selected_alpha, params)
                st.session_state.confirmed_result = confirmed
                st.session_state.confirmed_alpha = selected_alpha
                status.update(label="Confirmed inversion complete", state="complete")

    confirmed = st.session_state.get("confirmed_result")
    visible_source = _visible_spectrum_source(
        outputs,
        confirmed,
        selected_alpha,
        st.session_state.get("confirmed_alpha"),
    )
    if visible_source:
        spectrum_path, spectrum_alpha, spectrum_mode = visible_source
        st.markdown("<div class='t2-explorer-card'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='t2-section-label'>{spectrum_mode} T2 spectrum</div>", unsafe_allow_html=True)
        st.markdown("<div class='t2-muted-note'>Only the selected T2 distribution is shown here; decay-fit panels stay hidden for this explorer.</div>", unsafe_allow_html=True)
        spectrum = _read_first_sheet(spectrum_path)
        st.plotly_chart(_spectrum_figure(spectrum, spectrum_alpha), width="stretch")
        st.download_button(
            "Download visible T2 spectrum workbook",
            data=spectrum_path.read_bytes(),
            file_name=spectrum_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )


if __name__ == "__main__":
    main()
