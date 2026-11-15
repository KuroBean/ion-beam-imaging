# plan_phase2.md: Agentic ion optics design system (Phase 2: agents and loop)

Working plan for Claude Code. Read plan_v1.md first: every tool named here (backend, checker,
optimizer, run log, electrodes.py, config system) is specified there. Phase 2 adds three LLM
agents (planner, critic, editor), a constraint validator, and the loop that connects them.
Status: DRAFT. Sections marked (TBD) are open decisions for the author.

## 1. Summary

- The loop is a LangGraph state machine. Code, not an LLM, decides what runs next, counts the
  solve budget, and enforces stop conditions.
- Planner: decides the next configuration and search bounds, and classifies the last result
  as a parametric, structural, or specification problem. This classification is the agent
  decision the project measures (lab report section B).
- Optimizer (plan_v1 9.9): picks voltages and positions inside the planner's bounds. The
  planner never picks individual parameter values.
- Editor: creates new model variants when the planner asks for geometry that is not already
  a switch in the model. The author approves every variant before use.
- Checker (plan_v1 9.6): decides validity, feasibility and score. Deterministic.
- Critic: fresh-context review of the checker output, plots and the planner's claims. Returns
  accept / reject / dispute plus suggestions. Can veto a result.
- Human checkpoints: spec freeze, editor variant approval, specification escalations, final
  design.

## 2. Prerequisites from Phase 1

- [ ] YAML values filled (spec, constraints; plan_v1 13 task 10 note).
- [ ] Fidelity check (plan_v1 task 10): DEFERRED until 3D compute is available. A known small
      2D vs 3D inconsistency remains; for now the 2D model is treated as trusted for search, and
      3D is used only to validate finalists once compute allows. Record this assumption in
      every run's metadata.
- [ ] B0 run on at least one chamber setup (plan_v1 task 11). Its result is the reference the
      agent must beat, and its run log entries are the planner's starting context.
- [ ] Spec thresholds (eta_min, impact threshold, sigma_mcp) fixed before any formal evaluation.

## 3. Model access (no API key)

- The author has a Claude Enterprise seat and no Anthropic API key. LLM calls go through
  Claude Code in headless mode (`claude -p`), called from Python with subprocess.
- One helper, `agents/llm.py: run_claude(prompt, schema, model, allowed_tools, cwd)`:
  - passes `--output-format json` and `--json-schema <schema from the pydantic model>`;
  - pins the model with `--model` (value from config/agents.yaml);
  - sets allowed tools per role (planner: none; critic: Read on the result folder only;
    editor: read/write/Bash inside its sandbox);
  - validates `structured_output` with pydantic; on failure retries up to N times with the
    validation error appended, then raises;
  - returns the result plus session_id, duration and total_cost_usd (an estimate on a seat,
    but logged as usage data);
  - is the only place in the codebase that invokes `claude`.
- Checks before building on it (author, on the WorkSpace):
  - [ ] `claude -p "say hi" --output-format json` works from Python under the seat.
  - [ ] Claude Code version supports `--json-schema` with schema validation (v2.1.205 or
        later; older versions silently ignored invalid schemas).
  - [ ] Headless runs do not pick up the repo's CLAUDE.md or other project context meant for the
        coding agent (check what headless mode loads; use a clean cwd if needed). Note: `--bare`
        cannot be used on a seat (it accepts only an API key, never OAuth); isolate with
        `--system-prompt`, `--tools`, `--setting-sources`, `--strict-mcp-config`,
        `--no-session-persistence` and a clean per-call cwd.
  - [ ] Usage: measure calls and cost for one full loop on the mock before planning the
        evaluation runs (seat usage limits).
- No temperature control from the CLI. Reproducibility comes from the pinned model ID, saved
  prompts, and five repeats per case. Update the lab report wording ("fixed temperature").
- A fake LLM (`agents/llm_fake.py`) returns scripted responses from files, so the whole loop is
  testable with the MockBackend and no LLM or COMSOL.

## 4. Design space: what each component may change

| Change | Existing switch? | Who handles it |
|---|---|---|
| Voltages (LV channels, mesh HV4, MCP front HV1), positions within bounds | yes | optimizer |
| Bounds on the above | yes | planner |
| Chamber setup (cfg 1/2/3) | yes | planner |
| Wiring of tip and L1 to L9 to LV1 to LV4 or GND, deflectors (cfg 3) | yes | planner |
| lens_gap, mesh_gap, z_mcp (cfg 1) ranges | yes | planner |
| Remove L1..L9 individually (presence) | yes, 2D model switch (author 2026-11-14) | planner |
| z of each present L1..L9 within bounds | yes, 2D model switch (author 2026-11-14) | optimizer (planner sets bounds) |
| Remove or resize the mesh, change its frame | no | editor (if inventory allows) |
| Add a grounded grid before the MCP | no | editor |
| Add an electrode outside the fixed stack, move a fixed part | no | editor |
| Thresholds, emission assumptions, inventory | no | author only (planner escalates) |

Inventory and buildability limits for editor proposals (what can be bought, machined, mounted
and powered) go in constraints.yaml under a new `inventory:` block (TBD, author).

## 5. Loop

```
start -> load_context -> planner -> validator
validator --invalid (with reasons, max 2 retries)--> planner
validator --needs_edit--> editor -> author_approval
author_approval --approved--> optimize
author_approval --rejected (with reason)--> planner
validator --ok--> optimize -> check -> critic -> update_state -> stop_check
stop_check --continue--> planner
stop_check --stop--> finalize (3D promotion + convergence run) -> end
planner --escalate_spec--> author (loop pauses) ; planner --stop--> finalize
```

One round = one planner proposal through to the critic verdict. A round may run one optimizer
study (many solves).

### 5.1 Stop conditions (checked in code after every round)

- Success: best result is valid, feasible, accepted by the critic, and the planner chooses stop
  (or no improvement above a tolerance for k rounds, k from config).
- Solve budget spent (counts optimizer solves, editor smoke tests, 3D promotions).
- Round cap reached.
- Editor failure cap (consecutive failed edits).
- Specification escalation: pause and wait for the author.

## 6. Shared state (agents/state.py)

One pydantic model, saved by a LangGraph SQLite checkpointer after every node so a loop can be
resumed and inspected.

- run_id, method (agent / A1 / A2), case_id (held-out case), seed, model ID
- budget: solves_total, solves_used, rounds_used, round_cap
- spec_hash, constraints_hash
- model_variants: list of approved variants (id, parent, edit script path, new parameters)
- history: per round: proposal, validator result, study_id, best job_id, metrics summary,
  critic verdict
- best_so_far: job_id, score, eta, valid, feasible, critic_accepted
- pending: current proposal, edit request, approval status
- stop_reason

Agents never read the raw state. Each gets a prompt built by a deterministic summarizer
(agents/summaries.py) from the state and the run log, so context stays small and identical
inputs give identical prompts.

## 7. Agents

### 7.1 Planner

Input (prompt): spec and constraints (summarized), design space table (section 4), approved
variants, round history (compact table), best-so-far metrics, last checker flags and last
critic verdict.

Output (PlannerProposal):
- diagnosis: parametric | structural | specification | none (first round)
- diagnosis_evidence: which metrics or critic findings support it
- action: optimize | edit_then_optimize | escalate_spec | stop
- configuration: cfg, wiring, variant_id (plan_v1 7.2 format)
- bounds: per optimizer variable, within constraints.yaml
- solve_budget: solves for this study (capped by remaining budget)
- edit_request (if action = edit_then_optimize): see 7.3
- claims: testable predictions, e.g. "r(theta) will be monotonic up to 25 deg", "mesh frame
  losses will drop below 5%". These are what the critic checks.
- rationale: free text, logged but not shown to the critic

Rules in the prompt: never propose parameter values for the optimizer to fix; prefer existing
switches before edits; do not repeat a configuration already in the history without a stated
reason.

### 7.2 Critic

Input: metrics.json (validity flags, fates, spot statistics, score), the round's optimizer
history summary, the planner's claims (not its rationale), and read access to the best job's
plots folder (trajectory side view, field map, r(theta), dtheta(theta), fate bars, axis
potential). Fresh context every round.

Output (CriticVerdict):
- verdict: accept | reject | dispute
  - reject: the result should not count (e.g. a validity concern the checker missed or a
    suspicious default-valued result). Rejected results are excluded from best_so_far.
  - dispute: result is valid but a planner claim is contradicted or untested.
- claim_checks: per claim: supported | contradicted | untestable, with the metric or plot that
  shows it
- observed_failure_modes: e.g. crossover folds r(theta), mesh frame clipping, MCP field
  penetration, slow ions in grounded regions (plan_v1 7.4), in-flight ions
- suggestions: non-binding ideas for the planner

The critic does not classify the next action; the planner does. This keeps ablation A1
(critic removed) a clean test of review, not of diagnosis.

### 7.3 Editor

Input (EditRequest from the planner): what to change (element type, position, dimensions,
which supply it connects to), why, and the parent variant.

Process, in a sandbox folder per edit (results/edits/<edit_id>/):
1. Introspect the parent model (plan_v1 task 8 scripts) and read docs/comsol_api_notes.md and
   the COMSOL 5.5 API reference. No remembered node names.
2. Write an edit script that produces a new variant. Never touch models/.
3. Register any new parameters (e.g. v_grid, z_grid) in a variant parameter file and add
   their bounds request.
4. Geometry checks: build succeeds, named selections still resolve, new element does not
   overlap others, minimum gaps and field limit respected.
5. One smoke solve (2D) through the normal backend; checker must report valid.
6. Return EditResult: variant_id, edit script, introspection diff, new parameters, check
   results, smoke job_id.

Then the loop pauses for author approval (CLI prompt showing the diff, geometry plot and smoke
plots). Rejected edits return to the planner with the author's reason.

Target of edits (author 2026-11-14): 2D only. The editor edits a copy of scripts/build_axisym.py
per edit (results/edits/<edit_id>/). 3D .mph edits by the editor come later, once a stronger
computer is available; until then the author builds 3D finalists in the GUI.

Risk tiers (from the FEABench notes): re-introspect after every structural edit; selections by
name only; watch boundary dimension (dim 1 in 2D axisymmetric, dim 2 in 3D).

## 8. Constraint validator (agents/validator.py)

Deterministic, no LLM. Extends electrodes.py and constraints.yaml checks to full proposals:
- schema valid; cfg allowed; wiring valid (at most 4 LV channels, HV roles fixed)
- bounds inside constraints.yaml for the chamber setup
- requested solves within remaining budget
- edit requests within inventory and buildability limits
- not a duplicate of a previous round (same configuration and overlapping bounds) unless the
  planner gave a reason
Returns ok / needs_edit / invalid with reasons that go back to the planner.

## 9. Logging

- SQLite table agent_calls: call_id, run_id, round, role, model, prompt path, prompt hash,
  structured output, raw result, session_id, duration, cost estimate, retries, error.
- Prompts (system and per-call) saved as files under results/runs/<run_id>/; prompt templates
  versioned in prompts/ and their hash stored.
- Every round links to its study_id and job_ids in the existing run log tables.
- One command exports a run's trace (rounds, agent calls, metrics) for the report.

## 10. Evaluation (from the lab report)

All methods share simulator, checker, optimizer and solve budget.
- B0: optimizer on author-chosen fixed configurations (Phase 1).
- B1: optimizer on randomly sampled valid configurations (sampler built on the validator).
- Agent: full loop.
- A1: critic removed (check -> update_state).
- A2: editor removed (planner limited to existing switches; validator rejects edit requests).
- Held-out cases: other cone half-angles, energy spreads and eta_min values; five repeats each.
- Metrics: best feasible dtheta, solves to reach a target, success rate, agent cost.
- Critic planted-failure test: runs with an unassigned electrode, too-short end time, wrong MCP
  area, unit error. Score: caught / missed / false alarms.

## 11. Repository additions

```
config/agents.yaml        # model ID, round cap, budget, retries, k for no-improvement stop
prompts/                  # planner.md, critic.md, editor.md (versioned)
src/ionopt/agents/
  llm.py, llm_fake.py     # run_claude helper and scripted fake
  schemas.py              # PlannerProposal, CriticVerdict, EditRequest, EditResult
  state.py                # LoopState
  summaries.py            # deterministic prompt context builders
  validator.py
  planner.py, critic.py, editor.py
  graph.py                # LangGraph nodes, edges, stop checks
  baselines.py            # B1 sampler, ablation switches
tests/agents/             # loop tests with llm_fake + MockBackend
```

CLI: `ionopt agent-run --case <id> --method agent|A1|A2 --budget N`, `ionopt b1 ...`,
`ionopt trace <run_id>`, `ionopt approve <edit_id>`.

## 12. Task order (target: Lab Report 4, Nov 29)

- [ ] 1. llm.py + headless checks (section 3); fake LLM.
- [ ] 2. Schemas and LoopState; validator with tests.
- [ ] 3. Graph skeleton with fake agents on MockBackend: rounds, budget, stop conditions,
         checkpoint and resume.
- [ ] 4. Planner prompt + summaries; one real planner call on stored B0 results.
- [ ] 5. Critic prompt; planted-failure test set built from mock runs.
- [ ] 6. Full planner-critic loop on 2D COMSOL, one chamber setup (no editor).
- [ ] 7. B1 sampler and A1 switch; first comparison runs.
- [ ] 8. Editor, limited edits (move a component, add an axisymmetric electrode or grounded
         grid) behind the approval gate; first grounding test from the FEABench notes.
- [ ] 9. Held-out case runs (agent, B0, B1, A1; A2 if editor works).

## 13. Open decisions (author)

- [x] Editor target: build_axisym.py copy, 2D only for now (section 7.3, author 2026-11-14).
- [x] Per-electrode removal/move: 2D model switches, not editor edits (section 4, author 2026-11-14).
- [ ] Evaluation sizing (cases, repeats, budget per run): decide after measuring real per-round
      solve and LLM cost (author 2026-11-14). B0 uses the draft c3_* templates until the author's
      own templates replace them.
- [ ] Inventory block in constraints.yaml: what may be added or removed (mesh sizes, grids,
      extra electrodes) and their limits.
- [ ] Round cap, total solve budget, per-study budget limits.
- [ ] Whether the planner may request 3D promotion mid-loop or only at finalize.
- [ ] Planner literature search or setup images (lab report TA question): out of scope for the
      first version unless the TAs suggest otherwise.
