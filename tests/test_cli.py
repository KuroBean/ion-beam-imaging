import json

from ionopt.backends.queue import QueueBackend
from ionopt.backends.transports import LocalFSTransport
from ionopt.cli import main
from ionopt.runlog import RunLog

from conftest import CONFIG_DIR, DEV_OVERRIDES
from helpers import einzel_job


def _args(tmp_path, *extra):
    return ["--config-dir", str(CONFIG_DIR), "--overrides", str(DEV_OVERRIDES),
            "--set", f"paths.results_dir={(tmp_path / 'results').as_posix()}",
            "--set", f"paths.queue_dir={(tmp_path / 'queue').as_posix()}",
            "--set", f"paths.db_path={(tmp_path / 'log.sqlite').as_posix()}",
            "--set", f"paths.optuna_db_path={(tmp_path / 'optuna.sqlite').as_posix()}", *extra]


def test_launch_preview(tmp_path, capsys):
    out = tmp_path / "lp.png"
    assert main(["launch-preview", *_args(tmp_path), "--out", str(out)]) == 0
    assert out.stat().st_size > 5000 and "ions" in capsys.readouterr().out


def test_run_job_check_recheck(cfg_tmp, tmp_path, capsys):
    job = einzel_job(cfg_tmp)
    jf = tmp_path / "job.json"
    jf.write_text(job.model_dump_json())
    assert main(["run-job", str(jf), *_args(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert f"job {job.job_id}: success" in out and "feasible=True" in out
    rd = tmp_path / "results" / job.job_id
    assert (rd / "metrics.json").is_file() and (rd / "plots" / "r_theta.png").is_file()

    assert main(["check", job.job_id, "--no-plots", *_args(tmp_path)]) == 0
    assert main(["recheck", "--all", *_args(tmp_path, "--set", "spec.requirements.eta_min=0.99")]) == 0
    assert "0 feasible" in capsys.readouterr().out
    with RunLog(tmp_path / "log.sqlite") as rl:
        assert len(rl.metrics_history(job.job_id)) == 2       # two spec hashes


def test_run_job_3d_needs_flag(cfg_tmp, tmp_path):
    jf = tmp_path / "job.json"
    jf.write_text(einzel_job(cfg_tmp, fidelity="3d").model_dump_json())
    assert main(["run-job", str(jf), *_args(tmp_path)]) == 2
    assert main(["run-job", str(jf), "--allow-3d", "--no-plots", *_args(tmp_path)]) == 0


def test_optimize_command(tmp_path, capsys):
    assert main(["optimize", "--config", "example_einzel", "--budget", "4", *_args(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "4 solves" in out


def test_worker_command_processes_queue(cfg_tmp, tmp_path, capsys):
    q = tmp_path / "queue"
    b = QueueBackend(cfg_tmp, LocalFSTransport(q))
    ids = [b.submit(einzel_job(cfg_tmp)) for _ in range(2)]
    assert main(["worker", "--runner", "mock", "--stop-when-empty", *_args(tmp_path)]) == 0
    assert "processed 2 jobs" in capsys.readouterr().out
    assert all((q / "done" / i / "meta.json").is_file() for i in ids)


def test_not_yet_commands(tmp_path):
    assert main(["baseline-b0", *_args(tmp_path)]) == 2


def test_fidelity_check_command(tmp_path, capsys):
    s = tmp_path / "settings.json"
    s.write_text(json.dumps([{"name": "einzel", "cfg": 1, "wiring": {"tip": "LV1", "e3": "LV2"},
                              "channels": {"LV1": 100.0, "LV2": 85.0, "HV1": -5000.0, "HV4": -200.0},
                              "positions_mm": {"lens_gap": 13.482, "z_mcp": 145, "mesh_gap": 12.7}}]))
    pins = ["--set", "spec.launch.n_theta=26", "--set", "spec.launch.n_phi=8", "--set", "spec.launch.preaccel=false"]
    assert main(["fidelity-check", "--settings", str(s), *_args(tmp_path, *pins)]) == 2      # needs --allow-3d
    assert main(["fidelity-check", "--settings", str(s), "--allow-3d", *_args(tmp_path, *pins)]) == 0
    assert '"fate_agreement"' in capsys.readouterr().out
