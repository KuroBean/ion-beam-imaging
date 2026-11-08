"""Command-line interface (plan 9.11). Every command accepts --set key=value overrides."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

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


COMMANDS = {
    "config-check": (cmd_config_check, "load and validate all config, list TBD keys", None),
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
