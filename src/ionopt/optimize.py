"""Bayesian optimization over supply channel voltages and positions for one configuration (plan 9.9).

Search space (bounds from constraints.yaml for the configuration's chamber setup):
  * voltages of the LV channels used by the wiring, the MCP-front and mesh HV ports
  * z_mcp and mesh_gap (fixed when their range has min == max)
  * the front offset (from E1) of each plate the configuration moves (conf.moved), in beam order, as a
    fraction of the window that keeps constraints.electrodes.min_gap_mm to both neighbours
  * lens_gap (places the stack), as a fraction of its feasible range so the stack always stays
    upstream of the mesh
  * with pre-acceleration, E1 as a fraction of its accelerating range (q (V_tip - V_E1) >= min_extraction_V)
  * with optimizer.no_mirror, every other lens channel and the mesh as a fraction of the range below
    the tip potential (above it for q < 0), and the tip itself on the passing side of ground (the
    deflectors, unwired plates and the chamber are grounded): ions keep at least E0 everywhere

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
from .electrodes import (OFFSET, check_structure, face_shift, has_screen_mesh, layout_problems, mcp_max_from_e1,
                         rear_reach, stack_layout, used_lv_channels)
from .jobs import build_job
from .runlog import RunLog
from .variants import load_variant

log = logging.getLogger(__name__)
EPS_M = 1e-9


def _rng(cfg: Config, key: str) -> list[float]:
    return cfg.require(key)


def _rear_setup(cfg: Config, conf: ConfigurationDef, parts: list[dict]
                ) -> tuple[str, dict[str, float], float | None]:
    """Rear obstacle ("mesh" or "mcp"), each part's reach to its plane (min gap included), and the largest
    z_mcp - lens_gap when the MCP sits on the rods (None otherwise)."""
    rear = "mesh" if has_screen_mesh(cfg, conf.variant_id) else "mcp"
    g = (cfg.constraints.electrodes.min_gap_mm or 0.0) * units.MM
    return rear, {e["name"]: rear_reach(e["profile"], rear) + g for e in parts}, mcp_max_from_e1(cfg, conf.cfg)


def _end_room_max(z_mcp_hi: float, gap_lo: float, lens_lo: float, rear: str, mcp_max: float | None) -> float:
    """Largest offset (m, from the E1 front face) the rear reference plane can have."""
    gap = gap_lo if rear == "mesh" else 0.0
    room = z_mcp_hi - gap - lens_lo
    if mcp_max is not None:
        room = min(room, mcp_max - gap)
    return room - EPS_M


def offset_windows(parts: list[dict], moved: list[str], bounds: dict[str, tuple[float, float]], gap: float,
                   end_room: float, max_offset: float | None, placed: dict[str, float] | None = None,
                   reach: dict[str, float] | None = None) -> dict[str, tuple[float, float]]:
    """Allowed front offsets (m, from the E1 front face) of the moved plates not yet placed.

    parts: present stack parts at lens_gap 0, as built (stack_layout); bounds: plate -> (lo, hi) m;
    end_room: offset of the rear obstacle's reference plane (mesh or MCP plane - smallest lens_gap);
    reach: part -> room it needs in front of that plane, from its front face (min gap included; default
    its full length); placed: plates already sampled (beam order). Lower limits come from the upstream
    neighbours, upper limits from the downstream ones (at their own upper limits) and the end, so any
    value in a window leaves room for every later plate.
    """
    placed = placed or {}
    names = [e["name"] for e in parts]
    front = {e["name"]: e["z_front_m"] for e in parts}
    ext = {e["name"]: e["z_back_m"] - e["z_front_m"] for e in parts}
    prof = {e["name"]: e["profile"] for e in parts}
    lo: dict[str, float] = {}
    hi: dict[str, float] = {}
    for i, n in enumerate(names):
        if n in placed or n not in moved:
            lo[n] = placed.get(n, front[n])
            continue
        v = bounds.get(n, (-math.inf, math.inf))[0]
        if i > 0:
            u = names[i - 1]
            v = max(v, lo[u] + gap - face_shift(prof[u], prof[n]))
        lo[n] = v
    for i in reversed(range(len(names))):
        n = names[i]
        if n in placed or n not in moved:
            hi[n] = placed.get(n, front[n])
            continue
        v = min(bounds.get(n, (-math.inf, math.inf))[1], end_room - (reach[n] if reach else ext[n]))
        if max_offset is not None:
            v = min(v, max_offset - ext[n])
        if i + 1 < len(names):
            d = names[i + 1]
            v = min(v, hi[d] - gap + face_shift(prof[n], prof[d]))
        hi[n] = v
    return {n: (lo[n], hi[n]) for n in names if n in moved and n not in placed}


@dataclass
class SearchSpace:
    conf: ConfigurationDef
    channels: dict[str, tuple[float, float]]               # V
    z_mcp: tuple[float, float]                             # m
    mesh_gap: tuple[float, float]                          # m
    lens_gap: tuple[float, float]                          # m
    stack_length: float                                    # m, E1 front face to the closest allowed rear plane
                                                           # (moved plates at their lowest offsets, min gap included)
    names: list[str] = field(default_factory=list)
    # extraction rule (pre-acceleration on): q (V_tip - V_E1) >= min_extraction (V)
    tip_ch: str | None = None
    e1_ch: str | None = None
    q_sign: int = 1
    min_extraction: float | None = None
    fixed_extraction: float | None = None  # optimizer.fixed_extraction_V: E1 follows the tip at this q (V_tip - V_E1)
    max_extraction: float | None = None    # optimizer.max_extraction_V: upper limit on q (V_tip - V_E1)
    # no-mirror rule: channels in `capped` stay on the passing side of V_tip
    mirror_tip: str | None = None          # tip channel (None: tip grounded)
    capped: list[str] = field(default_factory=list)
    # moved plates (beam order): static offset windows (m), present parts as built at lens_gap 0
    offsets: dict[str, tuple[float, float]] = field(default_factory=dict)
    variant_vars: dict[str, tuple[float, float]] = field(default_factory=dict)   # variant lengths (m)
    parts: list[dict] = field(default_factory=list)
    min_gap: float = 0.0
    max_offset: float | None = None
    # what the stack must clear at the back: "mesh" (plane z_mcp - mesh_gap) or, without a screen mesh, "mcp"
    # (plane z_mcp); reach = part -> room it needs in front of that plane from its front face (m, min gap included)
    rear: str = "mesh"
    reach: dict[str, float] = field(default_factory=dict)
    # MCP on the tie rods (chamber_setups.<n>.mcp_rod_margin_mm): z_mcp - lens_gap <= mcp_max (m); then z_mcp
    # is sampled first, mesh_gap within the room it leaves (u_mesh_gap) and lens_gap from z_mcp - mcp_max up
    mcp_max: float | None = None
    gap_dependent: bool = False

    @staticmethod
    def raw_ranges(cfg: Config, conf: ConfigurationDef) -> dict[str, tuple[float, float]]:
        """Ranges from constraints.yaml for this configuration, before the extraction and no-mirror rules.

        Keys: the LV channels used by the wiring and the MCP-front / mesh HV ports (V), and
        lens_gap_mm, mesh_gap_mm, z_mcp_mm, e<k>_offset_mm for moved plates (mm). These are the variable
        names planner bounds use.
        """
        problems = check_structure(cfg, conf.cfg, conf.wiring, conf.removed, conf.variant_id, conf.variant_settings)
        if conf.cfg in cfg.constraints.chamber_setups:
            problems += layout_problems(cfg, conf.cfg, conf.removed, {})
            problems += [f"cannot move {m}: {'removed' if m in conf.removed else 'not movable'}" for m in conf.moved
                         if m in conf.removed or m not in cfg.constraints.electrodes.movable]
        if problems:
            raise ConfigError(f"configuration '{conf.config_id}' is invalid:\n  " + "\n  ".join(problems))
        s = cfg.constraints.supplies
        out: dict[str, tuple[float, float]] = {}
        for ch in used_lv_channels(cfg, conf.wiring):
            out[ch] = tuple(_rng(cfg, "constraints.supplies.low_voltage.range_V"))
        hv = s.high_voltage.range_V
        for role, key in (("mcp_front", "constraints.supplies.mcp_front_V"), ("mesh", "constraints.supplies.mesh_V")):
            lo, hi = _rng(cfg, key)
            if range_known(hv):
                lo, hi = max(lo, hv[0]), min(hi, hv[1])
            out[s.hv_port(role)] = (lo, hi)
        ck = f"constraints.chamber_setups.{conf.cfg}"
        lo_g, hi_g = _rng(cfg, f"{ck}.mesh_gap_mm")
        lo_g = max(lo_g, cfg.require("constraints.mesh.min_gap_to_mcp_mm"))
        if lo_g > hi_g:
            raise ConfigError(f"{ck}.mesh_gap_mm upper bound is below constraints.mesh.min_gap_to_mcp_mm")
        out["lens_gap_mm"] = tuple(_rng(cfg, f"{ck}.lens_gap_mm"))
        out["mesh_gap_mm"] = (lo_g, hi_g)
        out["z_mcp_mm"] = tuple(_rng(cfg, f"{ck}.z_mcp_mm"))
        if conf.moved:
            el = cfg.constraints.electrodes
            parts = stack_layout(cfg, conf.cfg, 0.0, conf.removed)
            rear, reach, mcp_max = _rear_setup(cfg, conf, parts)
            end = _end_room_max(out["z_mcp_mm"][1] * units.MM, lo_g * units.MM, out["lens_gap_mm"][0] * units.MM,
                                rear, mcp_max)
            w = offset_windows(parts, _beam_order(parts, conf.moved), {}, el.min_gap_mm * units.MM, end,
                               None if el.max_offset_mm is None else el.max_offset_mm * units.MM, reach=reach)
            for n, (lo, hi) in w.items():
                if lo > hi + EPS_M:
                    raise ConfigError(f"configuration '{conf.config_id}': no room to move {n} "
                                      f"(electrodes.min_gap_mm to its neighbours)")
                out[f"{n}{OFFSET}_mm"] = (lo / units.MM, hi / units.MM)
        var = load_variant(cfg, conf.variant_id)
        if var is not None:
            for x in var.variables():
                out[f"{x.name}_mm"] = (float(x.range[0]), float(x.range[1]))
                item = cfg.inventory.get(x.inventory_item) if x.inventory_item else None
                if item is not None and item.replaces in var.removed_base:
                    # dimension of a part the variant has since removed (e.g. the opening of a mesh that is
                    # gone): it no longer reaches the geometry, so hold it at its as-built value
                    v = float(x.as_built if x.as_built is not None else x.range[0])
                    out[f"{x.name}_mm"] = (v, v)
            if "screen_mesh" in var.removed_base:      # no mesh: its voltage and gap do nothing
                lo, hi = out[s.hv_port("mesh")]
                v = min(max(0.0, lo), hi)
                out[s.hv_port("mesh")] = (v, v)
                out["mesh_gap_mm"] = (out["mesh_gap_mm"][0], out["mesh_gap_mm"][0])
        return out

    @classmethod
    def from_config(cls, cfg: Config, conf: ConfigurationDef,
                    bounds: dict[str, tuple[float, float]] | None = None) -> "SearchSpace":
        """Search space of a configuration; `bounds` (planner, same keys as raw_ranges) narrow the
        constraint ranges first, then the extraction and no-mirror rules apply to the result."""
        raw = cls.raw_ranges(cfg, conf)
        for k, (lo, hi) in (bounds or {}).items():
            if k not in raw:
                raise ConfigError(f"'{conf.config_id}': bound on unknown variable '{k}' (known: {sorted(raw)})")
            r_lo, r_hi = raw[k]
            n_lo, n_hi = max(r_lo, lo), min(r_hi, hi)
            if n_lo > n_hi:
                raise ConfigError(f"'{conf.config_id}': bound {k} = [{lo}, {hi}] does not overlap the allowed "
                                  f"range [{r_lo}, {r_hi}]")
            raw[k] = (n_lo, n_hi)
        mm = lambda r: (r[0] * units.MM, r[1] * units.MM)  # noqa: E731
        var = load_variant(cfg, conf.variant_id)
        vnames = {f"{x.name}_mm": x.name for x in var.variables()} if var else {}
        chan = {k: v for k, v in raw.items() if not k.endswith("_mm")}
        parts = stack_layout(cfg, conf.cfg, 0.0, conf.removed)
        el = cfg.constraints.electrodes
        rear, reach, mcp_max = _rear_setup(cfg, conf, parts)
        sp = cls(conf=conf, channels=chan, z_mcp=mm(raw["z_mcp_mm"]), mesh_gap=mm(raw["mesh_gap_mm"]),
                 lens_gap=mm(raw["lens_gap_mm"]), stack_length=0.0,
                 parts=parts, min_gap=(el.min_gap_mm or 0.0) * units.MM,
                 max_offset=None if el.max_offset_mm is None else el.max_offset_mm * units.MM,
                 variant_vars={n: mm(raw[k]) for k, n in vnames.items()}, rear=rear, reach=reach, mcp_max=mcp_max)
        sp.stack_length = sp.stack_reach({})
        if conf.moved:
            b = {n: mm(raw[f"{n}{OFFSET}_mm"]) for n in conf.moved}
            end = _end_room_max(sp.z_mcp[1], sp.mesh_gap[0], sp.lens_gap[0], rear, mcp_max)
            sp.offsets = offset_windows(parts, _beam_order(parts, conf.moved), b, sp.min_gap, end, sp.max_offset,
                                        reach=reach)
            for n, (lo, hi) in sp.offsets.items():
                if lo > hi + EPS_M:
                    raise ConfigError(f"'{conf.config_id}': the bounds leave no room for {n} "
                                      f"(electrodes.min_gap_mm to its neighbours)")
            sp.offsets = {n: (lo, max(lo, hi)) for n, (lo, hi) in sp.offsets.items()}
            sp.stack_length = sp.stack_reach({})
        sp.fixed_extraction = cfg.optimizer.fixed_extraction_V
        sp.max_extraction = cfg.optimizer.max_extraction_V
        if cfg.spec.launch.preaccel or sp.fixed_extraction is not None or sp.max_extraction is not None:
            sp._extraction_rule(conf.wiring, 1 if cfg.spec.launch.charge > 0 else -1, cfg.optimizer.min_extraction_V)
        if cfg.optimizer.no_mirror:
            sp._mirror_rule(conf.wiring, 1 if cfg.spec.launch.charge > 0 else -1,
                            cfg.constraints.supplies.hv_port("mcp_front"))
        what = "screen mesh" if rear == "mesh" else "MCP"
        gap_lo, gap_hi = (sp.mesh_gap if rear == "mesh" else (0.0, 0.0))
        if mcp_max is None:
            # MCP held by the chamber: the worst case (mesh closest to the tip, stack furthest out) must still fit
            if sp.lens_gap[0] + sp.stack_length >= sp.z_mcp[0] - gap_hi - EPS_M:
                raise ConfigError(f"configuration '{conf.config_id}': the lens stack does not fit in front of the "
                                  f"{what} even at the smallest lens_gap, z_mcp and largest mesh_gap")
            return sp
        # MCP on the rods: it goes behind the stack (+ mesh gap) and no further than mcp_max behind E1
        if sp.stack_length + gap_lo > mcp_max - 2 * EPS_M:
            raise ConfigError(f"configuration '{conf.config_id}': the lens stack does not fit on the rods in front of "
                              f"the {what} (needs {(sp.stack_length + gap_lo) / units.MM:.2f} mm behind the E1 front "
                              f"face, the MCP may be at most {mcp_max / units.MM:.2f} mm)")
        lo = max(sp.z_mcp[0], sp.lens_gap[0] + sp.stack_length + gap_lo + 4 * EPS_M)
        hi = min(sp.z_mcp[1], sp.lens_gap[1] + mcp_max)
        if lo > hi:
            raise ConfigError(f"configuration '{conf.config_id}': no MCP position fits behind the stack within "
                              f"z_mcp {raw['z_mcp_mm']} mm and lens_gap {raw['lens_gap_mm']} mm")
        sp.z_mcp = (lo, hi)
        sp.gap_dependent = rear == "mesh" and gap_hi - gap_lo > 1e-12
        return sp

    def variable_ranges(self) -> dict[str, tuple[float, float]]:
        """Static range of every variable after the rules (V, mm), keyed like raw_ranges. E1 and the
        capped channels are further limited by the sampled tip voltage at each trial."""
        out = dict(self.channels)
        out["lens_gap_mm"] = (self.lens_gap[0] / units.MM, self.lens_gap[1] / units.MM)
        out["mesh_gap_mm"] = (self.mesh_gap[0] / units.MM, self.mesh_gap[1] / units.MM)
        out["z_mcp_mm"] = (self.z_mcp[0] / units.MM, self.z_mcp[1] / units.MM)
        for n, (lo, hi) in self.offsets.items():
            out[f"{n}{OFFSET}_mm"] = (lo / units.MM, hi / units.MM)
        for n, (lo, hi) in self.variant_vars.items():
            out[f"{n}_mm"] = (lo / units.MM, hi / units.MM)
        return out

    # ---- moved plates
    def stack_reach(self, offsets: dict[str, float]) -> float:
        """Closest allowed rear plane (m from the E1 front face) with these plate offsets; moved plates not
        given sit at their lowest offsets."""
        full = {n: lo for n, (lo, _) in self.offsets.items()}
        full.update(offsets)
        shift = {n: full[n] - e["z_front_m"] for e in self.parts for n in [e["name"]] if n in full}
        return max(e["z_front_m"] + shift.get(e["name"], 0.0) + self.reach[e["name"]] for e in self.parts)

    def z_ref(self, z_mcp: float, gap: float) -> float:
        """Reference plane of the rear obstacle (m): the mesh plane, or the MCP face without a mesh."""
        return z_mcp - gap if self.rear == "mesh" else z_mcp

    def lens_gap_min(self, z_mcp: float) -> float:
        """Smallest lens_gap at this MCP position (MCP on the rods: at most mcp_max behind E1)."""
        lo = self.lens_gap[0]
        return lo if self.mcp_max is None else max(lo, z_mcp - self.mcp_max)

    def mesh_gap_max(self, z_mcp: float) -> float:
        """Largest mesh_gap at this MCP position that still leaves room for the stack."""
        hi = self.mesh_gap[1]
        if self.gap_dependent:
            hi = min(hi, z_mcp - self.lens_gap_min(z_mcp) - self.stack_length - 2 * EPS_M)
        return max(self.mesh_gap[0], hi)

    def window(self, name: str, placed: dict[str, float], z_ref: float, lens_lo: float) -> tuple[float, float]:
        """Offset window of a moved plate given the plates placed before it, the rear plane and the
        smallest lens_gap."""
        lo, hi = offset_windows(self.parts, list(self.offsets), self.offsets, self.min_gap,
                                z_ref - lens_lo - EPS_M, self.max_offset, placed, reach=self.reach)[name]
        return lo, max(lo, hi)

    def contains(self, channels: dict[str, float], positions: dict[str, float], tol: float = 1e-9) -> bool:
        """True if a (channels, positions) point lies inside this space, rules included (warm starts)."""
        if set(channels) != set(self.channels):
            return False
        for ch, v in channels.items():
            lo, hi = self._sub_range(ch, channels) if self._dependent(ch) else self.channels[ch]
            if not (lo - tol <= v <= hi + tol):
                return False
        z, g, lg = positions["z_mcp"], positions["mesh_gap"], positions["lens_gap"]
        ok = (self.z_mcp[0] - tol <= z <= self.z_mcp[1] + tol and self.mesh_gap[0] - tol <= g <= self.mesh_gap_max(z) + tol)
        offs = {k[: -len(OFFSET)]: v for k, v in positions.items() if k.endswith(OFFSET)}
        if set(offs) != set(self.offsets):
            return False
        for n, (lo, hi) in self.variant_vars.items():
            if n not in positions or not (lo - tol <= positions[n] <= hi + tol):
                return False
        z_ref, lens_lo = self.z_ref(z, g), self.lens_gap_min(z)
        placed: dict[str, float] = {}
        for n in self.offsets:
            lo, hi = self.window(n, placed, z_ref, lens_lo)
            if not (lo - tol <= offs[n] <= hi + tol):
                return False
            placed[n] = offs[n]
        return ok and lens_lo - tol <= lg <= self.lens_gap_max(z_ref, placed) + tol

    def _extraction_rule(self, wiring: dict[str, str], q_sign: int, u_min: float) -> None:
        """Restrict the tip / E1 channel ranges so that q (V_tip - V_E1) >= u_min is always possible."""
        tip, e1 = wiring.get("tip"), wiring.get("e1")
        tip = tip if tip in self.channels else None
        e1 = e1 if e1 in self.channels else None
        if tip is None and e1 is None or tip == e1:
            raise ConfigError(f"configuration '{self.conf.config_id}': tip and E1 are at the same potential, so "
                              f"there is no extraction field (pre-acceleration needs V_tip != V_E1)")
        self.tip_ch, self.e1_ch, self.q_sign, self.min_extraction = tip, e1, q_sign, u_min
        if self.fixed_extraction is not None:
            self._fixed_extraction_rule(tip, e1, q_sign, u_min)
            return
        u_max = self.max_extraction if self.max_extraction is not None else math.inf
        if u_max < u_min:
            raise ConfigError(f"optimizer.max_extraction_V = {u_max} V is below optimizer.min_extraction_V = {u_min} V")
        if tip is not None:
            lo, hi = self.channels[tip]
            e_lo, e_hi = self.channels[e1] if e1 else (0.0, 0.0)
            # positive ions: min(V_E1) + u_min <= V_tip <= max(V_E1) + u_max; negative: mirrored
            lo, hi = ((max(lo, e_lo + u_min), min(hi, e_hi + u_max)) if q_sign > 0
                      else (max(lo, e_lo - u_max), min(hi, e_hi - u_min)))
            if lo > hi:
                raise ConfigError(f"'{self.conf.config_id}': no tip voltage gives an extraction field in "
                                  f"[{u_min:g}, {u_max:g}] V")
            self.channels[tip] = (lo, hi)
        elif e1 is not None:        # grounded tip
            lo, hi = self.channels[e1]
            lo, hi = (max(lo, -u_max), min(hi, -u_min)) if q_sign > 0 else (max(lo, u_min), min(hi, u_max))
            if lo > hi:
                raise ConfigError(f"'{self.conf.config_id}': no E1 voltage gives an accelerating field at a grounded tip")
            self.channels[e1] = (lo, hi)

    def _fixed_extraction_rule(self, tip: str | None, e1: str | None, q_sign: int, u_min: float) -> None:
        """optimizer.fixed_extraction_V: q (V_tip - V_E1) = dV exactly. E1 follows the tip (or a grounded
        partner sets the other one to a constant), so only one of the two is a variable."""
        dv = self.fixed_extraction
        if dv < u_min:
            raise ConfigError(f"optimizer.fixed_extraction_V = {dv} V is below optimizer.min_extraction_V = {u_min} V")
        s = q_sign * dv                                   # V_tip - V_E1
        cid = self.conf.config_id
        if tip is not None:
            lo, hi = self.channels[tip]
            e_lo, e_hi = self.channels[e1] if e1 else (0.0, 0.0)
            lo, hi = max(lo, e_lo + s), min(hi, e_hi + s)
            if lo > hi:
                raise ConfigError(f"'{cid}': no tip voltage keeps E1 = V_tip - ({s:g} V) inside its channel range")
            self.channels[tip] = (lo, hi)
            if e1 is not None:                            # sampled range of E1 (it is set from the tip)
                self.channels[e1] = (lo - s, hi - s)
        else:                                             # grounded tip: E1 is a constant
            lo, hi = self.channels[e1]
            if not lo <= -s <= hi:
                raise ConfigError(f"'{cid}': E1 = {-s:g} V (grounded tip, fixed extraction) is outside its range")
            self.channels[e1] = (-s, -s)

    def _mirror_rule(self, wiring: dict[str, str], q_sign: int, mcp_port: str) -> None:
        """No ion mirrors: lens channels and the mesh on the passing side of the tip potential, the tip on the
        passing side of ground (deflectors, unwired plates and the chamber are grounded)."""
        tip = wiring.get("tip")
        self.mirror_tip = tip if tip in self.channels else None
        self.q_sign = q_sign
        self.capped = [ch for ch in self.channels if ch not in (self.mirror_tip, self.e1_ch, mcp_port)]
        if self.mirror_tip:
            lo, hi = self.channels[self.mirror_tip]
            lo, hi = (max(lo, 0.0), hi) if q_sign > 0 else (lo, min(hi, 0.0))
            if lo > hi:
                raise ConfigError(f"'{self.conf.config_id}': the tip range {self.channels[self.mirror_tip]} has no "
                                  f"voltage on the passing side of the grounded parts")
            self.channels[self.mirror_tip] = (lo, hi)
            if self.fixed_extraction is not None and self.e1_ch is not None and self.tip_ch == self.mirror_tip:
                s = q_sign * self.fixed_extraction            # E1 follows the tip: keep its range in step
                self.channels[self.e1_ch] = (lo - s, hi - s)
        t_lo, t_hi = self.channels[self.mirror_tip] if self.mirror_tip else (0.0, 0.0)
        for ch in self.capped:
            lo, hi = self.channels[ch]
            if (q_sign > 0 and lo > t_hi) or (q_sign < 0 and hi < t_lo):
                raise ConfigError(f"'{self.conf.config_id}': channel {ch} cannot stay "
                                  f"{'below' if q_sign > 0 else 'above'} the tip potential for any tip voltage")

    def _sub_range(self, ch: str, channels: dict[str, float]) -> tuple[float, float]:
        """Sampling range of a dependent channel (E1 or a capped channel) given the tip voltage."""
        lo, hi = self.channels[ch]
        if ch == self.e1_ch and self.tip_ch is not None and self.fixed_extraction is not None:
            v = channels[self.tip_ch] - self.q_sign * self.fixed_extraction
            return v, v
        if ch == self.e1_ch and self.tip_ch is not None:
            vt, u = channels[self.tip_ch], self.min_extraction
            u_max = self.max_extraction if self.max_extraction is not None else math.inf
            lo, hi = ((max(lo, vt - u_max), min(hi, vt - u)) if self.q_sign > 0
                      else (max(lo, vt + u), min(hi, vt + u_max)))
        elif ch in self.capped:
            m = channels[self.mirror_tip] if self.mirror_tip else 0.0
            lo, hi = (lo, min(hi, m)) if self.q_sign > 0 else (max(lo, m), hi)
        return lo, max(lo, hi)

    def _dependent(self, ch: str) -> bool:
        return (ch == self.e1_ch and self.tip_ch is not None) or ch in self.capped

    def to_params(self, channels: dict[str, float], positions: dict[str, float]) -> dict[str, float]:
        """Optuna parameters that reproduce these channels/positions (inverse of suggest; values clipped)."""
        def frac(v, lo, hi):
            return min(1.0, max(0.0, (v - lo) / (hi - lo)))

        def clip(v, rng):
            return min(max(v, rng[0]), rng[1])

        p = {}
        indep = {ch: clip(v, self.channels[ch]) for ch, v in channels.items()
                 if ch in self.channels and not self._dependent(ch)}
        for ch, (lo, hi) in self.channels.items():
            if hi - lo <= 1e-12 or ch not in channels:
                continue
            if self._dependent(ch):
                lo, hi = self._sub_range(ch, indep)
                if hi - lo > 1e-12:
                    p[f"u_{ch}"] = frac(channels[ch], lo, hi)
            else:
                p[ch] = indep[ch]
        z_mcp = clip(positions["z_mcp"], self.z_mcp)
        gap = clip(positions["mesh_gap"], (self.mesh_gap[0], self.mesh_gap_max(z_mcp)))
        if self.z_mcp[1] - self.z_mcp[0] > 1e-12:
            p["z_mcp_mm"] = z_mcp / units.MM
        if self.gap_dependent:
            g_lo, g_hi = self.mesh_gap[0], self.mesh_gap_max(z_mcp)
            if g_hi - g_lo > 1e-12:
                p["u_mesh_gap"] = frac(gap, g_lo, g_hi)
        elif self.mesh_gap[1] - self.mesh_gap[0] > 1e-12:
            p["mesh_gap_mm"] = gap / units.MM
        for n, (lo, hi) in self.variant_vars.items():
            if hi - lo > 1e-12:
                p[f"{n}_mm"] = clip(positions.get(n, lo), (lo, hi)) / units.MM
        z_ref, lens_lo = self.z_ref(z_mcp, gap), self.lens_gap_min(z_mcp)
        placed: dict[str, float] = {}
        for n in self.offsets:
            lo, hi = self.window(n, placed, z_ref, lens_lo)
            v = clip(positions.get(f"{n}{OFFSET}", lo), (lo, hi))
            if hi - lo > 1e-12:
                p[f"u_{n}{OFFSET}"] = frac(v, lo, hi)
            placed[n] = v
        lo, hi = lens_lo, self.lens_gap_max(z_ref, placed)
        if hi - lo > 1e-12:
            p["u_lens_gap"] = frac(positions["lens_gap"], lo, hi)
        return p

    def lens_gap_max(self, z_ref: float, offsets: dict[str, float] | None = None) -> float:
        """Largest lens_gap that keeps the whole stack min_gap in front of the rear plane (mesh or MCP)."""
        return min(self.lens_gap[1], z_ref - self.stack_reach(offsets or {}) - EPS_M)

    # ---- optuna
    def suggest(self, trial: optuna.Trial) -> tuple[dict[str, float], dict[str, float]]:
        def f(name, lo, hi):
            return lo if hi - lo <= 1e-12 else trial.suggest_float(name, lo, hi)

        channels = {}
        for ch, (lo, hi) in self.channels.items():
            if not self._dependent(ch):
                channels[ch] = f(ch, lo, hi)
        indep = dict(channels)
        for ch, (lo0, hi0) in self.channels.items():
            if self._dependent(ch) and hi0 - lo0 > 1e-12:
                # E1 and capped channels as a fraction of their range given the tip (cf. lens_gap)
                lo, hi = self._sub_range(ch, indep)
                channels[ch] = lo if hi - lo <= 1e-12 else lo + trial.suggest_float(f"u_{ch}", 0.0, 1.0) * (hi - lo)
            elif self._dependent(ch):
                channels[ch] = lo0
        channels = {ch: channels[ch] for ch in self.channels}   # keep the channel order
        z_mcp = f("z_mcp_mm", self.z_mcp[0] / units.MM, self.z_mcp[1] / units.MM) * units.MM
        if self.gap_dependent:     # MCP on the rods: mesh_gap as a fraction of the room the stack leaves
            lo, hi = self.mesh_gap[0], self.mesh_gap_max(z_mcp)
            gap = lo if hi - lo <= 1e-12 else lo + trial.suggest_float("u_mesh_gap", 0.0, 1.0) * (hi - lo)
        else:
            gap = f("mesh_gap_mm", self.mesh_gap[0] / units.MM, self.mesh_gap[1] / units.MM) * units.MM
        variant = {n: f(f"{n}_mm", lo / units.MM, hi / units.MM) * units.MM
                   for n, (lo, hi) in self.variant_vars.items()}
        z_ref, lens_lo = self.z_ref(z_mcp, gap), self.lens_gap_min(z_mcp)
        # moved plates in beam order, each as a fraction of the window its neighbours leave
        placed: dict[str, float] = {}
        for n in self.offsets:
            lo, hi = self.window(n, placed, z_ref, lens_lo)
            placed[n] = lo if hi - lo <= 1e-12 else lo + trial.suggest_float(f"u_{n}{OFFSET}", 0.0, 1.0) * (hi - lo)
        # lens_gap as a fraction of its feasible range, so the stack never reaches the mesh / MCP
        lo, hi = lens_lo, self.lens_gap_max(z_ref, placed)
        lens_gap = lo if hi - lo <= 1e-12 else lo + trial.suggest_float("u_lens_gap", 0.0, 1.0) * (hi - lo)
        return channels, {"lens_gap": lens_gap, "z_mcp": z_mcp, "mesh_gap": gap,
                          **{f"{n}{OFFSET}": v for n, v in placed.items()}, **variant}


def _beam_order(parts: list[dict], moved: list[str]) -> list[str]:
    order = [e["name"] for e in parts]
    return sorted(moved, key=lambda n: order.index(n) if n in order else len(order))


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
    n_new: int = 0              # solves run by this call (a resumed study already had the rest)


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
         "evaluable": 0.0 if r["evaluable"] else 1.0,
         "ghosts": r.get("ghost_frac", 0.0) - r.get("max_ghost_frac", cfg.spec.tolerances.max_ghost_frac)}
    c.update({k: 0.0 if v else 1.0 for k, v in r.items() if k.startswith("opt_")})
    return c


def optimize(cfg: Config, config_id: str, budget: int | None = None, fidelity: str = "2d",
             backend: SimulationBackend | None = None, study_id: str | None = None,
             on_trial: Callable[[int, Any], None] | None = None,
             initial: list[tuple[dict, dict]] | None = None, conf: ConfigurationDef | None = None,
             bounds: dict[str, tuple[float, float]] | None = None,
             tags: dict[str, str] | None = None) -> StudyResult:
    """Run (or resume) one optimization study for a fixed configuration.

    initial: optional warm start, (channels, positions) pairs evaluated first, only when the study
    has no trials yet. Pure B0 runs leave it empty.
    conf: a configuration not in b0_configs.yaml (Phase 2 planner); config_id is then ignored.
    bounds: planner bounds (SearchSpace.raw_ranges keys) narrowing the constraint ranges.
    tags: extra job tags (e.g. run_id, round), on top of study_id / trial / purpose.
    """
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    if conf is None:
        conf = cfg.b0_configs.get(config_id)
    config_id = conf.config_id
    if bounds is None and conf.bounds:
        bounds = {k: (float(v[0]), float(v[1])) for k, v in conf.bounds.items()}
    space = SearchSpace.from_config(cfg, conf, bounds)
    # values the checker needs: fail now, not after the first solve
    for key in ("spec.detector.sigma_mcp_um", "spec.detector.mesh_open_fraction", "spec.requirements.eta_min",
                "spec.tolerances.energy_conservation_rel", "spec.tolerances.potential_match_V",
                "spec.tolerances.monotonic_tol_um", "spec.tolerances.fate_position_tol_um"):
        cfg.require(key)
    budget = budget or cfg.optimizer.default_budget
    own_backend = backend is None
    backend = backend or make_backend(cfg)
    try:
        return _optimize(cfg, config_id, conf, space, budget, fidelity, backend, study_id, on_trial, initial,
                         tags or {})
    finally:
        if own_backend and hasattr(backend, "close"):
            backend.close()


def _optimize(cfg, config_id, conf, space, budget, fidelity, backend, study_id, on_trial, initial,
              tags) -> StudyResult:
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
    if initial and not study.get_trials(deepcopy=False):
        for ch, pos in initial:
            study.enqueue_trial(space.to_params(ch, pos), skip_if_exists=True)
        log.info("warm start: %d enqueued trials", len(initial))

    n_new = 0
    with RunLog(cfg.path("db_path")) as rl:
        rl.start_study(study_id, config_id, sampler_name, cfg.optimizer.seed, budget, fidelity)
        while done < budget:
            trial = study.ask()
            channels, positions = space.suggest(trial)
            job = build_job(cfg, conf, channels, positions, fidelity=fidelity,
                            tags={"purpose": "optimize", **tags, "study_id": study_id, "trial": str(trial.number)})
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
            n_new += 1
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
        best_channels=ch_b if best else None, best_positions=pos_b if best else None, n_new=n_new,
    )


def _best(study: optuna.Study):
    ok = [t for t in study.get_trials(deepcopy=False, states=(optuna.trial.TrialState.COMPLETE,))
          if t.user_attrs.get("feasible")]
    return min(ok, key=lambda t: t.value) if ok else None
