"""Editor agent with a scripted LLM on the mock backend: checks, retries, variant files, approval."""

import json

from conftest import CONFIG_DIR
from ionopt.agents.config import load_agents_config
from ionopt.agents.editor import SCRIPT, Editor, static_problems
from ionopt.agents.graph import LoopRun, new_state
from ionopt.agents.llm_fake import FakeLLM
from ionopt.agents.roles import LoopContext
from ionopt.agents.schemas import EditRequest
from ionopt.backends.mock import MockBackend
from ionopt.config import ConfigurationDef
from ionopt.optimize import optimize
from ionopt.variants import load_variant, variant_dir

REPO = CONFIG_DIR.parent
WIRING = {"tip": "LV1", "e3": "LV2"}
MESH_LINE = '["5.5", f"{m}-mesh_gap"]'
WIDE_REPORT = {"summary": "mesh disc radius is now d_mesh_open/2",
               "parameters": [{"name": "mesh_open_diameter", "comsol_name": "d_mesh_open", "role": "variable",
                               "inventory_item": "screen_mesh_wide", "inventory_param": "open_diameter_mm",
                               "as_built": 11}]}


def ctx_with(cfg, responses):
    acfg = load_agents_config(CONFIG_DIR, overrides={"loop": {"study_budget_min": 3}})
    return LoopContext(cfg=cfg, acfg=acfg, llm=FakeLLM(responses), backend=MockBackend(cfg),
                       runs_dir=cfg.path("results_dir") / "runs", prompts_dir=REPO / "prompts", editor=Editor())


def widen(sandbox, bad_import=False):
    def edit(prompt, schema):
        f = sandbox / SCRIPT
        s = f.read_text(encoding="utf-8")
        s = s.replace(MESH_LINE, '["d_mesh_open/2", f"{m}-mesh_gap"]')
        s = s.replace('    ("mesh_gap", "12.7[mm]",', '    ("d_mesh_open", "11[mm]", "screen mesh open diameter"),\n'
                      '    ("mesh_gap", "12.7[mm]",')
        if bad_import:
            s = "import os\n" + s
        elif s.startswith("import os\n"):
            s = s[len("import os\n"):]
        f.write_text(s, encoding="utf-8")
        return WIDE_REPORT
    return edit


def base_run(cfg):
    """A stored valid parent run (the equivalence reference)."""
    conf = ConfigurationDef(config_id="ref", cfg=1, wiring=WIRING)
    optimize(cfg, "ref", budget=2, backend=MockBackend(cfg), study_id="ref", conf=conf)


def test_static_checks():
    assert static_problems("import os\nos.system('x')\n")
    assert static_problems("x = open('f').read()\n")
    assert static_problems("import argparse\nimport jpype\nfrom comsol_session import start\n") == []


def test_editor_builds_a_variant_after_a_retry(cfg_tmp):
    base_run(cfg_tmp)
    sandbox = cfg_tmp.path("results_dir") / "runs" / "r1" / "edits" / "r01_e0"
    sandbox.mkdir(parents=True)
    ctx = ctx_with(cfg_tmp, {"editor": [widen(sandbox, bad_import=True), widen(sandbox)]})
    req = EditRequest(inventory_items=["screen_mesh_wide"], description="sweep the mesh opening", reason="eta")
    res = Editor()(req, new_state(ctx, "r1"), ctx, sandbox)
    assert res.ok, res.notes
    assert "import ['os'] not allowed" in ctx.llm.calls[1]["prompt"]          # the retry got the failed check
    assert res.n_solves == 2 and res.checks == {"static": True, "build": True, "equivalence": True,
                                                 "smoke_valid": True, "no_overlap": True}
    m = load_variant(cfg_tmp, res.variant_id)
    assert not m.approved and m.variables()[0].range == [10, 40] and m.mesh_open_fraction == 0.7
    assert (variant_dir(cfg_tmp, res.variant_id) / "edit.diff").read_text().count("d_mesh_open") >= 2
    assert ctx.llm.calls[0]["add_dirs"] == [sandbox]


def test_editor_without_a_change_fails(cfg_tmp):
    base_run(cfg_tmp)
    sandbox = cfg_tmp.path("results_dir") / "runs" / "r1" / "edits" / "r01_e0"
    sandbox.mkdir(parents=True)
    ctx = ctx_with(cfg_tmp, {"editor": [WIDE_REPORT] * 3})
    req = EditRequest(inventory_items=["screen_mesh_wide"], description="x", reason="x")
    res = Editor()(req, new_state(ctx, "r1"), ctx, sandbox)
    assert not res.ok and "unchanged" in res.notes and len(ctx.llm.calls) == 3


def test_loop_edit_approve_and_optimize_the_variant(cfg_tmp):
    base_run(cfg_tmp)
    sandbox = cfg_tmp.path("results_dir") / "runs" / "r1" / "edits" / "r01_e0"
    edit = {"diagnosis": "structural", "diagnosis_evidence": "mesh frame losses", "action": "edit_then_optimize",
            "configuration": {"cfg": 1, "wiring": WIRING}, "solve_budget": 3,
            "edit_request": {"inventory_items": ["screen_mesh_wide"], "description": "sweep the mesh opening",
                             "reason": "frame losses"},
            "claims": [{"id": "c1", "statement": "fewer frame losses", "evidence_needed": "fates"}], "rationale": "r"}
    stop = {"diagnosis": "parametric", "diagnosis_evidence": "-", "action": "stop", "rationale": "r"}
    ctx = ctx_with(cfg_tmp, {"planner": [edit, stop], "editor": [widen(sandbox)],
                             "critic": [{"verdict": "accept", "reasons": "ok"}]})
    with LoopRun(ctx, "r1") as lr:
        st = lr.start(new_state(ctx, "r1", solve_budget=50))
        assert st.interrupt["type"] == "edit_approval"
        st = lr.resume({"approved": True})
    s = st.state
    vid = s.history[0].proposal.configuration.variant_id
    assert vid.startswith("v-r1-") and load_variant(cfg_tmp, vid).approved
    assert s.budget.solves_used == 2 + 3 and s.history[0].n_solves == 3
    best = json.loads((cfg_tmp.path("results_dir") / s.history[0].best_job_id / "job.json").read_text())
    assert best["variant_id"] == vid and 0.010 <= best["positions"]["mesh_open_diameter"] <= 0.040
    # the next planner prompt lists the approved variant and its variable
    assert f"- {vid}:" in ctx.llm.calls[-1]["prompt"] and "mesh_open_diameter_mm [10, 40]" in ctx.llm.calls[-1]["prompt"]
