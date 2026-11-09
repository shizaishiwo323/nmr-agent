"""Shared data models for the T2 Streamlit agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ToolStatus = Literal["success", "failed", "needs_confirmation"]


@dataclass
class AgentToolResult:
    """Structured result returned by every whitelisted agent tool."""

    status: ToolStatus
    message: str
    artifacts: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class UserWorkflowPlan:
    """Inferred user intent and key processing parameters."""

    workflow: Literal[
        "lcurve_inversion",
        "fixed_nnls",
        "gaussian_only",
        "full_analysis",
        "simulation_2d_png",
        "simulation_2d_rule",
        "simulation_2d_full",
    ] = "lcurve_inversion"
    needs_gaussian: bool = False
    peak_count: int = 2
    regularization: float | None = None
    t2_min_ms: float = 1e-2
    t2_max_ms: float = 1e5
    trim_from_peak: bool = True
    user_is_unsure: bool = True
