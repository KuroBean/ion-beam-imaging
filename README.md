# Ion Beam Imaging

Ion beam imaging / measurement project: COMSOL simulations of MCP-based beam imaging,
plus `ionopt`, the Phase 1 tool chain from [plan_v1.md](plan_v1.md) (config, launch
grid, wiring, backends, checker, plots, run log, optimizer).

COMSOL `.mph` model files and run results are not tracked in this repo (size). See
[Files to copy by hand](#files-to-copy-by-hand-not-in-git) when setting up a new computer.

## Setup

Python 3.10 or later (tested on 3.11 and 3.12).

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install uv                                  # or use pip directly
uv pip install --python .venv\Scripts\python.exe -e ".[dev,agents]"        # agents = the Phase 2 loop
.venv\Scripts\python.exe -m pytest            # COMSOL tests are skipped by default
.venv\Scripts\python.exe -m pytest -m comsol  # one real 2D solve end to end (~1 min), checks COMSOL + the 2D model
```

COMSOL 5.5 bundles Java 8, so `jpype1` must stay below 1.6.

### Files to copy by hand (not in git)

When moving to a new computer, copy these from the old one, keeping the same paths relative to the
repository root (the locations are set in `config/paths.yaml`). Everything else comes with `git clone`.

| Path | Size | Needed for |
|---|---|---|
| `lens8_axisym_v3.mph` | ~56 MB | **Required.** The 2D base model (`models: 2d`). Every 2D solve, B0 study and agent run. |
| `lens8newMCP_ks_v6_tip.mph` | ~1.2 GB | The 3D model (`models: 3d`). Only for 3D work: `fidelity-check`, `promote`, the 3D scripts. |
| `results/runlog.sqlite` | ~20 MB | Run log: every job, its metrics, the studies. The planner's B0 table and `ionopt report` / `trace` read it. Without it, history starts empty (rerun `baseline-b0`). |
| `results/optuna.sqlite` | ~5 MB | Optimizer studies (needed to resume or extend a study). Copy together with `runlog.sqlite`. |
| `results/variants/` | ~55 MB per variant | Model variants built by the editor (each has its own `model.mph`). Needed by any configuration with a `variant_id`, e.g. `v-demo-1-r01-e0` and `v-run-2-high-collection-r06-e1` in `config/b0_configs.yaml`. |
| `results/runs/` | small | Agent run folders (prompts, responses, trace). Only to look at or resume old runs (`ionopt trace`, `agent-resume`, `scripts/agent_run_report.py`). |
| `results/<job_id>/` | large in total | Raw exports and plots per job. Only to look at old jobs' plots or `recheck` them; new runs don't need them. |

Not copied: `.venv/` (recreate it, see above), `queue/` (transient job queue, empty between runs),
`logs/mesh_stats_3d.npz` (regenerable). COMSOL 5.5 and its license are installed separately, at
`comsol_root` in `config/paths.yaml`. The older models (`lens8_axisym_v2.mph`,
`lens8newMCP_ks_v2..v5*.mph`) are history: only needed to rerun the scripts that built the current ones.

Check the result with `ionopt config-check` and `pytest -m comsol`.

## Configuration

Every adjustable value lives in `config/*.yaml` (units in the key names, `null` = TBD).

```powershell
ionopt config-check                                    # validate and list TBD keys
ionopt config-check --set spec.detector.sigma_mcp_um=80
ionopt <command> --overrides config/dev_overrides.yaml # placeholder values for MOCK development only
```

## Commands (Phase 1 status)

| Command | Status |
|---|---|
| `config-check` | done |
| `launch-preview [--fidelity 2d/3d]` | done |
| `run-job job.json` | done (mock or queue backend) |
| `check <job_id>`, `recheck --all` | done |
| `optimize --config <id> --budget N` | done (TPE; GP if PyTorch is installed) |
| `worker --runner mock` | done; `--runner comsol` arrives with task 9 |
| `fidelity-check`, `baseline-b0`, `promote` | tasks 10-11 |

Example on the mock backend:

```powershell
ionopt optimize --config example_einzel --budget 30 --overrides config/dev_overrides.yaml
```

Results go to `results/<job_id>/` (raw exports, `ions_derived.csv`, `metrics.json`,
`plots/`), the run log to `results/runlog.sqlite`.

## Running the agent loop (Phase 2)

The agent loop ([plan_phase2.md](plan_phase2.md)) runs rounds of: a **planner** (Claude) picks a
configuration (wiring, chamber setup, removed/moved parts, bounds), the Bayesian **optimizer** runs a
study of 2D COMSOL solves inside it, the **checker** scores every run, and a **critic** (Claude)
reviews the best result. An optional **editor** builds hypothetical parts from `config/inventory.yaml`
into a new 2D model variant, which you approve before it is used.

### 1. Prerequisites

- **Python environment.** Create `.venv` and install the package (see [Setup](#setup)). Activate it in
  every new PowerShell terminal, from the project folder:
  ```powershell
  .\.venv\Scripts\Activate.ps1      # the prompt then starts with (.venv)
  ```
  Type this into a terminal: double-clicking the `.ps1` file only opens it in an editor. If PowerShell
  says running scripts is disabled, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
  Without activating, call `.\.venv\Scripts\ionopt.exe <command>` instead of `ionopt <command>`.
- **COMSOL 5.5**, installed where `comsol_root` in `config/paths.yaml` points.
- **The COMSOL models.** `.mph` files are not in the repo: get them from the author and put them where
  `models:` in `config/paths.yaml` says (the 2D model must have the part switches, `lens8_axisym_v3.mph`
  or later). The variants and run history in `results/` also come separately; see
  [Files to copy by hand](#files-to-copy-by-hand-not-in-git).
- **Claude Code CLI** (`claude`), installed and logged in. The loop calls it headless (`claude -p`) for
  the planner, critic and editor; models and effort are set in `config/agents.yaml`.

### 2. Check the configuration

```powershell
ionopt config-check        # lists every value still TBD (null)
```

Chamber setups cfg 1 (tube alone, MCP on the tie rods behind the stack) and cfg 3 (chambers joined) are
usable; cfg 2 is TBD and the planner is told it is unusable. If a value the loop needs is TBD, set it in
the YAML, or pass placeholders with `--overrides config/dev_overrides.yaml` (placeholders, not physical
decisions).

### 3. Edit the config files (in this order)

| File | What to set |
|---|---|
| `config/spec.yaml` | What "better" means: `requirements.eta_min`, impact threshold, launch energy and angle, MCP resolution. Changing it changes how every run is scored. |
| `config/constraints.yaml` | Position ranges per chamber setup, supplies, and `electrodes.removable` / `movable` (the parts the planner may leave out or let the optimizer move). |
| `config/b0_configs.yaml` | Baseline B0: hand-designed configurations the agent has to beat. Replace the DRAFT entries with your own. |
| `config/inventory.yaml` | Parts the editor may build into a model variant. To skip geometry edits, run with `--method A2` instead. |
| `config/agents.yaml` | `loop:` sizes the run: `solve_budget` (total solves), `round_cap`, `study_budget_min/max` (solves per round). A 2D solve takes ~30 s to 1 min. |
| `config/backend.yaml` | `backend: comsol` for real solves (`mock` is the analytic toy model for testing), or pass `--set backend.backend=comsol` on every command. |

Any value can also be overridden for one command with `--set key=value`, e.g.
`--set spec.requirements.eta_min=0.5`. Use the same `--set` options for the baseline and the agent run,
so both are scored under the same spec.

### 4. Run the baseline B0

```powershell
ionopt baseline-b0 --configs <id> <id> ... --budget 50 --set backend.backend=comsol
```

One optimizer study per configuration. The planner sees the latest B0 study of each configuration
in its prompt as the reference to beat; it is not otherwise constrained by it. Results scored under an
older spec are marked as indicative: rerun B0 (or `ionopt recheck --all`) after changing `spec.yaml`.

### 5. Preview the planner prompt (no solves, no LLM call)

```powershell
ionopt agent-plan --prompt-only --run-id preview-1 --set backend.backend=comsol
```

Read `results/runs/preview-1/planner_prompt.md`: check the design space, the B0 table and the inventory.

### 6. Start the run

```powershell
ionopt agent-run --run-id run-1 --set backend.backend=comsol
```

Useful options:

| Option | Effect |
|---|---|
| `--method A2` | no editor (existing switches only); `A1` = no critic |
| `--goal "..."` | a direction shown to the planner every round, e.g. "test whether removing d1, d2 helps". A suggestion, not a requirement: the planner may drop it if the results argue against it. The run is recorded as steered. |
| `--budget N`, `--rounds N` | total solves and round cap (default: `config/agents.yaml`) |
| `--round-max N` | largest optimizer study per round (short demo runs) |

A small first run: `--method A2 --budget 80 --round-max 20`.

To restrict a run to chamber setup 1 (tube alone, MCP on the tie rods behind the stack), add
`--overrides config/cfg1_only.yaml`: it marks cfg 3 as not usable, so the planner can only pick cfg 1.
In cfg 1 the MCP's usable z range depends on the configuration (it sits behind the last plate, or behind
the screen mesh it carries, and at most rod end - 10 mm behind E1); `ionopt agent-plan --prompt-only`
shows the ranges per configuration.

To test a specific configuration exactly as written, do not rely on `--goal`: add it to
`b0_configs.yaml` and run `ionopt optimize --config <id> --budget N`.

### 7. While it runs

The loop pauses when the editor proposes a model variant or the planner asks a question
(`escalate_spec`). Continue with:

```powershell
ionopt agent-resume run-1 --approve              # approve the pending model edit
ionopt agent-resume run-1 --reject "reason"      # reject it
ionopt agent-resume run-1 --answer "..."         # answer the planner's question
ionopt agent-resume run-1 --stop                 # end the run
ionopt agent-resume run-1 --extend-rounds 2 --extend-solves 40   # give a finished run more room
```

`agent-resume` reuses the run's `--set` / `--overrides`, and also continues a run that was
interrupted (e.g. the terminal closed): `ionopt agent-resume run-1`.

### 8. Review the results

```powershell
ionopt trace run-1                                   # results/runs/run-1/trace.md: rounds, scores, LLM costs
.venv\Scripts\python.exe scripts/agent_run_report.py run-1 --set backend.backend=comsol
                                                     # readable transcript + variable figure (same --set/--overrides as the run)
ionopt report --study run-1-r03                      # HTML page with plots for one round's study
```

Everything a run produced (prompts, responses, critic evidence, edits) is under `results/runs/<run_id>/`.

## Layout

```
config/            YAML config (paths, parameters, spec, constraints, backend, optimizer, b0_configs)
src/ionopt/        package: config, schemas, launch, electrodes, backends/, worker/, checker, plots, runlog, optimize, cli
src/ionopt/agents/ Phase 2 agent loop: graph, planner/critic/editor calls, validator, prompt summaries
prompts/           system prompts of the planner, critic and editor
tests/             pytest (mock-based; no COMSOL needed)
scripts/           COMSOL model building / validation tools (2D axisymmetric builder, 3D touch-up, 2D-vs-3D comparisons)
data/              release files derived from the 3D model
```
