import types
from pathlib import Path

from t2_agent.runtime_env import collect_runtime_environment_status


def _fake_importer(available: set[str]):
    def import_module(name: str):
        if name not in available:
            raise ModuleNotFoundError(name)
        return types.SimpleNamespace(__version__="test")

    return import_module


def test_runtime_environment_rejects_unverified_python_version():
    status = collect_runtime_environment_status(
        import_module=_fake_importer({"pygimli", "pygimli.meshtools"}),
        version_info=(3, 14, 6),
        executable="C:/Python314/python.exe",
        prefix="C:/Python314",
        user_site_enabled=False,
    )

    assert not status.ok
    assert "Python 3.11" in status.message
    assert "C:/Python314/python.exe" in status.message


def test_runtime_environment_reports_missing_pygimli_meshtools():
    status = collect_runtime_environment_status(
        import_module=_fake_importer({"pygimli"}),
        version_info=(3, 11, 15),
        executable="C:/ProgramData/anaconda3/python.exe",
        prefix="C:/ProgramData/anaconda3",
        user_site_enabled=True,
    )

    assert not status.ok
    assert "pygimli.meshtools" in status.message
    assert "scripts/run_streamlit_t2agent.ps1" in status.message
    assert "PYTHONNOUSERSITE" in status.message


def test_runtime_environment_accepts_verified_t2agent_runtime():
    status = collect_runtime_environment_status(
        import_module=_fake_importer({"pygimli", "pygimli.meshtools"}),
        version_info=(3, 11, 15),
        executable="/Users/example/.conda/envs/t2agent/python.exe",
        prefix="/Users/example/.conda/envs/t2agent",
        user_site_enabled=False,
    )

    assert status.ok
    assert "pygimli.meshtools" in status.message


def test_verified_start_script_exists_and_runs_preflight():
    script = Path("scripts/run_streamlit_t2agent.ps1")

    assert script.exists()
    text = script.read_text(encoding="utf-8")
    assert "check_t2agent_env.py" in text
    assert "PYTHONNOUSERSITE" in text
    assert "streamlit" in text
