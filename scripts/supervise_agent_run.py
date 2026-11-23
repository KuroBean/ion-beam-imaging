"""Keep a long agent run going without the author (author 2026-11-22, run 3).

Starts `ionopt agent-run` (or resumes the run if it already exists) and then:
  * edit approval pause  -> `agent-resume <run> --approve` (author: accept every editor change in this run)
  * planner question     -> stop with status QUESTION (logs/<run>.status holds the question); answer it with
                            `--answer "..."` on the next start of this script
  * finished (exit 0)    -> status DONE
  * crash / killed       -> kill orphaned COMSOL servers, wait, `agent-resume <run>`; after --max-stalls
                            restarts in a row without a new solve, stop with status CRITICAL

Run it detached from the editor/terminal, e.g. (PowerShell):
  Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine = '<python> scripts\\supervise_agent_run.py ...'; CurrentDirectory = '<repo>'}

Usage:
  python scripts/supervise_agent_run.py RUN_ID [--answer TEXT] [--goal-file F] -- <agent-run arguments>
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IONOPT = REPO / ".venv" / "Scripts" / "ionopt.exe"
PY = REPO / ".venv" / "Scripts" / "python.exe"


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Sup:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.log_path = REPO / "logs" / f"{run_id}.log"
        self.sup_path = REPO / "logs" / f"{run_id}-supervisor.log"
        self.status_path = REPO / "logs" / f"{run_id}.status"

    def note(self, msg: str) -> None:
        with self.sup_path.open("a", encoding="utf-8") as f:
            f.write(f"[{now()}] {msg}\n")

    def status(self, state: str, **extra) -> None:
        self.status_path.write_text(json.dumps({"state": state, "time": now(), "run_id": self.run_id, **extra},
                                               indent=1), encoding="utf-8")
        self.note(f"status {state} {extra if extra else ''}")

    def solves(self) -> int:
        """Jobs of this run's studies in the run log (progress measure)."""
        try:
            con = sqlite3.connect(REPO / "results" / "runlog.sqlite", timeout=30)
            n = con.execute("SELECT COUNT(*) FROM jobs WHERE study_id LIKE ?", (f"{self.run_id}-%",)).fetchone()[0]
            con.close()
            return int(n)
        except Exception as e:      # noqa: BLE001
            self.note(f"cannot count solves: {e}")
            return -1

    def exists(self) -> bool:
        return (REPO / "results" / "runs" / self.run_id / "checkpoints.sqlite").is_file()

    def call(self, args: list[str]) -> tuple[int, str]:
        """Run ionopt, appending its output to the run log; returns (exit code, this call's output)."""
        self.note("ionopt " + " ".join(a if len(a) < 80 else a[:60] + "..." for a in args))
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n===== [{now()}] ionopt {args[0]} {args[1] if len(args) > 1 else ''} =====\n")
            f.flush()
            p = subprocess.Popen([str(IONOPT), *args], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace")
            out = []
            for line in p.stdout:
                f.write(line)
                f.flush()
                out.append(line)
            rc = p.wait()
        self.note(f"exit {rc}")
        return rc, "".join(out)


def write_reports(sup: Sup) -> None:
    """Finished run: transcript, round-by-round overview page, cross-run index (scripts/agent_run_report.py)."""
    try:
        r = subprocess.run([str(PY), str(REPO / "scripts" / "agent_run_report.py"), sup.run_id], cwd=REPO,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        sup.note(f"reports: exit {r.returncode}" + ("" if r.returncode == 0 else f": {r.stderr.strip()[-500:]}"))
    except Exception as e:      # noqa: BLE001 - reports must never fail the run
        sup.note(f"reports failed: {e}")


def kill_orphan_comsol(sup: Sup) -> None:
    """COMSOL servers whose parent process is gone (left by a killed run) hold RAM: stop them."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='comsolmphserver.exe'\" | ForEach-Object { "
          "if (-not (Get-Process -Id $_.ParentProcessId -ErrorAction SilentlyContinue)) { "
          "Stop-Process -Id $_.ProcessId -Force; Write-Output \"killed $($_.ProcessId)\" } }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=120)
        if r.stdout.strip():
            sup.note("orphan COMSOL: " + r.stdout.strip().replace("\n", ", "))
    except Exception as e:      # noqa: BLE001
        sup.note(f"orphan check failed: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--answer", default=None, help="answer to a pending planner question")
    ap.add_argument("--goal-file", default=None, help="file whose text is passed as --goal on the first start")
    ap.add_argument("--max-stalls", type=int, default=6, help="restarts in a row without a new solve before CRITICAL")
    ap.add_argument("--wait-s", type=int, default=120, help="pause before restarting after a crash")
    argv = sys.argv[1:]
    cut = argv.index("--") if "--" in argv else len(argv)
    a = ap.parse_args(argv[:cut])
    run_args = argv[cut + 1:]          # agent-run arguments after "--" (first start only)
    if a.goal_file:
        run_args += ["--goal", (REPO / a.goal_file).read_text(encoding="utf-8").strip()]
    sup = Sup(a.run_id)
    sup.status("RUNNING", solves=sup.solves())
    answer, stalls, last = a.answer, 0, sup.solves()

    while True:
        if not sup.exists():
            rc, out = sup.call(["agent-run", "--run-id", a.run_id, *run_args])
        elif answer is not None:
            rc, out = sup.call(["agent-resume", a.run_id, "--answer", answer])
            answer = None
        else:
            rc, out = sup.call(["agent-resume", a.run_id])

        if rc == 0:
            if "already finished" in out or re.search(r"run \S+: stop ", out):
                write_reports(sup)
                sup.status("DONE", solves=sup.solves(), summary=out.strip().splitlines()[-2:])
                return 0
        if rc == 3 or "PAUSED:" in out:
            if "(edit_approval)" in out:
                m = re.search(r"edit (\S+): variant (\S+): (.*)", out)
                sup.note(f"auto-approving edit (author 2026-11-22): {m.group(0) if m else '?'}")
                with (REPO / "logs" / f"{a.run_id}-approved-edits.log").open("a", encoding="utf-8") as f:
                    f.write(f"[{now()}] {m.group(0) if m else out[-500:]}\n")
                rc, out = sup.call(["agent-resume", a.run_id, "--approve"])
                if rc == 0 and re.search(r"run \S+: stop ", out):
                    write_reports(sup)
                    sup.status("DONE", solves=sup.solves(), summary=out.strip().splitlines()[-2:])
                    return 0
                if rc == 3 or "PAUSED:" in out:
                    if "(edit_approval)" in out:
                        continue        # another edit: handled on the next pass (resume shows the pause again)
                    q = out[out.find("PAUSED:"):].strip()
                    sup.status("QUESTION", text=q)
                    return 3
                if rc != 0:
                    pass                # crashed while continuing: fall through to the restart logic
                else:
                    continue
            else:
                q = out[out.find("PAUSED:"):].strip()
                sup.status("QUESTION", text=q)
                return 3
        if rc == 2:
            sup.status("CRITICAL", reason="ionopt refused the command (exit 2)", tail=out.strip().splitlines()[-5:])
            return 2
        # crash or kill: restart unless nothing moves any more
        n = sup.solves()
        stalls = 0 if n > last else stalls + 1
        last = max(last, n)
        if stalls >= a.max_stalls:
            sup.status("CRITICAL", reason=f"{stalls} restarts in a row without a new solve",
                       tail=out.strip().splitlines()[-15:])
            return 1
        sup.status("RESTARTING", exit=rc, solves=n, stalls=stalls, tail=out.strip().splitlines()[-5:])
        kill_orphan_comsol(sup)
        time.sleep(a.wait_s)
        sup.status("RUNNING", solves=sup.solves())


if __name__ == "__main__":
    sys.exit(main())
