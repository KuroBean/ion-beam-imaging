# Known issues and deferred fixes

Problems found while building the Phase 1 models and tools. They are deferred until the
overall agentic structure (plan_v1.md, tasks 8-12) is in place. Each entry: what is wrong,
why it matters, and the fix we have in mind.

Models referred to: 3D = `lens8newMCP_ks_v4_lens_voltages.mph`, 2D = `lens8_axisym_asm.mph`
(built by `scripts/build_axisym.py`).

## Accuracy

1. **3D particle energy error of about ±1 eV.** Ions start at 1 eV, so this error decides
   which ions pass the decelerating step at L9. With the placeholder voltages, MCP arrivals
   ranged from 0 to 101 of 1000 between meshes whose electric fields agree to within 1 V.
   Most of the error builds up in the first 1-2 mm after the needle tip. Refining the tip
   face (0.03 mm) helped. The rest comes from the vacuum between the tip and L2, which
   COMSOL 5.5 cannot refine locally: the beam path is just the middle of the big vacuum
   domain. *Fix:* add a thin beam-cylinder domain along the axis (r about 6 mm, tip to MCP)
   with its own volume mesh size, finest from the tip to L4. Until then, use 2D for
   transmission numbers. The energy check used is `KE + qV - E0` along each trajectory;
   build it into the checker (plan section 9.6).
2. **2D stand-in for the screen cross.** The cross arms are not axisymmetric. In 2D they
   are a solid -1 kV ring of radius `R_cross`. `R_cross` was refit to 24.5 mm
   (`scripts/calibrate_2d.py`) after the MCP-region materials changed. Remaining 2D vs 3D
   difference: on axis up to 64 V, at r = 10 mm up to about 430 V, both right at the
   screen. *Fix:* refit `R_cross` whenever the MCP, screen or dielectrics change. Make this
   part of the fidelity check (task 10).
3. **2D omits non-axisymmetric parts:** the Al2O3 posts (smearing them into a ring made the
   match worse), the rods and bracket, the small tabs on the MCP surround, and the split of
   each deflector into halves. The 2D deflector is one ring at the mean of its two
   half-voltages, so steering can only be studied in 3D.
4. **3D mesh convergence near the MCP has only been checked once.** Refining the MCP face
   changed the potential there by about 30 V; meshes refined further agree to within 1 V.
   A deliberate convergence test is still to be done.

## Model setup that does not match the plan yet

5. **Particle species.** Both models still use m_ion = 1.7e-24 kg (about 1024 Da). Since
   v5 (`scripts/add_3d_params.py`), it is the parameter `m_ion` in both models, along with
   `Z_ion`, `t_end`, `dt_out`, `V_mcp_front`, `V_mcp_back` and `V_screen`. Plan:
   Na+ at 22.99 Da, set from config. Na+ arrives about 6.7 times sooner, so `t_end` can
   shrink (3D 250 µs, 2D 800 µs now).
6. **Needle is grounded.** The plan needs a tip voltage parameter `v_tip` on an LV channel.
   **Done 2026-11-10:** `v_tip` now exists in 2D v2 (`es/pot_needle`) and in 3D v6 (`es/pot_tip`).
7. **MCP back is at -5 kV with the front at -10 kV.** Set both from the constraints offset
   (plan section 12). Phosphor not modelled.
8. **Screen-mesh offset `mesh_gap`.** **Done 2026-11-12.** 2D since v2. 3D: the author's GUI edit
   in `lens8newMCP_ks_v6_tip.mph` is verified (`scripts/verify_3d_geometry.py`): after a geometry
   rebuild, all 58 domains match v5 and the disc sits at `mcp_z - mesh_gap` (503.1-503.3 mm).
   The file was saved without a mesh and with a stale geometry state; the adapter now rebuilds
   when the stored mesh is empty. The edit put the MCP plate under ULTEM; it is now lead glass
   (`mat3`, eps 8) on the box selection `sel_mcp_plate` (`scripts/set_mcp_material_3d.py`,
   saved in place with a mesh; backup `lens8newMCP_ks_v6_tip_backup_20261112.mph`).
   Still open: the opening diameter is 11 mm in the model, 10 mm in the plan.
9. **3D release.** The 3D model uses a Particle Beam (1000 ions, Gaussian), not the plan's
   launch grid from a release file. The release-file format is now verified for both 2D
   and 3D (task 8, `scripts/verify_release_file.py`). *Fix:* the adapter disables `pbeam1`
   and adds a `ReleaseFromDataFile` node in memory for each job (docs/comsol_api_notes.md §5).
10. **The search space no longer matches the hardware.** Plan and `optimize.py` assume 9
    identical electrodes at free positions `z_e_k` with on/off flags `use_e_k`. The real
    assembly is a fixed stack. Its free variables are the voltages L1_v..L9_v and
    D1a_v..D2b_v, `lens_gap`, `mesh_gap` and z_mcp, and the deflectors are new.
    **Done 2026-11-10.** `JobSpec.positions` is now `{lens_gap, z_mcp, mesh_gap}`. The wiring
    covers the tip and e1..e9 (unlisted nodes are GND), and the deflectors are grounded.
    `constraints.electrodes.stack` holds the CAD geometry. The registry maps onto the model
    names (`L<k>_v`, `V_screen`, ...). `electrodes.py`, `optimize.py`, the mock and the tests
    were updated to match.
11. **Placeholder voltages** (L1 -120 V, L2-L8 -40 V, L9 0 V). Only about 1% of ions reach
    the MCP. Real operating points come from the optimizer (task 11).

18. **Emission target not reachable at 1 eV (2026-11-10).** The target is a Gaussian-like
    beam with 20 deg HWHM (40 deg FWHM) just in front of L1. With E_ion = 1 eV, L1 at -120 V
    and a grounded tip, the ions reach about 114 eV at L1. Even a launch at 89.5 deg arrives at
    only 10.3 deg, so no launch spread can meet the target. 2D maps (`scripts/calibrate_emission.py`,
    `logs/emission_fit.*`) give the best match vs the initial energy:
    - 1 eV: impossible (max 10.3 deg).
    - 5 eV: max 21.5 deg; best is about 15-16 deg HWHM.
    - 15 eV: launch HWHM 52 deg (launch.py style, no cut) gives 19.2 deg.
    - 40 eV: launch HWHM 34 deg gives 19.9 deg, a good match.

    Only the ratio of voltage to energy matters, so the calibration is tied to the
    extraction voltages. The 2D map transfers to 3D: per ion, angles agree within about 3%.
    COMSOL's "Gaussian" Particle Beam slopes have heavier tails than a true Gaussian, and the
    slope std per axis is 0.611 x xmp. *Fix:* decision needed (initial energy, emitter model,
    or where the 20 deg applies).

19. **Particle solver tolerance (2026-11-10).** The default `rtol` of 1e-5 gave errors of
    up to 135 eV (1.3%) at the MCP. It also gave up to 4.8 eV for ions ending on electrodes,
    and some 2D ions picked up about 10 eV within the first mm after the tip. At 1e-9 these
    drop to 19 eV and 0.05 eV, with the same runtime in 2D. The worker now sets
    `backend.worker.particle_rtol` (1e-9).
    - **3D, tested 2026-11-12** (`scripts/run_3d_job.py`, cfg 3, 603 Na+ ions, placeholder
      voltages). Tolerance matters even more in 3D. At 1e-5, MCP ions are off by a median
      of 2.5% (255 eV) and at most 8.4%, landing positions move by a median of 270 µm
      (p90 970 µm) vs 1e-9, and 5.5% of ions change fate. At 1e-9 the error is a median of
      0.2% (20 eV) and at most 1.5% (147 eV); ions ending on electrodes are off by up to
      2.8 eV. That is still several times 2D, so the remainder is mesh (#1). Particle solve:
      79 s at 1e-5 vs 1060 s at 1e-9; whole job about 1230 s with the stored mesh (+260 s
      if the mesh must be built). 1e-7 untested.
    - Remeshing alone (plus ULTEM -> lead-glass MCP plate) moved MCP landings by a median of
      27 µm (p90 100 µm): a rough floor for 3D-to-3D differences.

## Geometry and configuration

12. **cfg 2 is unusable.** The MCP (z = 215.9 mm) sits inside L8/L9. cfg 1 fits with the
    deflectors removed: L9 ends 7 mm before the screen hub. *Fix:* move the MCP for cfg 2,
    or drop cfg 2 from `config/constraints.yaml` so the optimizer cannot pick it. Neither
    has been done.
13. **Some 3D selections are still numeric:** the 304L material and the particle-release
    face, and possibly others set in the GUI. Any geometry change renumbers entities and
    silently breaks them. *Fix:* point them at named or geometric selections. For example,
    `sel_tipface` already exists for the release face.
14. **Further mesh savings are possible.** The chamber-2 solid (about 170k elements) and
    the vacuum outside the chambers (about 200k) could be coarser. `scripts/mesh_stats_3d.py`
    shows where the elements go.

## Housekeeping

15. **Model files sit at the repo root.** The 3D v4 file is 1.3 GB. The plan wants a
    read-only `models/` folder; jobs must copy the model, never edit it. `run_3d_v4.py`
    currently edits v4 in place.
16. **Old scripts.** `touchup_3d.py` (numeric IDs, old geometry) is obsolete. The compare
    scripts default to the old model paths; pass the paths explicitly.
17. **STEP files are not committed** (`lens assembly *.step`, `front_flange_assembly.step`).
