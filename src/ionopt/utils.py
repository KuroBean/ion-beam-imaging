"""Small shared helpers: timestamps, hashes, git commit, JSON I/O."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import socket
import subprocess
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def hostname() -> str:
    return socket.gethostname()


def sha256_file(path: Path | str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def git_commit(repo: Path | str | None = None) -> str | None:
    """HEAD commit hash, with '+dirty' if tracked files have uncommitted changes."""
    try:
        cwd = str(repo) if repo else None
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True,
                             timeout=10, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=cwd,
                               capture_output=True, text=True, timeout=10).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return None


def _clean(o: Any) -> Any:
    """Make data JSON-safe: NaN/inf -> None, numpy scalars -> python."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        try:
            o = o.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def write_json(path: Path | str, data: Any) -> None:
    Path(path).write_text(json.dumps(_clean(data), indent=2), encoding="utf-8")


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
