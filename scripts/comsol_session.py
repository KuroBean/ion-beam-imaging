"""Helpers for driving the local COMSOL 5.5 install from Python via MPh.

COMSOL 5.5 ships a Java 8 JVM, so this environment needs:
  * jpype1 < 1.6  (JPype 1.6+ refuses to start a Java 8 JVM)
  * the bundled JRE's bin directory on PATH, so jvm.dll can find msvcr120.dll
"""
import os
import time
from pathlib import Path

COMSOL_ROOT = Path(r"C:\Program Files\COMSOL\COMSOL55\Multiphysics")
JRE_BIN = COMSOL_ROOT / "java" / "win64" / "jre" / "bin"
PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_FILE = PROJECT_DIR / "lens8newMCP_ks_v2_multi_flange_config_11_2.mph"

if str(JRE_BIN) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(JRE_BIN) + os.pathsep + os.environ.get("PATH", "")

import mph  # noqa: E402  (must come after the PATH fix)


def start(cores=None):
    """Start a stand-alone COMSOL session (defaults to all cores)."""
    t = time.time()
    client = mph.start(cores=cores)
    print(f"COMSOL {client.version} started in {time.time() - t:.1f} s", flush=True)
    return client


def load(client, path=MODEL_FILE):
    t = time.time()
    model = client.load(str(path))
    print(f"Loaded {Path(path).name} in {time.time() - t:.1f} s", flush=True)
    return model
