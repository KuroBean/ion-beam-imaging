"""Bayesian optimization over supply channel voltages and positions for one configuration (plan 9.9).

Search space (bounds from constraints.yaml for the configuration's chamber setup):
  * voltages of the LV channels used by the wiring, the MCP-front and mesh HV ports
  * z_mcp and mesh_gap (fixed when their range has min == max)
  * lens_gap (places the fixed lens stack), as a fraction of its feasible range so the
    stack always stays upstream of the mesh

Objective: minimize the checker score (max dtheta, degrees). Constraints (eta,
fast fraction, monotonicity, evaluability, optional constraints) go to Optuna's
constraints_func. Invalid or failed runs are logged and told to Optuna as FAILED trials.
The budget counts solves; studies resume from their SQLite storage.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable

import optuna

from . import units
from .backends import SimulationBackend, make_backend
from .checker import check
from .config import Config, ConfigError, ConfigurationDef, range_known
from .electrodes import check_structure, stack_layout, used_lv_channels
from .jobs import build_job
from .runlog import RunLog

log = logging.getLogger(__name__)
EPS_M = 1e-9


def _rng(cfg: Config, key: str) -> list[float]:
    return cfg.require(key)


@dataclass
class SearchSpace:
    conf: ConfigurationDef
    channels: dict[str, tuple[float, float]]               # V
    z_mcp: tuple[float, float]                             # m
    mesh_gap: tuple[float, float]                          # m
    lens_gap: tuple[float, float]                          # m
    stack_length: float                                    # m, E1 front to the end of the last stack part
    names: list[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, cfg: Config, conf: ConfigurationDef) -> "SearchSpace":
        problems = check_structure(cfg, conf.cfg, conf.wiring)
        if problems:
            raise ConfigError(f"configuration '{conf.config_id}' is invalid:\n  " + "\n  ".join(problems))
        s = cfg.constraints.supplies
        chan = {}
        for ch in used_lv_channels(cfg, conf.wiring):
            chan[ch] = tuple(_rng(cfg, "constraints.supplies.low_voltage.range_V"))
        hv = s.high_voltage.range_V
        for role, key in (("mcp_front", "constraints.supplies.mcp_front_V"), ("mesh", "constraints.supplies.mesh_V")):
            lo, hi = _rng(cfg, key)
            if range_known(hv):
                lo, hi = max(lo, hv[0]), min(hi, hv[1])
            chan[s.hv_port(role)] = (lo, hi)
        ck = f"constraints.chamber_setups.{conf.cfg}"
        mm = lambda r: (r[0] * units.MM, r[1] * units.MM)  # noqa: E731
        lo_g, hi_g = _rng(cfg, f"{ck}.mesh_gap_mm")
        lo_g = max(lo_g, cfg.require("constraints.mesh.min_gap_to_mcp_mm"))
        if lo_g > hi_g:
            raise ConfigError(f"{ck}.mesh_gap_mm upper bound is below constraints.mesh.min_gap_to_mcp_mm")
        parts = stack_layout(cfg, conf.cfg, 0.0)
        sp = cls(conf=conf, channels=chan, z_mcp=mm(_rng(cfg, f"{ck}.z_mcp_mm")),
                 mesh_gap=(lo_g * units.MM, hi_g * units.MM), lens_gap=mm(_rng(cfg, f"{ck}.lens_gap_mm")),
                 stack_length=max(e["z_back_m"] for e in parts))
        # worst case (mesh closest to the tip, stack furthest out) must still fit
        if sp.lens_gap[0] + sp.stack_length >= sp.z_mcp[0] - sp.mesh_gap[1] - EPS_M:
            raise ConfigError(f"configuration '{conf.config_id}': the lens stack does not fit in front of the mesh "
                              f"even at the smallest lens_gap, z_mcp and largest mesh_gap")
        return sp

    def lens_gap_max(self, z_mesh: float) -> float:
        """Largest lens_gap that keeps the whole stack upstream of the mesh plane."""
        return min(self.lens_gap[1], z_mesh - self.stack_length - EPS_M)

    # ---- optuna
    def suggest(self, trial: optuna.Trial) -> tuple[dict[str, float], dict[str, float]]:
        def f(name, lo, hi):
            return lo if hi - lo <= 1e-12 else trial.suggest_float(name, lo, hi)

        channels = {ch: f(ch, lo, hi) for ch, (lo, hi) in self.channels.items()}
        z_mcp = f("z_mcp_mm", self.z_mcp[0] / units.MM, self.z_mcp[1] / units.MM) * units.MM
        gap = f("mesh_gap_mm", self.mesh_gap[0] / units.MM, self.mesh_gap[1] / units.MM) * units.MM
        # lens_gap as a fraction of its feasible range, so the stack never reaches the mesh
        lo, hi = self.lens_gap[0], self.lens_gap_max(z_mcp - gap)
        lens_gap = lo if hi - lo <= 1e-12 else lo + trial.suggest_float("u_lens_gap", 0.0, 1.0) * (hi - lo)
        return channels, {"lens_gap": lens_gap, "z_mcp": z_mcp, "mesh_gap": gap}


@dataclass
class StudyResult:
    study_id: str
    config_id: str
    sampler: str
    n_trials: int
    n_failed: int
    n_feasible: int
    best_job_id: str | None
    best_score: float | None
    best_channels: dict[str, float] | None
    best_positions: dict[str, float] | None


# Optuna >= 5 reads per-trial constraints (Trial.set_constraint); older versions need constraints_func
NEW_CONSTRAINT_API = hasattr(optuna.trial.Trial, "set_constraint")


def make_sampler(cfg: Config) -> tuple[optuna.samplers.BaseSampler, str]:
    o = cfg.optimizer
    cons = None if NEW_CONSTRAINT_API else (lambda ft: ft.user_attrs.get("constraints", [1.0]))  # noqa: E731
    want = o.sampler
    if want in ("auto", "gp"):
        try:
            import torch  # noqa: F401  (GPSampler needs PyTorch)

            return optuna.samplers.GPSampler(seed=o.seed, n_startup_trials=o.n_startup_trials,
                                             constraints_func=cons), "gp"
        except ImportError:
            if want == "gp":
                raise ConfigError("optimizer.sampler = gp needs PyTorch (pip install torch), or use tpe/auto")
    return optuna.samplers.TPESampler(seed=o.seed, n_startup_trials=o.n_startup_trials, multivariate=True,
                                      constraints_func=cons), "tpe"


def _constraints(m, cfg: Config) -> dict[str, float]:
    """Optuna constraint values: <= 0 means satisfied."""
    r = m.requirements
    c = {"eta": cfg.spec.requirements.eta_min - r["eta"],
         "frac_fast": cfg.spec.requirements.frac_fast_min - r["frac_fast"],
         "monotonic": 0.0 if r["monotonic"] else 1.0,
         "evaluable": 0.0 if r["evaluable"] else 1.0}
    c.update({k: 0.0 if v else 1.0 for k, v in r.items() if k.startswith("opt_")})
    return c


def optimize(cfg: Config, config_id: str, budget: int | None = None, fidelity: str = "2d",
             backend: SimulationBackend | None = None, study_id: str | None = None,
             on_trial: Callable[[int, Any], None] | None = None) -> StudyResult:
    """Run (or resume) one optimization study for a fixed configuration."""
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    conf = cfg.b0_configs.get(config_id)
    space = SearchSpace.from_config(cfg, conf)
    # values the checker needs: fail now, not after the first solve
    for key in ("spec.detector.sigma_mcp_um", "spec.detector.mesh_open_fraction", "spec.requirements.eta_min",
                "spec.tolerances.energy_conservation_rel", "spec.tolerances.potential_match_V",
                "spec.tolerances.monotonic_tol_um", "spec.tolerances.fate_position_tol_um"):
        cfg.require(key)
    budget = budget or cfg.optimizer.default_budget
    backend = backend or make_backend(cfg)
    sampler, sampler_name = make_sampler(cfg)
    study_id = study_id or f"{config_id}-{fidelity}-seed{cfg.optimizer.seed}"
    db = cfg.path("optuna_db_path")
    db.parent.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(study_name=study_id, storage=f"sqlite:///{db.as_posix()}", sampler=sampler,
                                direction="minimize", load_if_exists=True)
    T = optuna.trial.TrialState
    for t in study.get_trials(deepcopy=False, states=(T.RUNNING,)):   # interrupted before: never left hanging
        study.tell(t.number, state=T.FAIL)
    done = len(study.get_trials(deepcopy=False, states=(T.COMPLETE, T.FAIL)))

    with RunLog(cfg.path("db_path")) as rl:
        rl.start_study(study_id, config_id, sampler_name, cfg.optimizer.seed, budget, fidelity)
        while done < budget:
            trial = study.ask()
            channels, positions = space.suggest(trial)
            job = build_job(cfg, conf, channels, positions, fidelity=fidelity,
                            tags={"study_id": study_id, "trial": str(trial.number), "purpose": "optimize"})
            trial.set_user_attr("job_id", job.job_id)
            bundle = backend.run(job)
            rl.record_job(job, bundle, cfg.config_hash(), backend=getattr(backend, "name", None))
            m = check(bundle.result_dir, cfg)
            rl.record_metrics(m)
            if cfg.optimizer.write_plots and bundle.status == "success":
                from .plots import make_plots
                make_plots(bundle.result_dir, cfg)
            trial.set_user_attr("flags", m.flags[:5])
            if not m.valid:
                study.tell(trial, state=T.FAIL)
            else:
                score = m.score if (m.score is not None and math.isfinite(m.score)) \
                    else cfg.optimizer.nonevaluable_score_deg
                cons = _constraints(m, cfg)
                if NEW_CONSTRAINT_API:
                    for k, v in cons.items():
                        trial.set_constraint(k, v)
                trial.set_user_attr("constraints", list(cons.values()))
                trial.set_user_attr("feasible", m.feasible)
                study.tell(trial, score)
            done += 1
            if on_trial:
                on_trial(done, m)

        best = _best(study)
        rl.finish_study(study_id, best.user_attrs["job_id"] if best else None)

    trials = study.get_trials(deepcopy=False)
    if best:
        ch_b, pos_b = space.suggest(optuna.trial.FixedTrial(best.params))
    return StudyResult(
        study_id=study_id, config_id=config_id, sampler=sampler_name,
        n_trials=len([t for t in trials if t.state in (T.COMPLETE, T.FAIL)]),
        n_failed=len([t for t in trials if t.state == T.FAIL]),
        n_feasible=len([t for t in trials if t.user_attrs.get("feasible")]),
        best_job_id=best.user_attrs["job_id"] if best else None,
        best_score=best.value if best else None,
        best_channels=ch_b if best else None, best_positions=pos_b if best else None,
    )


def _best(study: optuna.Study):
    ok = [t for t in study.get_trials(deepcopy=False, states=(optuna.trial.TrialState.COMPLETE,))
          if t.user_attrs.get("feasible")]
    return min(ok, key=lambda t: t.value) if ok else None
