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

5. **Particle species.** Both models still use m_ion = 1.7e-24 kg (about 1024 Da). Plan:
   Na+ at 22.99 Da, set from config. Na+ arrives about 6.7 times sooner, so `t_end` can
   shrink (3D 250 µs, 2D 800 µs now).
6. **Needle is grounded.** The plan needs a tip voltage parameter `v_tip` on an LV channel.
7. **MCP back is at -5 kV with the front at -10 kV.** Set both from the constraints offset
   (plan section 12). Phosphor not modelled.
8. **Screen-mesh offset `mesh_gap` is not a model parameter yet.** The mesh sits at
   mcp_z - 12.7 mm. The opening diameter also differs: 11 mm in the model, 10 mm in the
   plan.
9. **3D release.** The 3D model uses a Particle Beam (1000 ions, Gaussian), not the plan's
   launch grid from a release file. The 2D release-file format has been checked; the 3D
   format has not (task 8).
10. **The search space no longer matches the hardware.** Plan and `optimize.py` assume 9
    identical electrodes at free positions `z_e_k` with on/off flags `use_e_k`. The real
    assembly is a fixed stack. Its free variables are the voltages L1_v..L9_v and
    D1a_v..D2b_v, `lens_gap`, `mesh_gap` and z_mcp, and the deflectors are new.
    *Fix:* rework `config/parameters.yaml`, `config/constraints.yaml`, `electrodes.py` and
    `optimize.py` before task 9/11.
11. **Placeholder voltages** (L1 -120 V, L2-L8 -40 V, L9 0 V). Only about 1% of ions reach
    the MCP. Real operating points come from the optimizer (task 11).

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
