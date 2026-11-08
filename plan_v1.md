# plan.md: Agentic ion optics design system (Phase 1: tools and baseline)

This file is the working plan for Claude Code. Read it fully before writing code.
Phase 1 builds every deterministic tool the agents will later call, plus the
optimizer-only baseline (B0). Agents (planner, critic, editor) are Phase 2 and are
only outlined at the end.

## 1. Context

- Device: nanopore ion source; ions travel through a stack of up to 9 identical disk
  electrodes (E1 is the extractor, E2 to E9 form Einzel lens and accelerator sections)
  and a 10 mm diameter mesh opening (TBD: current model has 11 mm) to a microchannel plate (MCP)
  detector with phosphor screen (Hamamatsu F2225-21P, 40 mm plate diameter). The mesh is mounted
  on the MCP holder at an adjustable gap in front of the MCP face.
- First test species: ions from NaCl salt solutions (Na+, 22.99 Da). Heavier peptides
  (e.g. protonated arginine, 175.1 Da) come later and are a config change only.
- Goal: find configurations (chamber setup, which electrodes are used and where, how the
  tip and electrodes are wired to supplies, supply voltages, mesh and MCP positions) whose MCP image is easiest to invert back to the
  initial angular distribution, while enough ions are collected and land fast enough
  to trigger the MCP.
- Simulator: COMSOL 5.5 (Electrostatics + Charged Particle Tracing), driven from Python
  through MPh (https://mph.readthedocs.io).
- Fidelity strategy: fast 2D axisymmetric model for sweeps and optimization; existing 3D
  model only for validating promising candidates.
- Compute: currently the AWS WorkSpace (8 GB RAM, 2 cores, about 8 min per 3D run with the
  refined mesh: ~3 min remesh, ~3 min electrostatics, ~1.5 min particles; 2D about 30 s).
  Later, simulations may move to a 128 GB lab machine over SSH. The code must make that
  switch a configuration change, not a rewrite.

## 2. Phase 1 deliverables (target: Nov 15)

1. Config system: every adjustable value in editable YAML files, validated on load (section 4).
2. Launch generator: deterministic ion grid and weights, written in COMSOL release format.
3. Simulation backend interface with three implementations: Mock, LocalQueue, (stub) SSHQueue.
4. COMSOL worker: persistent process that runs jobs with MPh and exports raw results.
5. Checker: derived per-ion table, spot statistics, metrics and validity flags.
6. Plotting: standard diagnostic plots from exported data.
7. Run log: SQLite database plus one result folder per job.
8. Optimizer: Bayesian optimization over supply channel voltages and positions for a
   fixed configuration.
9. Baseline B0: optimizer over a fixed list of configurations, with 2D to 3D promotion.

## 3. Conventions

- Units: SI internally. Config files may use mm, kV, eV, degrees; every config key
  states its unit in its name or comment, and values are converted on load.
- Coordinates: z is the beam axis, origin at the model tip apex, z increasing toward
  the MCP. r is radial distance from the axis. Emission angle theta is measured from +z.
  The COMSOL models use a chamber frame (tip apex at parameter tip_z = 105 mm);
  model_adapter.py converts (z_model = z + tip_z), nothing else sees model coordinates.
- Charge sign comes from config (Na+ now; Cl- would flip every polarity). No code may
  assume q > 0.
- Platform: Windows. Use pathlib everywhere. No hard-coded absolute paths; all paths
  come from config/paths.yaml (including the COMSOL install root).
- Python: verified 3.12 with MPh 1.4.0. COMSOL 5.5 bundles Java 8, so jpype1 must stay
  < 1.6, and the bundled JRE bin directory must be on PATH before importing mph.
- Style: type hints, pydantic models for every schema, pytest for tests.

## 4. Configuration system (all adjustable values live here)

Many values are not known yet (MCP resolution, tolerances, position ranges, supply limits).
They must be easy to change by hand, and changing them must never require code edits.

- All adjustable values live in YAML files under config/ (spec.yaml, constraints.yaml,
  parameters.yaml, backend.yaml, paths.yaml, b0_configs.yaml). Each key has a comment
  with its unit and meaning.
- Unknown values are written as `null` with a `# TBD` comment. Loading succeeds with
  nulls, but any step that needs a null value stops with an error naming the exact key
  (for example: "spec.detector.sigma_mcp_um is TBD; set it in config/spec.yaml").
- Pydantic validates types, units and ranges on load (for example: a min position larger
  than its max is an error).
- Command-line overrides for quick experiments: `--set spec.detector.sigma_mcp_um=80`.
  Overrides are recorded like any other value.
- Every job saves a snapshot of the fully resolved config (config_snapshot.yaml) and the
  run log stores its hash, so every result is traceable to the exact values used.
- Thresholds and tolerances affect only the checker, so changing them later must not
  require new simulations: `ionopt recheck` recomputes metrics for stored runs with the
  current spec (section 8.6). The raw exports are the permanent record; metrics are
  re-derivable.

## 5. Physics assumptions (configurable, recorded in every run's metadata)

- Tip: a small meshable tip in both models, larger than the real nanopore. The launch
  distribution describes ions at the simulated launch point, not at the real emission site.
- Angular distribution: Gaussian in theta for current per solid angle,
  dI/dOmega proportional to exp(-theta^2 / (2 sigma^2)), with HWHM = 20 deg, so
  sigma = 20 / sqrt(2 ln 2) = 16.99 deg. Grid weights include sin(theta).
- Initial kinetic energy: uniform spread of width dE (default 2 eV) around mean E0
  (TBD). Must be replaceable by an arbitrary distribution later (pass a weight function).
- Charge state q (default +1). Mass m (default 22.99 Da, Na+; later 175.1 Da for
  protonated arginine). Paths depend only on kinetic energy per charge; mass affects
  landing speed and timing only (particle end time comes from config).
- Landing kinetic energy is fixed by potentials: KE_land = KE_0 + q (V_launch - V_land).
  The checker uses this as a conservation check.
- Mesh: thin, mounted on posts on the MCP holder at an adjustable gap (mesh_gap) in front
  of the MCP face (currently 12.7 mm). Modeled as a transparent equipotential disc (an
  interior boundary, so ions pass) plus a solid frame (cross + hub in 3D; the cross arms
  are not axisymmetric, so 2D uses a fitted ring of radius R_cross). Ions reaching the
  frame freeze there; crossing positions are not recorded. Wire transmission is a scalar
  factor (mesh_open_fraction, TBD) applied to collection efficiency.
- No space charge.

## 6. Repository layout

The package lives at the repository root (no extra ionopt/ folder). The existing
scripts/ folder keeps the model-building and validation tools (build_axisym.py,
touchup_3d.py, compare_axis.py, compare_particles.py, ...). models/ is gitignored.

```
<repo root>/
  config/
    paths.yaml            # model files, queue dirs, results dir, db path
    parameters.yaml       # parameter registry (section 7)
    spec.yaml             # launch assumptions, detector, thresholds, tolerances (section 10)
    constraints.yaml      # chambers, positions, electrodes, supplies (section 12)
    backend.yaml          # which backend, worker count, timeouts, SSH settings
    b0_configs.yaml       # fixed configuration list for baseline B0
  models/                 # base .mph files, READ ONLY for all code
  src/ionopt/
    config.py             # loading, validation, overrides, snapshots
    schemas.py            # JobSpec, ResultBundle, Metrics, etc.
    launch.py
    electrodes.py         # supply-channel to electrode mapping (section 7.2)
    backends/
      base.py             # SimulationBackend interface
      mock.py
      queue.py            # QueueBackend + Transport interface
      transports.py       # LocalFSTransport, SSHTransport (stub in Phase 1)
    worker/
      comsol_worker.py    # persistent MPh worker
      model_adapter.py    # all COMSOL-specific calls live here
    checker.py
    plots.py
    runlog.py
    optimize.py
    baseline.py
    cli.py
  tests/
  docs/
    comsol_api_notes.md   # verified node tags and property names (section 14)
  results/                # one folder per job_id (gitignored)
```

## 7. Parameters, electrodes and supplies

### 7.1 Parameter registry (config/parameters.yaml)

Every COMSOL parameter the code may set is declared here. Nothing outside the registry
gets set. Bounds are not stored here; they come from constraints.yaml so they can be
adjusted per chamber setup.

```yaml
- name: cfg              # chamber setup: 1 = chamber 1 (tube), 2 = chamber 2 (sphere), 3 = both joined
  comsol_name: cfg       # confirmed in both current models
  type: int
  allowed: [1, 2, 3]
- name: z_mcp            # MCP front face position (current models: mcp_z, a derived
  comsol_name: TBD       # expression; free only for cfg 1 via z_mcp_c1, fixed at the
  unit: mm               # sphere centre for cfg 2/3)
- name: mesh_gap         # mesh plane distance in front of the MCP face (mesh rides on the
  comsol_name: TBD       # MCP holder; current models hard-code 12.7 mm)
  unit: mm
- name: v_tip
  comsol_name: TBD
  unit: V
- name: v_extractor
  comsol_name: TBD
  unit: V
- name: v_mesh
  comsol_name: TBD
  unit: V
- name: v_mcp_front
  comsol_name: TBD
  unit: V
- name: v_mcp_back       # only if the model includes it; see 7.3
  comsol_name: TBD
  unit: V
- name: v_phosphor       # only if the model includes it; see 7.3
  comsol_name: TBD
  unit: V
# one block per disk electrode k = 1..9 (E1 = extractor):
- name: use_e_k          # electrode present in the geometry (E1 always present)
  comsol_name: TBD
  type: bool
- name: z_e_k            # axial position of electrode k (center of disk)
  comsol_name: TBD
  unit: mm
- name: v_e_k            # potential of electrode k, set from the wiring map (7.2)
  comsol_name: TBD
  unit: V
```

The disk geometry (outer diameter, aperture diameter, thickness) is identical for all nine
and fixed in the model; record the values in constraints.yaml for the validator and mock.

### 7.2 Electrodes, supplies and wiring

Hardware:
- Nine identical disk electrodes E1 to E9, ordered along +z from the tip. E1 is always the
  extractor. E2 to E9 can be used in any combination (Einzel lens sections, accelerating
  stages, or left out).
- Four low-voltage supplies LV1 to LV4 (+/- a few hundred V, exact limit TBD).
- The tip and every used electrode connect to one of LV1 to LV4 or to ground. Several
  electrodes may share one channel (tied together).
- Four high-voltage ports with fixed one-to-one roles: HV1 = MCP front, HV2 = MCP back,
  HV3 = phosphor, HV4 = mesh (+/- 10 kV).

The optimizer does not tune electrode potentials directly. It tunes channel voltages, and a
wiring map assigns the tip and each used electrode to a channel or to ground. This makes the
four-supply limit impossible to violate:

```yaml
# part of a configuration (b0_configs.yaml now, planner proposals in Phase 2)
electrodes_used: [1, 2, 3, 4, 7, 8]   # E1 always included
wiring:                  # tip and used electrodes only; HV roles are fixed
  tip: LV1               # e.g. slightly positive so ions keep energy in grounded regions
  e1: GND                # extractor
  e2: GND                # Einzel lens: E2 and E4 grounded, E3 on LV2
  e3: LV2
  e4: GND
  e7: LV3                # accelerating stage
  e8: LV3
```

- electrodes.py validates a wiring map: E1 is used; every used electrode and the tip is
  assigned; only LV1 to LV4 or GND appear; at most 4 distinct LV channels; HV roles are not
  reassigned.
- It expands channel voltages into the COMSOL parameters v_tip and v_e_k, setting GND and
  unused electrodes to 0 V, and sets use_e_k.
- Positions: z_e_k must increase with k and respect the minimum spacing and allowed range
  in constraints.yaml. Removed electrodes have no position.
- How an electrode is removed in COMSOL (geometry feature deactivated, or moved out of the
  domain) is decided after introspection (task 8) and lives only in model_adapter.py.
- The 2D model needs the disk cross-section (an annulus in r-z), which is simple because
  the disks are axisymmetric.
- Electrodes used and wiring are structural choices (fixed per configuration in Phase 1,
  proposed by the planner in Phase 2). Channel voltages, the mesh and MCP front voltages,
  and positions are continuous and go to the optimizer.
- Design space note: tip plus nine electrodes, each on one of five options, already gives
  millions of wirings before positions. This is the space where the Phase 2 planner should
  add value over baselines.

### 7.3 High-voltage roles

- HV1 (MCP front) and HV4 (mesh) shape the field the ions see and are optimizer variables.
- HV2 (MCP back) and HV3 (phosphor) sit behind the MCP front face and do not affect ion
  trajectories before impact. They are set from detector operating offsets in
  constraints.yaml (for example back = front + gain voltage), checked against the
  +/- 10 kV port range, and included in the model only if the author models them.

### 7.4 Physics note on tip voltage

The chamber walls are grounded, so an ion's kinetic energy anywhere is
KE_0 + q (V_tip - V_local). If the tip is grounded and only some electrodes are negative,
ions slow back down to about KE_0 (1 to 2 eV) wherever the local potential returns to near
ground, for example near grounded electrodes and walls, which makes them very sensitive to
small fields. A tip held positive relative to ground keeps ions energetic in grounded
regions. Both approaches stay in the search space; the checker and plots should make this
effect visible (axis potential plot, time of flight statistics).

## 8. Required conventions inside the COMSOL models (author sets these up in the GUI)

Both models (2D axisymmetric and 3D) should share these names so one adapter handles both.
The 2D model is generated by scripts/build_axisym.py, so it emits these names directly.
Only the 3D model needs GUI or script edits. Mesh refinement in 3D must use named
selections, not numeric boundary IDs (touchup_3d.py currently uses IDs and breaks on any
geometry change).

- Global parameters named as in parameters.yaml.
- Named selections: sel_tip, sel_e1 to sel_e9, sel_mesh_plane, sel_mesh_frame,
  sel_mcp_face, sel_walls.
- Studies: std_es (stationary electrostatics), std_pt (time-dependent particle
  tracing, using the std_es solution).
- Particle release: "release from data file". Verified for 2D in 5.5 (feature
  ReleaseFromDataFile, InitialVelocity = FromFile, columns r[mm] z[mm] vr vz [m/s], start
  r = 1e-6 mm just off the axis); still to verify for 3D (the 3D model currently uses a
  Particle Beam). The adapter sets the file path on the release node before each run.
- 2D axis condition: Bounce (the default Freeze stops ions at the beam crossover).
- Wall condition: freeze on all surfaces, so final positions show where each ion ended.
- Raw data: the adapter may read results with MPh evaluate() (already used by
  scripts/compare_particles.py) instead of GUI export nodes. Either way it writes these
  files:
  exp_ions_final (per ion: index, final position, velocity, kinetic energy, time),
  exp_ions_traj (optional, positions at output times, for plots only),
  exp_axis_potential (V and E along the axis),
  exp_cutplane_field (V and |E| on the r-z plane or a cut plane, gridded, for plots),
  exp_electrode_potentials (average V on each named selection).
- Particle tracing end time long enough for the slowest ion; the checker flags ions
  still in flight.

## 9. Module specifications

### 9.1 launch.py

- Input: launch section of spec.yaml, fidelity.
- Grid: theta from 0 to theta_max (default 50 deg) with n_theta points; energies across
  the spread with n_E points; phi with n_phi points in 3D only (2D launches in the r-z
  plane).
- Output: ion table (ion_id, theta, phi, KE_0, weight, x, y, z, vx, vy, vz) and a release
  file in COMSOL's expected format. Velocities from KE_0, mass and direction.
- Weights: exp(-theta^2/(2 sigma^2)) * sin(theta) * energy_weight * dphi, normalized to 1.
- The ion table is saved with each job so the checker joins on ion_id and never relies
  on COMSOL's internal particle ordering.
- Tests: weights sum to 1; the weighted angular histogram matches the target HWHM;
  KE recovered from velocities matches KE_0.

### 9.2 Schemas (schemas.py)

```python
class JobSpec(BaseModel):
    job_id: str                  # uuid
    fidelity: Literal["2d", "3d"]
    cfg: int
    electrodes_used: list[int]   # E1 always included
    wiring: dict[str, str]       # tip / e<k> -> LV1..LV4 or GND (section 7.2)
    channels: dict[str, float]   # e.g. {"LV1": 100.0, "LV2": 85.0, "HV1": -10000, "HV4": 0}
    positions: dict[str, float]  # z_e_k for used electrodes, mesh_gap, z_mcp
    launch: LaunchSpec
    mesh_level: Literal["normal", "fine"] = "normal"
    ion_level: Literal["search", "convergence"] = "search"   # convergence = 2x ions
    tags: dict[str, str] = {}    # study_id, config_id, purpose

class ResultBundle(BaseModel):   # describes files in results/<job_id>/
    job_id: str
    status: Literal["success", "failed", "timeout"]
    error: str | None
    files: dict[str, str]
    meta: RunMeta                # resolved params, model file + hash, COMSOL version,
                                 # mesh element count, solve times, worker host,
                                 # git commit, config hash, timestamps
```

Every job writes results/<job_id>/ containing:

| File | Written by | Contents |
|---|---|---|
| job.json, config_snapshot.yaml | backend | exact request and resolved config |
| meta.json | worker | run metadata (above) |
| ions_launch.csv | launch.py | initial conditions and weights |
| ions_final.csv | worker | raw COMSOL export per ion |
| axis_potential.csv, cutplane_field.csv | worker | field data |
| electrode_potentials.csv | worker | average V per named selection |
| traj.csv (optional) | worker | sampled trajectories |
| geometry.json | worker | key z positions and radii for the resolved params |
| ions_derived.csv | checker | per-ion derived values (9.6) |
| metrics.json | checker | summary statistics, metrics, flags (9.6) |
| plots/*.png | plots.py | diagnostic plots (9.7) |

### 9.3 Backend interface (backends/base.py)

```python
class SimulationBackend(Protocol):
    def submit(self, job: JobSpec) -> str: ...
    def status(self, job_id: str) -> Literal["pending", "running", "done", "failed"]: ...
    def fetch(self, job_id: str) -> ResultBundle: ...
    def run(self, job: JobSpec, timeout_s: float) -> ResultBundle: ...  # submit + wait + fetch
```

- MockBackend: no COMSOL. Analytic model returning files in the same format (9.4).
- QueueBackend(transport): writes job.json to queue/pending, waits for
  queue/done/<job_id>/, copies results into results/. The worker owns
  pending -> running -> done/failed moves.
- Transport interface: put_job, list_done, get_results. LocalFSTransport (same machine)
  in Phase 1. SSHTransport (scp/sftp over SSH to the lab machine) is a stub with the same
  interface; implementing it later must not change QueueBackend or anything above it.
- backend.yaml selects the backend and transport. Agents and the optimizer only see
  SimulationBackend.

### 9.4 Mock simulator

- Geometry: launch at z=0, mesh frame at z_mcp - mesh_gap with opening radius 5 mm, MCP
  at z_mcp with active radius 20 mm (both read from config, not hard-coded).
- Toy optics: r_land = z_mcp * tan(theta) * f(channels) + c * (KE_0 - E0), where f is a
  smooth function of one LV channel and HV4 (mesh) with a known optimum, and an
  optional fold (crossover) region to test the monotonicity check.
- Fates: mesh_frame if (z_mcp - mesh_gap)*tan(theta)*f > R_mesh; mcp_outside if r_land > R_mcp.
- KE_land from the conservation formula.
- Optional noise and optional failure injection (fake timeouts, missing files).
- Purpose: develop and test the checker, optimizer, run log and plots without COMSOL,
  and serve as the checker's analytic unit tests (field-free case: r = L tan theta).

### 9.5 COMSOL worker (worker/comsol_worker.py, worker/model_adapter.py)

- Long-running process: start one mph.Client, load each model once, then loop over
  queue/pending. Start with 1 worker on the WorkSpace; the worker count comes from config.
- Per job: validate the job (registry, wiring, constraints), expand channels into
  electrode parameters, set params and electrode toggles, write the release file and point the
  release node to it, build geometry and mesh, solve std_es then std_pt, trigger export
  nodes, write geometry.json and meta.json, move the job to done or failed.
- The worker exports raw data only. All derived quantities are computed by the checker,
  so they can be recomputed without rerunning COMSOL.
- Robustness: per-job timeout; catch COMSOL exceptions and record the message; restart
  the client after N jobs or after a crash; never leave a job in running after exit.
- All COMSOL node tags and property names live in model_adapter.py, nowhere else.
- Never save over a base model. If a model must be saved for inspection, save a copy
  into results/<job_id>/.
- The worker script must also run unchanged on the lab machine (no WorkSpace-specific
  paths or assumptions).

### 9.6 Checker (checker.py)

Inputs: ResultBundle files and the current spec.yaml. Outputs: ions_derived.csv and
metrics.json. No LLM involvement. Runs automatically after each job and on demand
(`ionopt recheck`).

**Step 1: per-ion derived table (ions_derived.csv)**

| Column | Meaning |
|---|---|
| ion_id, theta_deg, phi_deg, KE0_eV, weight | from ions_launch.csv |
| fate | mcp_active, mcp_outside, mesh_frame, electrode, wall, in_flight |
| surface | named selection where the ion stopped (for example sel_e3) |
| x_land_mm, y_land_mm, r_land_mm | landing coordinates on the MCP plane (NaN if not on MCP) |
| on_mcp_active | true if r_land <= 20 mm (from config) |
| impact_KE_eV, impact_speed_mps | at the final position |
| impact_angle_deg | angle between final velocity and the MCP normal (MCP ions only) |
| above_threshold | impact energy or speed above the requirement |
| tof_us | time of flight |
| energy_error_rel | deviation from KE_0 + q (V_launch - V_land) |

Fate classification uses final positions against geometry.json; in_flight if the final
time equals the end time and speed is nonzero.

**Step 2: summary statistics (metrics.json, "spot" and "fates" blocks).** All weighted by
emission weight, over mcp_active ions unless stated.

- Fate fractions: weight fraction for each fate (relative to all launched ions).
- Centroid (x, y) and its offset from the axis (3D only; zero by symmetry in 2D, which
  also makes it a useful 2D vs 3D asymmetry indicator).
- RMS radius about the centroid and about the axis.
- r50 and r90 (radius containing 50% and 90% of landed weight), r_max.
- Fill fraction: r90 / 20 mm (how much of the active area the image uses).
- Impact energy: weighted mean, minimum, and fraction above the threshold.
- Impact angle: mean and max.
- Time of flight: mean and spread.

These statistics describe the spot and help the critic and author diagnose runs. The
optimization score is the angular resolution in step 3. Any spot statistic can be turned
into an extra constraint (for example minimum fill fraction) through spec.yaml without
code changes.

**Step 3: mapping and resolution**

1. Over mcp_active ions, weighted mean r(theta) and spread sigma_E(theta) across energy
   (and phi in 3D).
2. dr/dtheta by central differences on the theta grid (or a smoothing spline,
   configurable); sigma_tot = sqrt(sigma_E^2 + sigma_MCP^2);
   dtheta(theta) = sigma_tot / |dr/dtheta|.
3. Evaluation range: contiguous theta range from 0 where at least
   eval_range_landed_frac of ion weight lands on mcp_active. Summary score: max dtheta
   over that range.
4. Monotonicity: r(theta) strictly increasing over the evaluation range (tolerance in spec).

**Step 4: requirements and validity**

- Collection efficiency: eta = mesh_open_fraction * (weight of mcp_active ions) /
  (weight of all launched ions).
- Fast fraction: weighted fraction of mcp_active ions with above_threshold true;
  must be at least frac_fast_min.
- Validity: fate counts sum to the number launched; energy_error_rel below tolerance;
  electrode potentials match assigned values; no in_flight ions; required files present.
- Overall: valid (all validity checks pass) and feasible (monotonic, eta >= eta_min,
  fast fraction >= frac_fast_min, plus any optional constraints). Score = summary dtheta
  (lower is better).
- Convergence check (separate function): compare a normal run with its convergence rerun
  (2x ions, fine mesh); pass if dtheta and eta change less than the tolerances.

Tests: analytic mock cases with hand-computed expected metrics and spot statistics; a
folded mapping must fail monotonicity; missing files and in-flight ions must mark the run
invalid; changing a threshold and running recheck must change the verdict without
rerunning the simulation.

### 9.7 Plots (plots.py)

Saved to results/<job_id>/plots/: trajectory side view (r vs z, colored by theta, if traj
exported), field map from cutplane_field.csv with electrodes outlined, r(theta) with
sigma_tot band, dtheta(theta), fate breakdown bar chart, MCP hit map (3D) or landing
radius histogram (2D) with the 40 mm active area drawn, axis potential. Fixed sizes and
axis limits per chamber setup so plots are comparable across runs (needed later by the
critic agent).

### 9.8 Run log (runlog.py)

SQLite tables:
- jobs: job_id, created_at, fidelity, cfg, config_json (electrodes used, wiring, channels,
  positions), status, backend, worker_host, solve_time_s, model_hash, git_commit,
  config_hash, study_id, config_id
- metrics: job_id, spec_hash, valid, feasible, score, eta, frac_fast, monotonic, r90,
  fill_fraction, metrics_json (recheck adds a new row per spec_hash instead of
  overwriting)
- studies: study_id, config_id, optimizer, seed, budget, started_at, finished_at, best_job_id
- promotions: job_id_2d, job_id_3d, score_2d, score_3d, eta_2d, eta_3d

### 9.9 Optimizer (optimize.py)

- Optuna with a fixed seed. Prefer its Gaussian process (Bayesian optimization) sampler;
  fall back to TPE if unavailable in the installed version.
- Search space: voltages of the LV channels used by the configuration's wiring, HV1 (MCP
  front) and HV4 (mesh), plus positions (z_mcp, mesh_gap, z_e_k of used electrodes, with
  the ordering and spacing constraints enforced by reparameterizing as gaps between
  consecutive electrodes). Bounds come from
  constraints.yaml for the configuration's chamber setup.
- Objective: minimize score. Constraints (eta, monotonicity, fast fraction) through
  Optuna's constraint support if available, otherwise a penalty.
- Failed or invalid runs are logged, never silently dropped, and returned to the optimizer
  as failed trials.
- Budget in number of solves. Studies are resumable from the SQLite log.

### 9.10 Baseline B0 and promotion (baseline.py)

- B0: for each configuration in config/b0_configs.yaml (chamber setup, electrodes used,
  wiring), run one 2D optimization study with the same budget. The author writes a small
  set of hand-designed templates, for example: extractor only; extractor + one Einzel
  lens (E2 to E4); extractor + Einzel lens + accelerating stage; each with a positive tip
  and with a grounded tip and negative electrodes.
- Promotion: top k feasible 2D results per configuration are rerun in 3D with the same
  params, then the best 3D candidate gets a convergence rerun.
- Early fidelity check (do this first, before trusting 2D): run about 5 identical
  settings in 2D and 3D and record how much r(theta), dtheta, eta and the spot statistics
  differ.

### 9.11 CLI (cli.py)

```
ionopt config-check          # load and validate all config, list TBD keys
ionopt launch-preview        # plot the launch distribution and weights
ionopt run-job job.json      # one job through the configured backend
ionopt check <job_id>        # run the checker on stored results
ionopt recheck [--all]       # recompute metrics for stored runs with the current spec
ionopt optimize --config <config_id> --budget N
ionopt baseline-b0
ionopt promote --study <study_id> --top-k 3
ionopt fidelity-check
ionopt worker                # start a COMSOL worker on this machine
```

All commands accept `--set key=value` overrides (section 4).

## 10. spec.yaml (launch assumptions, detector, thresholds, tolerances)

```yaml
launch:
  hwhm_deg: 20               # half width at half max of dI/dOmega
  theta_max_deg: 50
  n_theta: null              # TBD, e.g. 41 for search
  n_E: null                  # TBD, e.g. 3
  n_phi: null                # TBD, 3D only, e.g. 8
  E0_eV: null                # TBD, mean initial kinetic energy
  dE_eV: 2                   # uniform spread width (1 to 2)
  charge: 1                  # signed; -1 for Cl-
  mass_Da: 22.99             # Na+ (NaCl solutions first); 175.1 for protonated arginine later
  launch_offset_um: null     # TBD, distance from model tip apex
  t_end_us: null             # TBD, particle tracing end time (Na+ ~30 us vs ~200 us at 1024 Da)
detector:
  model: Hamamatsu F2225-21P
  mcp_active_diameter_mm: 40 # plate diameter
  sigma_mcp_um: null         # TBD, MCP + phosphor + camera resolution
  mesh_opening_diameter_mm: 10   # TBD: current model has 11
  mesh_open_fraction: null   # TBD, wire transmission
requirements:
  eta_min: null              # TBD
  impact_threshold_eV_per_charge: null   # TBD (literature review); or impact_threshold_mps
  threshold_species_mass_Da: null        # TBD, heaviest species of interest (Na+ 22.99,
                                         # Na2Cl+ ~81, hydrated Na+ clusters?)
  frac_fast_min: 0.90
  optional_constraints: {}   # e.g. {min_fill_fraction: 0.5}
tolerances:
  energy_conservation_rel: null   # TBD
  potential_match_V: null         # TBD
  monotonic_tol_um: null          # TBD
  convergence_rel: null           # TBD
  eval_range_landed_frac: 0.99
```

Thresholds should be fixed before any formal evaluation run. Until then they can be
changed freely, and `ionopt recheck` updates stored results.

## 11. Velocity requirement note

Landing energy depends only on the start and end potentials, so the fast-ion fraction is
set almost entirely by v_mcp_front (and v_tip), not by electrode or mesh voltages. Light
Na+ ions may need a lower MCP front voltage than the current -10 kV to trigger. Encode the
threshold as a bound on the MCP channel in constraints.yaml so the optimizer never proposes
an infeasible value, and keep the checker's per-ion check as a safety net.

## 12. constraints.yaml (chambers, positions, electrodes, supplies)

```yaml
chamber_setups:              # 2 physical chambers, 3 setups
  1:
    name: chamber 1 alone
    z_mcp_mm: [null, null]   # TBD allowed range
    mesh_gap_mm: [null, null]  # TBD, mesh distance in front of the MCP face
    electrode_z_mm: [null, null]  # TBD allowed range for E1..E9 placement
  2:
    name: chamber 2 alone
    z_mcp_mm: [null, null]
    mesh_gap_mm: [null, null]
    electrode_z_mm: [null, null]
  3:
    name: chambers 1 and 2 joined
    z_mcp_mm: [null, null]
    mesh_gap_mm: [null, null]
    electrode_z_mm: [null, null]
mesh:
  min_gap_to_mcp_mm: null    # TBD (mesh_gap lower bound; current model 12.7)
electrodes:
  count: 9                   # identical disks E1..E9, E1 = extractor
  outer_diameter_mm: null    # TBD, from the model
  aperture_diameter_mm: null # TBD
  thickness_mm: null         # TBD
  min_gap_mm: null           # TBD, between adjacent disks
  e1_z_mm: [null, null]      # TBD, allowed extractor position relative to the tip
supplies:
  low_voltage:
    channels: [LV1, LV2, LV3, LV4]
    range_V: [null, null]    # TBD, +/- a few hundred V
    connectable: [tip, e1, e2, e3, e4, e5, e6, e7, e8, e9]   # each uses an LV channel or GND
  high_voltage:
    range_V: [-10000, 10000]
    roles: {HV1: mcp_front, HV2: mcp_back, HV3: phosphor, HV4: mesh}   # fixed, one to one
  mcp_front_V: [null, null]  # TBD, upper limit also set by the velocity requirement
  mesh_V: [null, null]       # TBD
  mcp_back_offset_V: null    # TBD, back = front + offset (detector operation)
  phosphor_offset_V: null    # TBD, phosphor = back + offset
electrical:
  max_field_kV_per_mm: null  # TBD, arcing limit between adjacent electrodes
```

Phase 1 uses this file for optimizer bounds and job validation; Phase 2 adds a validator
for agent proposals.

## 13. Task order for Claude Code

- [ ] 1. Repo skeleton, config system (section 4) with validation, overrides, snapshots
         and `config-check`; schemas; pytest setup.
- [ ] 2. launch.py with tests.
- [ ] 3. electrodes.py (wiring validation and expansion) with tests.
- [ ] 4. MockBackend (with failure injection) and QueueBackend + LocalFSTransport,
         tested with a fake worker that uses the mock.
- [ ] 5. checker.py (derived table, spot statistics, metrics, recheck) with analytic tests.
- [ ] 6. runlog.py and plots.py.
- [ ] 7. optimize.py tested on the mock (must find the known optimum).
- [ ] 8. COMSOL introspection script: print the model tree, parameters, selections,
         studies, release and export nodes, and electrode geometry features for both models.
         Record findings in docs/comsol_api_notes.md. (Requires COMSOL; author runs or
         approves.) Blocked on the electrode rework (section 15); tasks 1-7 need no COMSOL
         and proceed in parallel. Earlier introspection of the 2-lens models (logs/inspect.log,
         scripts/inspect_model.py, dump_features.py, boundary_table.py) is reusable.
- [ ] 9. model_adapter.py and comsol_worker.py; one 2D job end to end, compared to a
         manual GUI run with the same params.
- [ ] 10. Fidelity check (2D vs 3D on about 5 settings).
- [ ] 11. baseline.py: B0 on at least one chamber setup, with promotion of top results to 3D.
- [ ] 12. SSHTransport stub with the same interface and a test using a local directory.

Tests needing COMSOL are marked @pytest.mark.comsol and skipped by default.

## 14. Rules for Claude Code

- Never modify files in models/. Never overwrite a .mph file.
- Before using any COMSOL node tag or property name, confirm it by introspection
  (MPh node properties or the exported Java model file) and record it in
  docs/comsol_api_notes.md. Do not rely on remembered API names.
- No hard-coded physical values in code (dimensions, voltages, thresholds, tolerances).
  They come from config files.
- 3D runs only when explicitly requested (flag or CLI command); default fidelity is 2D.
- No credentials, keys or hostnames in the repo. SSH settings come from the user's SSH
  config or environment variables.
- Every result must be reproducible from job.json, config_snapshot.yaml, the model hash
  and the git commit.
- Ask the author before changing values in spec.yaml or constraints.yaml.

## 15. Open items (author)

- [ ] Electrode rework (replaces the rough 2-lens model in both models): import the real
      electrode STEP (one part, used for all 9) into 3D and place 9 copies by z_e_k inside
      If/EndIf on use_e_k; 2D gets the axisymmetric r-z profile of the same part, generated
      by build_axisym.py. Parameters use_e_k, z_e_k, v_e_k; selections sel_e1 to sel_e9;
      also v_tip (needle is grounded now) and mesh_gap. Redo the 3D mesh refinement on named
      selections, then re-validate 2D vs 3D with compare_axis.py / compare_particles.py.
- [ ] Electrode STEP file, mounting hardware (rods, spacers, materials), minimum gap,
      extractor position range.
- [ ] MCP back and phosphor operating offsets (models currently: front -10 kV, back -5 kV;
      no phosphor).
- [ ] Mesh opening diameter (10 mm in this plan vs 11 mm in the model) and mesh_gap range.
- [ ] Hand-designed B0 templates (section 9.10).
- [x] Build the 2D axisymmetric model (scripts/build_axisym.py; represents all three
      chamber setups through cfg; validated against the refined 3D model).
- [ ] Fill parameter names (section 7), spec values (section 10), constraints (section 12).
- [ ] Initial kinetic energy mean E0, launch offset, and model tip dimensions.
- [ ] sigma_mcp, mesh open fraction, eta_min, impact threshold (literature review on the
      MCP velocity threshold for Na+), heaviest species of interest.
- [ ] Lab machine: core count, OS, network path from the WorkSpace, permission for an
      SSH server or worker service.

## 16. Phase 2 outline (not for Phase 1)

- Constraint validator for structured agent proposals (chamber setup, electrodes used and
  positions, wiring map).
- Planner agent: proposes configurations and bounds, classifies failures as parametric,
  structural or specification problems.
- Critic agent: fresh context, sees checker output, spot statistics, plots and planner
  claims (not its reasoning), returns a structured verdict.
- Editor agent: sandboxed edit scripts that create new .mph variants from the base model,
  with geometry checks and author approval.
- LangGraph state machine, budget and round caps, full logging of prompts, tool calls,
  tokens and cost. Baseline B1 and ablations A1 and A2.
