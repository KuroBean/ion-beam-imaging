"""Run log: SQLite database of jobs, metrics, studies and promotions (plan 9.8).

Raw exports in results/<job_id>/ are the permanent record; metrics are re-derivable,
so `recheck` adds a new metrics row per spec_hash instead of overwriting.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator

from .schemas import JobSpec, Metrics, ResultBundle
from .utils import now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    created_at TEXT, fidelity TEXT, cfg INTEGER,
    config_json TEXT,              -- electrodes used, wiring, channels, positions, levels
    status TEXT, error TEXT, backend TEXT, worker_host TEXT, solve_time_s REAL,
    model_hash TEXT, git_commit TEXT, config_hash TEXT,
    study_id TEXT, config_id TEXT
);
CREATE TABLE IF NOT EXISTS metrics (
    job_id TEXT, spec_hash TEXT, created_at TEXT,
    valid INTEGER, feasible INTEGER, score REAL, eta REAL, frac_fast REAL,
    monotonic INTEGER, r90 REAL, fill_fraction REAL, metrics_json TEXT,
    PRIMARY KEY (job_id, spec_hash)
);
CREATE TABLE IF NOT EXISTS studies (
    study_id TEXT PRIMARY KEY, config_id TEXT, optimizer TEXT, seed INTEGER, budget INTEGER,
    fidelity TEXT, started_at TEXT, finished_at TEXT, best_job_id TEXT
);
CREATE TABLE IF NOT EXISTS promotions (
    job_id_2d TEXT, job_id_3d TEXT, score_2d REAL, score_3d REAL, eta_2d REAL, eta_3d REAL, created_at TEXT,
    PRIMARY KEY (job_id_2d, job_id_3d)
);
CREATE INDEX IF NOT EXISTS jobs_study ON jobs(study_id);
-- Phase 2 agent loop (plan_phase2 section 9)
CREATE TABLE IF NOT EXISTS agent_runs (
    run_id TEXT PRIMARY KEY, method TEXT, case_id TEXT, seed INTEGER, models_json TEXT,
    spec_hash TEXT, constraints_hash TEXT, agents_hash TEXT, config_hash TEXT, assumptions_json TEXT,
    started_at TEXT, finished_at TEXT, stop_reason TEXT, best_job_id TEXT, best_score REAL, solves_used INTEGER
);
CREATE TABLE IF NOT EXISTS agent_rounds (
    run_id TEXT, round INTEGER, action TEXT, diagnosis TEXT, validation_status TEXT, study_id TEXT,
    n_solves INTEGER, best_job_id TEXT, score REAL, eta REAL, feasible INTEGER, critic_verdict TEXT,
    counted INTEGER, record_json TEXT, created_at TEXT,
    PRIMARY KEY (run_id, round)
);
CREATE TABLE IF NOT EXISTS agent_calls (
    call_id TEXT PRIMARY KEY, run_id TEXT, round INTEGER, role TEXT, model TEXT, call_dir TEXT,
    prompt_hash TEXT, template_hash TEXT, output_json TEXT, raw_json TEXT, session_id TEXT,
    duration_s REAL, cost_usd REAL, retries INTEGER, error TEXT, created_at TEXT
);
CREATE INDEX IF NOT EXISTS agent_calls_run ON agent_calls(run_id);
"""


class RunLog:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> "RunLog":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---------------------------------------------------------------- writes

    def record_job(self, job: JobSpec, bundle: ResultBundle | None = None, config_hash: str | None = None,
                   backend: str | None = None) -> None:
        meta = bundle.meta if bundle else None
        cfg_json = json.dumps({"wiring": job.wiring,
                               "channels": job.channels, "positions": job.positions,
                               "mesh_level": job.mesh_level, "ion_level": job.ion_level, "tags": job.tags})
        row = {
            "job_id": job.job_id, "created_at": now_iso(), "fidelity": job.fidelity, "cfg": job.cfg,
            "config_json": cfg_json,
            "status": bundle.status if bundle else "pending", "error": bundle.error if bundle else None,
            "backend": backend or (meta.backend if meta else None),
            "worker_host": meta.worker_host if meta else None,
            "solve_time_s": meta.solve_time_s if meta else None,
            "model_hash": meta.model_hash if meta else None,
            "git_commit": meta.git_commit if meta else None,
            "config_hash": config_hash or (meta.config_hash if meta else None),
            "study_id": job.tags.get("study_id"), "config_id": job.tags.get("config_id"),
        }
        with self.con:
            # keep the original created_at if the job is re-recorded (e.g. pending -> done)
            old = self.con.execute("SELECT created_at FROM jobs WHERE job_id=?", (job.job_id,)).fetchone()
            if old:
                row["created_at"] = old["created_at"]
            self.con.execute(f"INSERT OR REPLACE INTO jobs ({','.join(row)}) VALUES ({','.join('?' * len(row))})",
                             tuple(row.values()))

    def record_metrics(self, m: Metrics) -> None:
        req, spot = m.requirements or {}, m.spot or {}
        row = (m.job_id, m.spec_hash, now_iso(), int(m.valid), int(m.feasible), m.score, req.get("eta"),
               req.get("frac_fast"), int(bool((m.mapping or {}).get("monotonic"))), spot.get("r90_mm"),
               spot.get("fill_fraction"), m.model_dump_json())
        with self.con:
            self.con.execute("INSERT OR REPLACE INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", row)

    def start_study(self, study_id: str, config_id: str, optimizer: str, seed: int, budget: int,
                    fidelity: str = "2d") -> None:
        with self.con:
            self.con.execute("INSERT OR IGNORE INTO studies (study_id, config_id, optimizer, seed, budget, fidelity,"
                             " started_at) VALUES (?,?,?,?,?,?,?)",
                             (study_id, config_id, optimizer, seed, budget, fidelity, now_iso()))
            self.con.execute("UPDATE studies SET budget=? WHERE study_id=?", (budget, study_id))

    def finish_study(self, study_id: str, best_job_id: str | None) -> None:
        with self.con:
            self.con.execute("UPDATE studies SET finished_at=?, best_job_id=? WHERE study_id=?",
                             (now_iso(), best_job_id, study_id))

    def record_promotion(self, job_id_2d: str, job_id_3d: str, score_2d, score_3d, eta_2d, eta_3d) -> None:
        with self.con:
            self.con.execute("INSERT OR REPLACE INTO promotions VALUES (?,?,?,?,?,?,?)",
                             (job_id_2d, job_id_3d, score_2d, score_3d, eta_2d, eta_3d, now_iso()))

    # ---------------------------------------------------------------- agent loop (Phase 2)

    def start_agent_run(self, run_id: str, method: str, case_id: str, seed: int, models: dict,
                        spec_hash: str, constraints_hash: str, agents_hash: str, config_hash: str,
                        assumptions: list[str]) -> None:
        with self.con:
            self.con.execute(
                "INSERT OR IGNORE INTO agent_runs (run_id, method, case_id, seed, models_json, spec_hash, "
                "constraints_hash, agents_hash, config_hash, assumptions_json, started_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, method, case_id, seed, json.dumps(models), spec_hash, constraints_hash, agents_hash,
                 config_hash, json.dumps(assumptions), now_iso()))

    def finish_agent_run(self, run_id: str, stop_reason: str | None, best_job_id: str | None,
                         best_score: float | None, solves_used: int) -> None:
        with self.con:
            self.con.execute("UPDATE agent_runs SET finished_at=?, stop_reason=?, best_job_id=?, best_score=?, "
                             "solves_used=? WHERE run_id=?",
                             (now_iso(), stop_reason, best_job_id, best_score, solves_used, run_id))

    def record_round(self, run_id: str, rec: dict) -> None:
        """rec: a RoundRecord as JSON-compatible dict (agents/state.py)."""
        p, v, c, m = rec.get("proposal") or {}, rec.get("validation") or {}, rec.get("critic") or {}, \
            rec.get("metrics") or {}
        row = (run_id, rec["round"], p.get("action"), p.get("diagnosis"), v.get("status"), rec.get("study_id"),
               rec.get("n_solves", 0), rec.get("best_job_id"), m.get("score"), m.get("eta"),
               None if m.get("feasible") is None else int(bool(m.get("feasible"))), c.get("verdict"),
               int(bool(rec.get("counted", True))), json.dumps(rec, default=str), now_iso())
        with self.con:
            self.con.execute("INSERT OR REPLACE INTO agent_rounds VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)

    def record_agent_call(self, call_id: str, run_id: str, round_: int, role: str, model: str, call_dir: str,
                          prompt_hash: str, template_hash: str | None, output: dict | None, raw: dict | None,
                          session_id: str | None, duration_s: float, cost_usd: float, retries: int,
                          error: str | None) -> None:
        with self.con:
            self.con.execute(
                "INSERT OR REPLACE INTO agent_calls VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (call_id, run_id, round_, role, model, call_dir, prompt_hash, template_hash,
                 json.dumps(output) if output is not None else None,
                 json.dumps(raw, default=str) if raw is not None else None, session_id, duration_s, cost_usd,
                 retries, error, now_iso()))

    def agent_run(self, run_id: str) -> dict | None:
        r = self._rows("SELECT * FROM agent_runs WHERE run_id=?", (run_id,))
        return r[0] if r else None

    def agent_rounds(self, run_id: str) -> list[dict]:
        return self._rows("SELECT * FROM agent_rounds WHERE run_id=? ORDER BY round", (run_id,))

    def agent_calls(self, run_id: str) -> list[dict]:
        return self._rows("SELECT * FROM agent_calls WHERE run_id=? ORDER BY created_at, rowid", (run_id,))

    # ---------------------------------------------------------------- reads

    def _rows(self, sql: str, args: tuple = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self.con.execute(sql, args).fetchall()]

    def job(self, job_id: str) -> dict | None:
        r = self._rows("SELECT * FROM jobs WHERE job_id=?", (job_id,))
        return r[0] if r else None

    def jobs(self, study_id: str | None = None) -> list[dict]:
        if study_id is None:
            return self._rows("SELECT * FROM jobs ORDER BY created_at")
        return self._rows("SELECT * FROM jobs WHERE study_id=? ORDER BY created_at", (study_id,))

    def metrics(self, job_id: str, spec_hash: str | None = None) -> dict | None:
        """Metrics row for a job: for spec_hash if given, else the most recent."""
        if spec_hash:
            r = self._rows("SELECT * FROM metrics WHERE job_id=? AND spec_hash=?", (job_id, spec_hash))
        else:
            r = self._rows("SELECT * FROM metrics WHERE job_id=? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                           (job_id,))
        return r[0] if r else None

    def metrics_history(self, job_id: str) -> list[dict]:
        return self._rows("SELECT * FROM metrics WHERE job_id=? ORDER BY created_at", (job_id,))

    def study(self, study_id: str) -> dict | None:
        r = self._rows("SELECT * FROM studies WHERE study_id=?", (study_id,))
        return r[0] if r else None

    def study_results(self, study_id: str, spec_hash: str) -> list[dict]:
        """Jobs of a study joined with their metrics for one spec, best feasible first."""
        return self._rows(
            "SELECT j.job_id, j.status, j.config_json, m.valid, m.feasible, m.score, m.eta, m.frac_fast "
            "FROM jobs j LEFT JOIN metrics m ON m.job_id=j.job_id AND m.spec_hash=? WHERE j.study_id=? "
            "ORDER BY m.feasible DESC, m.score ASC", (spec_hash, study_id))

    def promotions(self) -> list[dict]:
        return self._rows("SELECT * FROM promotions ORDER BY created_at")

    def iter_job_ids(self) -> Iterator[str]:
        for r in self.con.execute("SELECT job_id FROM jobs ORDER BY created_at"):
            yield r["job_id"]
