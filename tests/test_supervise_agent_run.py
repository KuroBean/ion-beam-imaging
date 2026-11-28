"""scripts/supervise_agent_run.py: the optional B0 phase shares the agent run's config arguments."""
import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "supervise_agent_run.py"
_spec = importlib.util.spec_from_file_location("supervise_agent_run", _SCRIPT)
sup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sup)


def test_config_args_keeps_only_overrides_and_set_pairs():
    run_args = ["--budget", "500", "--require-removed", "screen_mesh", "--overrides", "config/x.yaml",
                "--set", "spec.requirements.eta_min=0.85", "--goal", "text --set inside"]
    assert sup.config_args(run_args) == ["--overrides", "config/x.yaml", "--set", "spec.requirements.eta_min=0.85"]


def test_b0_command():
    cmd = sup.b0_command("c3_x", 500, "run5", ["--rounds", "50", "--overrides", "config/x.yaml"])
    assert cmd == ["baseline-b0", "--configs", "c3_x", "--budget", "500", "--tag", "run5",
                   "--overrides", "config/x.yaml"]
