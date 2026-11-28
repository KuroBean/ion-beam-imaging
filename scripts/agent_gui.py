"""Ion beam agent console: a local GUI to start, watch and stop an agent loop run.

    .venv\\Scripts\\python scripts\\agent_gui.py            # opens the console in an app window
    .venv\\Scripts\\python scripts\\agent_gui.py --no-open  # only start the server

What it does
  * Setup: chamber drop-down with a live 2D diagram, voltage / position / budget / detector settings
    (several pages behind a drop-down), and a goal text for the planner.
  * Start: writes logs/<run>-goal.txt and logs/<run>-overrides.yaml, checks them with the ionopt config
    loader, then starts scripts/supervise_agent_run.py detached from this process (same method as
    memory note "long runs": WMI Win32_Process.Create), so closing the GUI or the editor does not stop a run.
  * Monitor: state, solves, rounds, best score, log tail, planner questions (answer box), Stop and Resume.

Only the standard library is used for the server (plus ionopt/pyyaml from the project .venv for the config
check). The server listens on 127.0.0.1 only and every change needs the session token embedded in the page.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

REPO = Path(__file__).resolve().parent.parent
PY = REPO / ".venv" / "Scripts" / "python.exe"
WEB = Path(__file__).resolve().parent / "agent_gui"
LOGS = REPO / "logs"
RESULTS = REPO / "results"

# Run in the project venv: it has ionopt and pyyaml.
if PY.is_file() and Path(sys.executable).resolve() != PY.resolve():
    sys.exit(subprocess.call([str(PY), str(Path(__file__).resolve()), *sys.argv[1:]]))

import yaml  # noqa: E402

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,58}$")
TOKEN = secrets.token_urlsafe(24)
STATIC_EXT = {".html", ".png", ".jpg", ".jpeg", ".svg", ".css", ".js", ".json", ".txt", ".md", ".csv", ".gif"}

# ------------------------------------------------------------------------------------------- config defaults


def read_yaml(name: str) -> dict:
    return yaml.safe_load((REPO / "config" / f"{name}.yaml").read_text(encoding="utf-8")) or {}


def defaults() -> dict:
    """Everything the page needs to show the as-configured values (ranges, limits, geometry)."""
    con, spec, opt, ag = read_yaml("constraints"), read_yaml("spec"), read_yaml("optimizer"), read_yaml("agents")
    cs = con["chamber_setups"]
    sup = con["supplies"]
    el = con["electrodes"]
    loop = ag.get("loop", {})

    def rng(v, fallback):
        return list(v) if v and None not in v else fallback

    chambers = {}
    for k, c in cs.items():
        usable = all(rng(c.get(x), None) for x in ("lens_gap_mm", "mesh_gap_mm", "z_mcp_mm"))
        chambers[str(k)] = {
            "name": c.get("name", f"setup {k}"),
            "usable": bool(usable),
            "lens_gap": rng(c.get("lens_gap_mm"), None),
            "mesh_gap": rng(c.get("mesh_gap_mm"), None),
            "z_mcp": rng(c.get("z_mcp_mm"), None),
            "mcp_on_rods": c.get("mcp_rod_margin_mm") is not None,
            "has_deflectors": int(k) == 3,
        }
    return {
        "chambers": chambers,
        "lv_range": rng(sup["low_voltage"]["range_V"], [-300, 300]),
        "mcp_front": rng(sup.get("mcp_front_V"), [-10000, -2000]),
        "mesh_v": rng(sup.get("mesh_V"), [-10000, 0]),
        "ext_min": opt.get("min_extraction_V") if opt.get("min_extraction_V") is not None else 1,
        "ext_max": opt.get("max_extraction_V"),
        "ext_fixed": opt.get("fixed_extraction_V"),
        "budget": int(loop.get("solve_budget", 200)),
        "rounds": int(loop.get("round_cap", 8)),
        "round_max": int(loop.get("study_budget_max", 60)),
        "no_improve": int(loop.get("no_improvement_rounds", 3)),
        "improve_tol": float(loop.get("improvement_tol_deg", 0.01)),
        "eta_min": float(spec["requirements"]["eta_min"]),
        "sigma_mcp": float(spec["detector"]["sigma_mcp_um"]),
        "hwhm": float(spec["launch"]["hwhm_deg"]),
        "e0": float(spec["launch"]["E0_eV"]),
        "mass": float(spec["launch"]["mass_Da"]),
        "charge": int(spec["launch"]["charge"]),
        "stack": [{"front": s["front_mm"], "plate": s["plate_mm"], "r_in": s["r_in_mm"], "r_out": s["r_out_mm"]}
                  for s in el["stack"]],
        "deflectors": [{"name": d["name"], "front": d["front_mm"], "length": d["length_mm"], "r_in": d["r_in_mm"],
                        "r_out": d["r_out_mm"]} for d in el["deflectors"]],
        "mcp_diameter": float(spec["detector"]["mcp_active_diameter_mm"]),
        "suggested_run_id": suggest_run_id(),
        "goals": list_goals(),
    }


def suggest_run_id() -> str:
    n = 0
    for p in list(LOGS.glob("run-*")) + list((RESULTS / "runs").glob("run-*")):
        m = re.match(r"run-(\d+)", p.name)
        if m:
            n = max(n, int(m.group(1)))
    return f"run-{n + 1}-cfg1"


def list_goals() -> list[dict]:
    out = []
    for p in sorted(LOGS.glob("run-*-goal.txt"), key=lambda q: q.stat().st_mtime, reverse=True):
        out.append({"name": p.name[: -len("-goal.txt")], "file": p.name})
    return out


# ------------------------------------------------------------------------------------------- processes


def ps_run(script: str, timeout: int = 60) -> subprocess.CompletedProcess:
    enc = base64.b64encode(script.encode("utf-16-le")).decode()
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
                          capture_output=True, text=True, timeout=timeout, creationflags=NO_WINDOW)


_sup_cache: dict = {"t": 0.0, "v": {}}
_sup_lock = threading.Lock()


def supervisors(max_age: float = 3.0) -> dict[str, list[int]]:
    """run id -> process ids of running supervise_agent_run.py processes (also ones started elsewhere)."""
    with _sup_lock:
        if time.time() - _sup_cache["t"] < max_age:
            return _sup_cache["v"]
        script = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                  "Where-Object { $_.CommandLine -like '*supervise_agent_run.py*' } | "
                  "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }")
        found: dict[str, list[int]] = {}
        try:
            r = ps_run(script)
            for line in r.stdout.splitlines():
                pid, _, cmd = line.partition("\t")
                m = re.search(r"supervise_agent_run\.py\"?\s+\"?([^\"\s]+)", cmd)
                if m and pid.strip().isdigit():
                    found.setdefault(m.group(1), []).append(int(pid))
        except Exception:      # noqa: BLE001 - a failed process query must not take the GUI down
            found = _sup_cache["v"]
        _sup_cache.update(t=time.time(), v=found)
        return found


def launch_detached(args: list[str]) -> int:
    """Start python <args> detached from this process (Win32_Process.Create, like the long-run practice)."""
    cmd = subprocess.list2cmdline([str(PY), *args]).replace("'", "''")
    cwd = str(REPO).replace("'", "''")
    script = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
              f"-Arguments @{{CommandLine = '{cmd}'; CurrentDirectory = '{cwd}'}}; "
              "if ($r.ReturnValue -ne 0) { Write-Error \"Create failed: $($r.ReturnValue)\"; exit 1 }; "
              "Write-Output $r.ProcessId")
    r = ps_run(script)
    if r.returncode != 0 or not r.stdout.strip().isdigit():
        raise RuntimeError(f"could not start the supervisor: {(r.stderr or r.stdout).strip()[:300]}")
    _sup_cache["t"] = 0.0
    return int(r.stdout.strip())


def kill_run_processes(pids: list[int]) -> None:
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
    # COMSOL servers left behind hold gigabytes of RAM (same rule as the supervisor)
    ps_run("Get-CimInstance Win32_Process -Filter \"Name='comsolmphserver.exe'\" | ForEach-Object { "
           "if (-not (Get-Process -Id $_.ParentProcessId -ErrorAction SilentlyContinue)) { "
           "Stop-Process -Id $_.ProcessId -Force } }")
    _sup_cache["t"] = 0.0


# ------------------------------------------------------------------------------------------- run info


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_exists(run_id: str) -> bool:
    return (RESULTS / "runs" / run_id / "checkpoints.sqlite").is_file()


def read_status(run_id: str) -> dict | None:
    p = LOGS / f"{run_id}.status"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def tail(path: Path, n: int, max_bytes: int = 60000) -> list[str]:
    if not path.is_file():
        return []
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        data = f.read().decode("utf-8", errors="replace")
    data = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", data)
    return data.replace("\r", "").splitlines()[-n:]


def count_solves(run_id: str) -> int | None:
    db = RESULTS / "runlog.sqlite"
    if not db.is_file():
        return None
    try:
        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=5)
        n = con.execute("SELECT COUNT(*) FROM jobs WHERE study_id LIKE ?", (f"{run_id}-%",)).fetchone()[0]
        con.close()
        return int(n)
    except Exception:      # noqa: BLE001
        return None


def run_meta(run_id: str) -> dict:
    p = LOGS / f"{run_id}.gui.json"
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    meta: dict = {}
    sup = tail(LOGS / f"{run_id}-supervisor.log", 400, 400000)
    for line in sup:
        if "ionopt agent-run" in line:
            for key, flag in (("budget", "--budget"), ("rounds", "--rounds")):
                m = re.search(rf"{flag} (\d+)", line)
                if m:
                    meta[key] = int(m.group(1))
            break
    return meta


def monitor(run_id: str) -> dict:
    sups = supervisors()
    alive = bool(sups.get(run_id))
    st = read_status(run_id)
    state = (st or {}).get("state")
    summary_p = RESULTS / "runs" / run_id / "summary.json"
    summary = None
    if summary_p.is_file():
        try:
            summary = json.loads(summary_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            summary = None
    if state in ("RUNNING", "RESTARTING") and not alive:
        state = "STOPPED"
    if state is None:
        state = "RUNNING" if alive else ("DONE" if summary and summary.get("stop_reason") else
                                          ("STOPPED" if run_exists(run_id) else "IDLE"))
    log = tail(LOGS / f"{run_id}.log", 60)
    rounds, last_round, best, best_round = 0, None, None, None
    for line in tail(LOGS / f"{run_id}.log", 4000, 600000):
        m = re.search(r"round (\d+):? ", line)
        if m:
            rounds = max(rounds, int(m.group(1)))
        m = re.search(r"round (\d+): (\d+) solves, (\d+) feasible, best ([0-9.eE+-]+)", line)
        if m:
            v = float(m.group(4))
            if v < 1 and (best is None or v < best):
                best, best_round = v, int(m.group(1))
    if log:
        last_round = next((ln for ln in reversed(log) if re.search(r"\] round \d+", ln)), None)
    best_info = None
    if summary and summary.get("best"):
        b = summary["best"]
        best_info = {"score": b.get("score"), "eta": b.get("eta"), "round": b.get("round"), "job": b.get("job_id"),
                     "final": True}
    elif best is not None:
        best_info = {"score": best, "eta": None, "round": best_round, "job": None, "final": False}
    meta = run_meta(run_id)
    approved = LOGS / f"{run_id}-approved-edits.log"
    return {
        "run_id": run_id, "state": state, "alive": alive, "status": st, "exists": run_exists(run_id),
        "solves": count_solves(run_id), "budget": meta.get("budget"), "rounds_cap": meta.get("rounds"),
        "rounds": rounds, "last_round": last_round, "best": best_info,
        "log": log, "supervisor_log": tail(LOGS / f"{run_id}-supervisor.log", 6),
        "approved_edits": len(approved.read_text(encoding="utf-8", errors="replace").splitlines())
        if approved.is_file() else 0,
        "report": (RESULTS / "runs" / run_id / "report" / "index.html").is_file(),
        "question": (st or {}).get("text") if state == "QUESTION" else None,
        "time": now(),
    }


def list_runs() -> list[dict]:
    names: dict[str, float] = {}
    for p in LOGS.glob("run-*.status"):
        names[p.name[: -len(".status")]] = p.stat().st_mtime
    for p in (RESULTS / "runs").glob("*/checkpoints.sqlite"):
        names.setdefault(p.parent.name, p.stat().st_mtime)
    sups = supervisors()
    for rid in sups:
        names.setdefault(rid, time.time())
    return [{"run_id": n, "mtime": t, "alive": bool(sups.get(n))}
            for n, t in sorted(names.items(), key=lambda kv: kv[1], reverse=True)]


# ------------------------------------------------------------------------------------------- start / stop


class UserError(Exception):
    pass


def num(v, name: str, lo: float | None = None, hi: float | None = None, integer: bool = False):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise UserError(f"{name} must be a number") from None
    if x != x or x in (float("inf"), float("-inf")):
        raise UserError(f"{name} must be a finite number")
    if lo is not None and x < lo:
        raise UserError(f"{name} must be at least {lo:g}")
    if hi is not None and x > hi:
        raise UserError(f"{name} must be at most {hi:g}")
    return int(round(x)) if integer else x


def pair(v, name: str) -> list[float]:
    if not isinstance(v, list) or len(v) != 2:
        raise UserError(f"{name} must be a [min, max] pair")
    lo, hi = num(v[0], name), num(v[1], name)
    if lo > hi:
        raise UserError(f"{name}: min is larger than max")
    return [lo, hi]


def build_run(s: dict) -> tuple[str, list[str], dict]:
    """Turn the page's settings into (run id, supervisor arguments, summary). Writes goal and overrides files."""
    dflt = defaults()
    run_id = str(s.get("run_id", "")).strip()
    if not RUN_ID_RE.match(run_id):
        raise UserError("Run name: 2 to 59 characters, letters, digits, dash or underscore, starting with a letter or digit")
    if run_exists(run_id) or (LOGS / f"{run_id}.status").is_file():
        raise UserError(f"A run named {run_id} already exists. Use Resume, or pick a new name.")
    if supervisors().get(run_id):
        raise UserError(f"A run named {run_id} is already running")

    ch = str(s.get("chamber"))
    chambers = dflt["chambers"]
    if ch not in chambers or not chambers[ch]["usable"]:
        raise UserError("This chamber setup is not usable yet. Pick another one.")
    other = [k for k in chambers if k != ch and chambers[k]["usable"]]
    c = chambers[ch]

    ov: dict = {"backend": {"backend": "mock" if s.get("test_mode") else "comsol"}}
    cons: dict = {}
    sup: dict = {}
    lv = pair(s.get("lv"), "LV range")
    mcp = pair(s.get("mcp"), "MCP front range")
    mesh_v = pair(s.get("mesh_v"), "Mesh range")
    lvd, mcpd, meshd = dflt["lv_range"], dflt["mcp_front"], dflt["mesh_v"]
    if lv[0] < lvd[0] or lv[1] > lvd[1]:
        raise UserError(f"LV range must stay inside {lvd[0]:g} to {lvd[1]:g} V")
    if mcp[0] < mcpd[0] or mcp[1] > mcpd[1]:
        raise UserError(f"MCP front range must stay inside {mcpd[0]:g} to {mcpd[1]:g} V")
    if mesh_v[0] < meshd[0] or mesh_v[1] > meshd[1]:
        raise UserError(f"Mesh range must stay inside {meshd[0]:g} to {meshd[1]:g} V")
    if lv != lvd:
        sup.setdefault("low_voltage", {})["range_V"] = lv
    if mcp != mcpd:
        sup["mcp_front_V"] = mcp
    if mesh_v != meshd:
        sup["mesh_V"] = mesh_v
    if sup:
        cons["supplies"] = sup

    setups: dict = {}
    cset: dict = {}
    for key, cfgkey in (("lens_gap", "lens_gap_mm"), ("mesh_gap", "mesh_gap_mm"), ("z_mcp", "z_mcp_mm")):
        val = pair(s.get(key), key)
        base = c[key]
        if val[0] < base[0] - 1e-9 or val[1] > base[1] + 1e-9:
            raise UserError(f"{key.replace('_', ' ')} must stay inside {base[0]:g} to {base[1]:g} mm for this chamber")
        if val != base:
            cset[cfgkey] = val
    if cset:
        setups[int(ch)] = cset
    for k in other:    # the planner may use only the chosen chamber setup (same method as config/cfg1_only.yaml)
        setups[int(k)] = {"z_mcp_mm": [None, None], "mesh_gap_mm": [None, None], "lens_gap_mm": [None, None]}
    if setups:
        cons["chamber_setups"] = setups
    if cons:
        ov["constraints"] = cons

    opt: dict = {}
    fixed = s.get("ext_fixed")
    if fixed not in (None, ""):
        opt["fixed_extraction_V"] = num(fixed, "Fixed extraction", 0, 2000)
    else:
        emin = num(s.get("ext_min"), "Extraction minimum", 0, 2000)
        emax = s.get("ext_max")
        emax = None if emax in (None, "") else num(emax, "Extraction maximum", 0, 2000)
        if emax is not None and emax < emin:
            raise UserError("Extraction: minimum is larger than maximum")
        if emin != dflt["ext_min"]:
            opt["min_extraction_V"] = emin
        if emax != dflt["ext_max"]:
            opt["max_extraction_V"] = emax
    if opt:
        ov["optimizer"] = opt

    spec: dict = {}
    eta = num(s.get("eta_min"), "Minimum collection", 0.01, 1)
    if eta != dflt["eta_min"]:
        spec["requirements"] = {"eta_min": eta}
    det, launch = {}, {}
    sigma = num(s.get("sigma_mcp"), "MCP resolution", 1, 1000)
    if sigma != dflt["sigma_mcp"]:
        det["sigma_mcp_um"] = sigma
    for key, ck, lo, hi in (("hwhm", "hwhm_deg", 0.5, 60), ("e0", "E0_eV", 0.01, 100), ("mass", "mass_Da", 0.5, 2000)):
        v = num(s.get(key), key, lo, hi)
        if v != dflt[key]:
            launch[ck] = v
    charge = num(s.get("charge"), "Charge", -3, 3, integer=True)
    if charge == 0:
        raise UserError("Charge number cannot be 0")
    if charge != dflt["charge"]:
        launch["charge"] = charge
    if det:
        spec["detector"] = det
    if launch:
        spec["launch"] = launch
    if spec:
        ov["spec"] = spec

    budget = num(s.get("budget"), "Solve budget", 10, 5000, integer=True)
    rounds = num(s.get("rounds"), "Round cap", 1, 200, integer=True)
    round_max = num(s.get("round_max"), "Largest study", 5, 500, integer=True)
    no_imp = num(s.get("no_improve"), "Rounds without gain", 1, 100, integer=True)
    tol = num(s.get("improve_tol"), "Smallest gain", 0, 1)

    if not str(s.get("goal", "")).strip():
        raise UserError("Write a goal for the planner first")
    goal = compose_goal(str(s.get("goal", "")), s.get("hints") or [], bool(s.get("remove_mesh")))

    LOGS.mkdir(exist_ok=True)
    ov_path = LOGS / f"{run_id}-overrides.yaml"
    goal_path = LOGS / f"{run_id}-goal.txt"
    ov_path.write_text("# written by scripts/agent_gui.py\n" + yaml.safe_dump(ov, sort_keys=False), encoding="utf-8")
    goal_path.write_text(goal, encoding="utf-8")
    try:
        from ionopt.config import load_config
        os.chdir(REPO)
        load_config(override_files=[ov_path])
    except Exception as e:      # noqa: BLE001 - show the config loader's own message
        ov_path.unlink(missing_ok=True)
        goal_path.unlink(missing_ok=True)
        raise UserError(f"The config loader rejected these settings: {str(e)[:400]}") from None

    args = [str(Path(__file__).resolve().parent / "supervise_agent_run.py"), run_id,
            "--goal-file", goal_path.relative_to(REPO).as_posix(), "--",
            "--budget", str(budget), "--rounds", str(rounds), "--round-max", str(round_max),
            "--no-improvement-rounds", str(no_imp), "--improvement-tol", f"{tol:g}"]
    if s.get("remove_mesh"):
        args += ["--require-removed", "screen_mesh"]
    args += ["--overrides", ov_path.relative_to(REPO).as_posix()]
    meta = {"run_id": run_id, "budget": budget, "rounds": rounds, "chamber": int(ch), "started": now(),
            "mock": bool(s.get("test_mode")), "overrides": ov, "goal_file": goal_path.name}
    (LOGS / f"{run_id}.gui.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return run_id, args, meta


def compose_goal(goal: str, hints: list, remove_mesh: bool) -> str:
    lines = []
    for h in hints:
        el = str(h.get("el", ""))
        if not re.match(r"^(tip|E[1-9])$", el):
            continue
        state = h.get("state", "auto")
        lo, hi = h.get("lo"), h.get("hi")
        part = []
        if state == "keep":
            part.append("keep it in the layout")
        elif state == "drop":
            part.append("prefer to leave it out")
        if lo not in (None, "") and hi not in (None, ""):
            part.append(f"voltage between {num(lo, el + ' min'):g} and {num(hi, el + ' max'):g} V if it is used")
        elif lo not in (None, ""):
            part.append(f"voltage at least {num(lo, el + ' min'):g} V if it is used")
        elif hi not in (None, ""):
            part.append(f"voltage at most {num(hi, el + ' max'):g} V if it is used")
        if part:
            lines.append(f"- {'Tip' if el == 'tip' else el}: " + "; ".join(part) + ".")
    text = goal.strip()
    if lines:
        text += ("\n\nAuthor hints set in the console (soft guidance, not enforced by the validator; follow them "
                 "unless the numbers clearly argue against):\n" + "\n".join(lines))
    if remove_mesh:
        text += "\n\nThe author requires that every configuration runs without the screen mesh."
    return text


def start_supervisor(run_id: str, extra: list[str] | None = None) -> int:
    return launch_detached([str(Path(__file__).resolve().parent / "supervise_agent_run.py"), run_id, *(extra or [])])


# ------------------------------------------------------------------------------------------- HTTP


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentConsole/1.0"

    def log_message(self, fmt, *args):      # noqa: D102 - keep the terminal quiet
        pass

    # helpers
    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def _file(self, path: Path) -> None:
        if not path.is_file() or path.suffix.lower() not in STATIC_EXT:
            self._send(404, b"not found", "text/plain")
            return
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self._send(200, path.read_bytes(), ctype)

    # GET
    def do_GET(self) -> None:      # noqa: N802
        if not self._host_ok():
            return self._send(403, b"forbidden", "text/plain")
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                html = (WEB / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)
                return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            if u.path in ("/app.js", "/style.css"):
                return self._file(WEB / u.path.lstrip("/"))
            if u.path == "/api/defaults":
                return self._json(defaults())
            if u.path == "/api/runs":
                return self._json({"runs": list_runs()})
            if u.path == "/api/monitor":
                rid = (q.get("run") or [""])[0]
                if not RUN_ID_RE.match(rid):
                    return self._json({"error": "bad run name"}, 400)
                return self._json(monitor(rid))
            if u.path == "/api/goal":
                name = (q.get("file") or [""])[0]
                p = LOGS / name
                if not re.match(r"^run-[A-Za-z0-9_-]+-goal\.txt$", name) or not p.is_file():
                    return self._json({"error": "no such goal"}, 404)
                return self._json({"text": p.read_text(encoding="utf-8")})
            if u.path.startswith("/results/"):
                rel = unquote(u.path[len("/results/"):])
                p = (RESULTS / rel).resolve()
                if RESULTS.resolve() not in p.parents:
                    return self._send(403, b"forbidden", "text/plain")
                return self._file(p)
        except Exception as e:      # noqa: BLE001
            return self._json({"error": f"{type(e).__name__}: {e}"}, 500)
        self._send(404, b"not found", "text/plain")

    # POST
    def do_POST(self) -> None:      # noqa: N802
        if not self._host_ok() or self.headers.get("X-Token") != TOKEN:
            return self._json({"error": "forbidden"}, 403)
        n = int(self.headers.get("Content-Length") or 0)
        if n > 200_000:
            return self._json({"error": "request too large"}, 413)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            path = urlparse(self.path).path
            if path == "/api/check":
                run_id, args, meta = build_run({**body, "run_id": body.get("run_id") or "check-only"})
                # a check must leave nothing behind
                for suffix in ("-overrides.yaml", "-goal.txt", ".gui.json"):
                    (LOGS / f"{run_id}{suffix}").unlink(missing_ok=True)
                return self._json({"ok": True})
            if path == "/api/start":
                run_id, args, meta = build_run(body)
                pid = start_supervisor_args(args)
                return self._json({"ok": True, "run_id": run_id, "pid": pid})
            rid = str(body.get("run_id", ""))
            if not RUN_ID_RE.match(rid):
                raise UserError("bad run name")
            if path == "/api/resume":
                if not run_exists(rid):
                    raise UserError(f"No run named {rid} to resume")
                if supervisors(0).get(rid):
                    raise UserError(f"{rid} is already running")
                return self._json({"ok": True, "pid": start_supervisor(rid)})
            if path == "/api/answer":
                text = " ".join(str(body.get("text", "")).split())[:2000]
                if not text:
                    raise UserError("Write an answer first")
                if supervisors(0).get(rid):
                    raise UserError(f"{rid} is running; the planner is not waiting for an answer")
                return self._json({"ok": True, "pid": start_supervisor(rid, ["--answer", text])})
            if path == "/api/stop":
                pids = supervisors(0).get(rid) or []
                if not pids:
                    raise UserError(f"{rid} is not running")
                kill_run_processes(pids)
                (LOGS / f"{rid}.status").write_text(json.dumps(
                    {"state": "STOPPED", "time": now(), "run_id": rid, "reason": "stopped from the console"}, indent=1),
                    encoding="utf-8")
                return self._json({"ok": True})
            raise UserError("unknown action")
        except UserError as e:
            return self._json({"error": str(e)}, 400)
        except Exception as e:      # noqa: BLE001
            return self._json({"error": f"{type(e).__name__}: {e}"}, 500)


def start_supervisor_args(args: list[str]) -> int:
    return launch_detached(args)


def pick_port(start: int) -> int:
    import socket
    for p in range(start, start + 20):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    raise SystemExit("no free port found")


def open_window(url: str) -> None:
    """Prefer an app-style window (no tabs or address bar) in Edge or Chrome; else the default browser."""
    candidates = [os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("PROGRAMFILES", ""),
                  os.environ.get("LOCALAPPDATA", "")]
    exes = []
    for base in candidates:
        exes += [Path(base) / "Microsoft/Edge/Application/msedge.exe", Path(base) / "Google/Chrome/Application/chrome.exe"]
    for exe in exes:
        if exe.is_file():
            subprocess.Popen([str(exe), f"--app={url}", "--window-size=1500,960"], creationflags=NO_WINDOW)
            return
    webbrowser.open(url)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true", help="do not open a window")
    a = ap.parse_args()
    os.chdir(REPO)
    port = pick_port(a.port)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Ion beam agent console: {url}   (Ctrl+C stops the console; runs keep going)")
    if not a.no_open:
        threading.Timer(0.6, open_window, args=(url,)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
