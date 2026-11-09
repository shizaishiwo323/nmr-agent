"""Runtime environment checks for the Streamlit NMR simulation app."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
import site
import sys
from typing import Callable, Sequence


EXPECTED_PYTHON = (3, 11)
START_COMMAND = "powershell -ExecutionPolicy Bypass -File scripts/run_streamlit_t2agent.ps1"


@dataclass(frozen=True)
class RuntimeEnvironmentStatus:
    ok: bool
    message: str
    python_version: str
    executable: str
    prefix: str
    user_site_enabled: bool


def _version_text(version_info: Sequence[int]) -> str:
    return ".".join(str(part) for part in version_info[:3])


def collect_runtime_environment_status(
    *,
    import_module: Callable[[str], object] = importlib.import_module,
    version_info: Sequence[int] | None = None,
    executable: str | None = None,
    prefix: str | None = None,
    user_site_enabled: bool | None = None,
) -> RuntimeEnvironmentStatus:
    version = tuple(version_info or sys.version_info)
    executable_text = executable or sys.executable
    prefix_text = prefix or str(Path(sys.prefix).resolve())
    user_site = site.ENABLE_USER_SITE if user_site_enabled is None else bool(user_site_enabled)
    problems: list[str] = []

    if version[:2] != EXPECTED_PYTHON:
        problems.append(
            f"Expected Python 3.11 for the verified pyGIMLi runtime, but this process uses Python {_version_text(version)}."
        )

    for module_name in ("pygimli", "pygimli.meshtools"):
        try:
            import_module(module_name)
        except Exception as exc:
            problems.append(f"Cannot import {module_name}: {exc}")

    if user_site:
        problems.append("User site-packages are enabled; set PYTHONNOUSERSITE=1 to avoid mixing packages across environments.")

    if problems:
        message = (
            "This Streamlit process is not using the verified T2 agent runtime.\n"
            f"Python executable: {executable_text}\n"
            f"Python prefix: {prefix_text}\n"
            + "\n".join(f"- {problem}" for problem in problems)
            + "\n\nStart the app with:\n"
            f"  {START_COMMAND}\n"
            "or use the t2agent conda environment python directly with PYTHONNOUSERSITE=1."
        )
        return RuntimeEnvironmentStatus(False, message, _version_text(version), executable_text, prefix_text, user_site)

    message = (
        "Verified runtime: Python 3.11 with pygimli.meshtools available.\n"
        f"Python executable: {executable_text}"
    )
    return RuntimeEnvironmentStatus(True, message, _version_text(version), executable_text, prefix_text, user_site)
