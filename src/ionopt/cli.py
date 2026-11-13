"""Command-line interface (plan 9.11). Every command accepts --set key=value overrides."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from .config import Config, ConfigError, load_config


def _common() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--config-dir", type=Path, default=None, help="config directory (default: ./config found upward)")
    p.add_argument("--set", dest="overrides", action="append", default=[], metavar="KEY=VALUE",
                   help="override a config value, e.g. --set spec.detector.sigma_mcp_um=80 (repeatable)")
    p.add_argument("--overrides", dest="override_files", action="append", default=[], type=Path, metavar="FILE",
                   help="partial YAML deep-merged over the config (repeatable), e.g. config/dev_overrides.yaml")
    return p


def _load(a) -> Config:
    return load_config(a.config_dir, a.overrides, a.override_files)


# --------------------------------------------------------------------------- commands


def cmd_config_check(a) -> int:
    cfg = _load(a)
    print(f"config OK ({cfg.root_dir / 'config'})")
    print(f"config hash {cfg.config_hash()[:12]}  spec hash {cfg.spec_hash()[:12]}")
    if cfg.overrides:
        print("overrides:", *cfg.overrides, sep="\n  ")
    tbd = cfg.list_tbd()
    print(f"\n{len(tbd)} TBD keys:")
    for k in tbd:
        print(f"  {k}")
    return 0


def _ingest(cfg: Config, result_dir: Path, plots: bool) -> int:
    """Check a result folder, record it in the run log, optionally plot; print a summary."""
    from .checker import check
    from .results import load_job, read_bundle
    from .runlog import RunLog

    m = check(result_dir, cfg)
    with RunLog(cfg.path("db_path")) as rl:
        rl.record_job(load_job(result_dir), read_bundle(result_dir))
        rl.record_metrics(m)
    if plots and read_bundle(result_dir).status == "success":
        from .plots import make_plots
        make_plots(result_dir, cfg)
    score = f"{m.score:.4g} deg" if m.score is not None else "n/a"
    eta = m.requirements.get("eta")
    eta_s = f"{eta:.3g}" if eta is not None else "n/a"
    print(f"{m.job_id}: valid={m.valid} feasible={m.feasible} score={score} eta={eta_s}")
    for f in m.flags:
        print(f"  - {f}")
    return 0 if m.valid else 1


def cmd_launch_preview(a) -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from .launch import make_launch
    from .plots import BLUE, FIGSIZE, INK2

    cfg = _load(a)
    df = make_launch(cfg.spec.launch, a.fidelity)
    g = df.groupby("theta_deg")["weight"].sum()
    print(f"{len(df)} ions ({df['theta_deg'].nunique()} theta x {df['KE0_eV'].nunique()} energies"
          + (f" x {cfg.spec.launch.n_phi} phi" if a.fidelity == "3d" else "") + ")")
    print(f"weighted mean theta {np.sum(df['weight'] * df['theta_deg']):.2f} deg; "
          f"HWHM {cfg.spec.launch.hwhm_deg} deg, sigma {np.degrees(cfg.spec.launch.sigma_rad):.2f} deg")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(g.index, g.values, width=0.8 * (g.index[1] - g.index[0]), color=BLUE)
    ax.set(xlabel="launch angle θ (deg)", ylabel="ion weight", title="Launch weights per θ")
    ax.text(0, 1.01, f"{a.fidelity.upper()}, {len(df)} ions; weights ∝ exp(-θ²/2σ²)·sin θ·dθ", fontsize=8,
            color=INK2, transform=ax.transAxes)
    out = a.out or (cfg.path("results_dir") / f"launch_preview_{a.fidelity}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")
    return 0


def cmd_run_job(a) -> int:
    from .backends import make_backend
    from .schemas import JobSpec

    cfg = _load(a)
    job = JobSpec.model_validate_json(a.job_file.read_text(encoding="utf-8"))
    if a.fidelity:
        job.fidelity = a.fidelity
    if job.fidelity == "3d" and not a.allow_3d:
        print("3D runs need --allow-3d (plan section 14: 3D only when explicitly requested)", file=sys.stderr)
        return 2
    backend = make_backend(cfg)
    res = backend.run(job, cfg.backend.job_timeout_s)
    print(f"job {res.job_id}: {res.status}" + (f" ({res.error})" if res.error else ""))
    return _ingest(cfg, Path(res.result_dir), not a.no_plots)


def cmd_check(a) -> int:
    cfg = _load(a)
    rc = 0
    for jid in a.job_ids:
        rc |= _ingest(cfg, cfg.path("results_dir") / jid, not a.no_plots)
    return rc


def cmd_recheck(a) -> int:
    from .checker import recheck
    from .runlog import RunLog

    cfg = _load(a)
    if not a.all and not a.job_ids:
        print("give job ids or --all", file=sys.stderr)
        return 2
    ms = recheck(cfg.path("results_dir"), cfg, None if a.all else a.job_ids)
    with RunLog(cfg.path("db_path")) as rl:
        for m in ms:
            rl.record_metrics(m)
    n_feas = sum(m.feasible for m in ms)
    print(f"rechecked {len(ms)} runs with spec {cfg.spec_hash()[:12]}: {sum(m.valid for m in ms)} valid, "
          f"{n_feas} feasible")
    return 0


def cmd_optimize(a) -> int:
    from .optimize import optimize

    cfg = _load(a)
    if a.fidelity == "3d" and not a.allow_3d:
        print("3D optimization needs --allow-3d", file=sys.stderr)
        return 2

    def progress(n, m):
        s = f"{m.score:.4g}" if m.score is not None else "n/a"
        print(f"  [{n}] valid={m.valid} feasible={m.feasible} score={s}", flush=True)

    r = optimize(cfg, a.config, a.budget, a.fidelity, on_trial=progress)
    print(f"study {r.study_id} ({r.sampler}): {r.n_trials} solves, {r.n_failed} failed, {r.n_feasible} feasible")
    if r.best_job_id:
        print(f"best {r.best_job_id}: score {r.best_score:.4g} deg")
        print("  channels:", {k: round(v, 2) for k, v in r.best_channels.items()})
        print("  positions (mm):", {k: round(v * 1e3, 3) for k, v in r.best_positions.items()})
    else:
        print("no feasible solution found")
    return 0


def cmd_worker(a) -> int:
    import logging

    from .worker.queue_worker import QueueWorker

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cfg = _load(a)
    if a.runner == "mock":
        from .backends.mock import run_mock
        runner = run_mock
    else:
        from .worker.comsol_worker import run_worker
        n = run_worker(cfg, max_jobs=a.max_jobs, stop_when_empty=a.stop_when_empty)
        print(f"worker processed {n} jobs")
        return 0
    w = QueueWorker(cfg.path("queue_dir"), runner, f"{a.runner}-worker", root_dir=cfg.root_dir,
                    poll_s=cfg.backend.poll_interval_s)
    n = w.run(max_jobs=a.max_jobs, stop_when_empty=a.stop_when_empty)
    print(f"worker processed {n} jobs")
    return 0


def cmd_fidelity_check(a) -> int:
    import json

    from .fidelity import load_settings, run_fidelity_check

    cfg = _load(a)
    if not a.allow_3d:
        print("the fidelity check runs 3D jobs: add --allow-3d (plan section 14)", file=sys.stderr)
        return 2
    if not a.settings and not a.resume:
        print("give --settings FILE or --resume results/fidelity_<time>_jobs.json", file=sys.stderr)
        return 2
    rep = run_fidelity_check(cfg, load_settings(a.settings) if a.settings else [], resume=a.resume)
    print(json.dumps(rep["summary"], indent=1, default=str))
    return 0 if not rep["failed"] else 1


def _not_yet(task: str):
    def fn(a) -> int:
        print(f"not implemented yet ({task})", file=sys.stderr)
        return 2
    return fn


def _args_launch(p):
    p.add_argument("--fidelity", choices=["2d", "3d"], default="2d")
    p.add_argument("--out", type=Path, default=None, help="output PNG (default results/launch_preview_<fid>.png)")


def _args_run_job(p):
    p.add_argument("job_file", type=Path, help="job.json (JobSpec; positions in metres, voltages in V)")
    p.add_argument("--fidelity", choices=["2d", "3d"], default=None, help="override the job's fidelity")
    p.add_argument("--allow-3d", action="store_true")
    p.add_argument("--no-plots", action="store_true")


def _args_check(p):
    p.add_argument("job_ids", nargs="+")
    p.add_argument("--no-plots", action="store_true")


def _args_recheck(p):
    p.add_argument("job_ids", nargs="*")
    p.add_argument("--all", action="store_true")


def _args_optimize(p):
    p.add_argument("--config", required=True, help="config_id from b0_configs.yaml")
    p.add_argument("--budget", type=int, default=None, help="number of solves (default optimizer.default_budget)")
    p.add_argument("--fidelity", choices=["2d", "3d"], default="2d")
    p.add_argument("--allow-3d", action="store_true")


def _args_fidelity(p):
    p.add_argument("--settings", type=Path, default=None,
                   help="JSON list of {name, cfg, wiring, channels, positions_mm}")
    p.add_argument("--resume", type=Path, default=None,
                   help="job manifest of an interrupted check (results/fidelity_<time>_jobs.json): no resubmission")
    p.add_argument("--allow-3d", action="store_true")


def _args_worker(p):
    p.add_argument("--runner", choices=["mock", "comsol"], default="comsol")
    p.add_argument("--max-jobs", type=int, default=None)
    p.add_argument("--stop-when-empty", action="store_true")


COMMANDS = {
    "config-check": (cmd_config_check, "load and validate all config, list TBD keys", None),
    "launch-preview": (cmd_launch_preview, "plot the launch distribution and weights", _args_launch),
    "run-job": (cmd_run_job, "run one job through the configured backend, then check it", _args_run_job),
    "check": (cmd_check, "run the checker on stored results", _args_check),
    "recheck": (cmd_recheck, "recompute metrics for stored runs with the current spec", _args_recheck),
    "optimize": (cmd_optimize, "optimize one configuration from b0_configs.yaml", _args_optimize),
    "worker": (cmd_worker, "start a worker on this machine (queue backend)", _args_worker),
    "baseline-b0": (_not_yet("task 11"), "baseline B0 over b0_configs.yaml (task 11)", None),
    "promote": (_not_yet("task 11"), "rerun top 2D results in 3D (task 11)", None),
    "fidelity-check": (cmd_fidelity_check, "2D vs 3D on identical settings (task 10)", _args_fidelity),
}


def build_parser() -> argparse.ArgumentParser:
    common = _common()
    ap = argparse.ArgumentParser(prog="ionopt", description="Ion optics design tools (plan_v1 Phase 1)")
    sub = ap.add_subparsers(dest="command", required=True)
    for name, (fn, help_, add_args) in COMMANDS.items():
        sp = sub.add_parser(name, help=help_, parents=[common])
        if add_args:
            add_args(sp)
        sp.set_defaults(func=fn)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        return a.func(a) or 0
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
