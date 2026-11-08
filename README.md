# Ion Beam Imaging

Ion beam imaging / measurement project: COMSOL simulations of MCP-based beam imaging,
plus `ionopt`, the Phase 1 tool chain from [plan_v1.md](plan_v1.md) (config, launch
grid, wiring, backends, checker, plots, run log, optimizer).

COMSOL `.mph` model files are not tracked in this repo due to their size.

## Setup

```powershell
uv pip install --python .venv\Scripts\python.exe -e ".[dev]"
.venv\Scripts\python.exe -m pytest            # COMSOL tests are skipped by default (-m comsol to run them)
```

COMSOL 5.5 bundles Java 8, so `jpype1` must stay below 1.6.

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

## Layout

```
config/            YAML config (paths, parameters, spec, constraints, backend, optimizer, b0_configs)
src/ionopt/        package: config, schemas, launch, electrodes, backends/, worker/, checker, plots, runlog, optimize, cli
tests/             pytest (mock-based; no COMSOL needed)
scripts/           COMSOL model building / validation tools (2D axisymmetric builder, 3D touch-up, 2D-vs-3D comparisons)
data/              release files derived from the 3D model
```
