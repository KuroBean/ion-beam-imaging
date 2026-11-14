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
      if the mesh must be built). 1e-7: particle solve 255 s, energy error similar to 1e-9
      (median 0.28%), but landings move by a median of 62 µm (p90 230 µm) vs 1e-9, 1.5% of
      ions change fate, and the score jumps from 36 to 100. The score amplifies landing noise,
      so 3D stays at 1e-9.
    - Remeshing alone (plus ULTEM -> lead-glass MCP plate) moved MCP landings by a median of
      27 µm (p90 100 µm): a rough floor for 3D-to-3D differences.

20. **Pre-acceleration (2026-11-12).** **Double counting fixed:** with `spec.launch.preaccel`, the model
    tip is held at V_tip - gain/q (`electrodes.model_tip_potential`), so E0 + q V_tip is conserved.
    Model tip size (2D, `scripts/study_2d.py tip`, B tip +200 V L3 -300 V): r_tip 200/100/50/25 um
    give the same fate for 96-100% of rays and MCP landings within ~0.1-0.2 mm (one edge ray
    ~1 mm), while the 2D mesh grows 212k -> 578k and remeshing 26 s -> 196 s. Keep 100 um.
21. **The emission model decides transmission (2026-11-12).** With pre-acceleration, ions leave the
    tip region nearly ballistic (energy ~0.67 of V_tip - V_E1, field scale-invariant), so the
    launch cone reaches E1 almost unchanged. E1's aperture (r 5 mm, 9 mm plate, 13.48 mm away)
    then accepts only ~12.5 deg (23% of a 20 deg HWHM beam), and the 5 mm bore of the stack stops
    most of the rest: in 33 cfg 3 settings (tip +10..+200 V, E1 -110 V, Einzel L2-L4 families,
    `logs/study_2d_scan.json`, `logs/study_2d_grid.json`) at most 8% reaches the MCP (theta <= 6 deg).
    Without pre-acceleration the same setting sends 96% to the MCP: 2 eV ions at the blunt 0.1 mm
    tip are bent strongly by its field. Which picture holds depends on the real emitter shape.
    Moving the stack closer helps: straight-ray acceptance 14.7/17.4/19.7 deg at lens_gap 10/7/5 mm.
22. **What the 20 deg HWHM means (2026-11-13, author still to confirm with the lab).** Two pictures:
    (a) 'launch': 20 deg HWHM is the beam spread at the model launch point (used until 2026-11-13);
    (b) 'meniscus': the ~2 eV ions just outside the meniscus move in directions with 20 deg HWHM, and
    the emitter's own field bends them toward the axis while it accelerates them. The author chose (b)
    (collaborators see ~93% transmission, which (a) cannot give) and it is now the spec
    (`spec.launch.emission_angle_at: meniscus`). Each grid angle theta0 is traced from the apex of the
    hyperboloid emitter (r_e 50 nm, extractor plane at lens_gap) to the launch distance s
    (`ionopt.launch.trace_preacceleration`); the ion is launched with that direction (column
    `theta_launch_deg`) while theta_deg, the weights and the checker's mapping stay at the meniscus
    angle. 20 deg becomes ~9.2/7.4/5.4/4.1 deg at V_tip - V_E1 = 35/66/150/300 V (not the ~3 deg I
    estimated first). Open points:
    - The angle keeps shrinking slowly with distance (the needle field keeps accelerating): s = 50 /
      275 / 1000 um gives 7.7/7.4/7.2 deg at 66 V. s stays 275 um (the old formula).
    - The hyperboloid is a thin needle (asymptotic half angle ~0.1 deg). A pulled pipette is a cone of
      a few degrees with a glass wall, so the field near the apex falls off differently and the bending
      will differ. *Fix:* build a 2D axisymmetric near-tip model with the real taper (apex radius,
      taper angle, glass, the extractor) and replace the analytic trace by a table from it; needs the
      pipette geometry from the author.
    - Where on the meniscus the ions start (point at the apex now) also matters.
23. **2D vs 3D fidelity check (task 10, 2026-11-13; `logs/fidelity_20261113_task10.json`).** Five
    cfg 3 settings from the 2D search, launch picture (a) of #22, 26 theta x 8 phi in 3D. All 10 jobs valid;
    3D 15-17 min each (field 130-160 s, particles 720-870 s, rtol 1e-9).
    - **Transmission: 2D is good enough for screening.** MCP fraction 3D - 2D = +0.9 to +5.3 points (3D
      always higher), eta +3% to +27% relative; per-ray fate agreement 88-96%. The disagreement sits at
      the edge of the transmitted cone (theta 12-16 deg): in 3D some azimuths still get through and land
      at r 5-15 mm (a halo 2D does not have).
    - **Mean mapping r(theta): within 0.6 mm** (rms 0.20-0.34 mm) on the rays both transmit, mostly the
      3D beam offset: the on-axis ray lands 0.38-0.58 mm off axis, spot centroid 0.28-0.79 mm.
    - **Resolution: 2D is not usable.** dtheta in 3D is 3-5x the 2D value (median), because the 8
      azimuths of one theta land at different radii (offset and non-axisymmetric parts), which 2D
      cannot show. Scores differ by -93% to +550%; all five mappings fold (non-monotonic), so the score
      hinges on single points. Spot rms is 1.3-3.2x larger in 3D.
    - *Consequence:* use 2D for transmission and the mean mapping only; score resolution in 3D, or add
      an azimuthal-blur term calibrated from 3D to the 2D score. Find out whether the ~0.5 mm offset is
      physical (posts, rods, split deflectors, MCP tabs: then the deflectors can correct it) or mesh
      asymmetry (then refine). Repeat the check with settings for picture (b), where the beam is narrower.

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
