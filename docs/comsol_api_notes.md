# COMSOL API notes (task 8)

Confirmed node tags, property names and API calls for the two base models. Every name
here was read from the live models with `scripts/introspect_models.py` (COMSOL 5.5,
MPh 1.4.0) on 2026-11-10. The adapter (task 9) may use only names recorded here (plan
section 14). Re-run the introspection after any model edit and update this file.

| key | file | size | load | geometry |
|---|---|---|---|---|
| 2d | `lens8_axisym_asm.mph` (built by `scripts/build_axisym.py`) | 56 MB | 7 s | 2D axisymmetric, 19 domains, 194 boundaries, 212k triangles |
| 3d | `lens8newMCP_ks_v4_lens_voltages.mph` | 1.1 GB | 10 s (lazy; walking the tree took ~5 min) | 58 domains, 2454 boundaries, 2.41M tetrahedra |

Both models are stored with `cfg = 3`.

Full dumps: `logs/introspect_2d.txt`/`.json` and `logs/introspect_3d.txt`/`.json`. They are
not committed (`logs/` is git-ignored); re-run the script to regenerate them.
The JSON files can be diffed after a model edit.

Scripts:
- `scripts/introspect_models.py [2d] [3d] [--path x.mph]`: read only, never saves.
- `scripts/verify_release_file.py 2d|3d`: works in memory, never saves. It writes a
  6-ion release file through `ionopt.launch.write_release_file`, runs the particle
  study for 0.1 µs, and compares the t = 0 state with the file.

## 1. Session setup (confirmed)

- The COMSOL root comes from `config/paths.yaml` (`comsol_root`). Put
  `<root>/java/win64/jre/bin` on PATH **before** `import mph`; COMSOL 5.5 bundles Java 8,
  so keep `jpype1 < 1.6`.
- `client = mph.start(cores=None)`, then `model = client.load(path)` and `j = model.java`.
  To drop a model without saving it, call `client.remove(model)`.
- Read a global parameter in SI with `float(j.param().evaluate(name))`.
  `model.evaluate(name)` returns an array over the dataset instead, so don't use it for parameters.
- Set a parameter with `j.param().set(name, "value[unit]")`.
- `selection.dimension()` returns an `int[]` with one entry. `selection.entities()` with no
  argument fails; call `selection.entities(dim)`.

## 2. Shared structure (identical tags in both models)

| item | tag | notes |
|---|---|---|
| component | `comp1` | |
| geometry | `geom1` | |
| mesh | `mesh1` | |
| electrostatics | `es` | |
| particle tracing | `cpt` | particle properties `pp1`, electric force `ef1`, default wall `wall1` (Freeze) |
| electrostatics study | `std1`, step `stat` (Stationary) | activate = es on, cpt off. The plan wanted `std_es`; we keep `std1` |
| particle study | `std2`, step `time` (Transient) | activate = es off, cpt on. Field from `sol1` (solver `sol2/v1`: `notsolmethod=sol`, `notsol=sol1`). The plan wanted `std_pt` |
| output times | `j.study("std2").feature("time")`, property `tlist` | 2D: `range(0,dt_out,t_end)` (params). 3D: literal `range(0,0.5[us],250[us])` |
| solutions | `sol1` (es), `sol2` (particles) | datasets `dset1`, `dset2` |
| solve | `j.study("std1").run()`, then `j.study("std2").run()` | `std2.run()` alone used the stored `sol1` (verified in `verify_release_file.py`) |

**Decision:** keep the tags `std1`/`std2` and record them in the adapter. Renaming them
would mean editing the 3D model and gains nothing.

## 3. Parameters

All names are global parameters. "—" means the parameter does not exist; the value is a
literal on a node.

| plan / registry name | 2D | 3D | notes |
|---|---|---|---|
| cfg | `cfg` | `cfg` | 1 tube, 2 sphere, 3 both. cfg 2 is unusable (KNOWN_ISSUES #12) |
| tip position | `tip_z` = 105 mm | `tip_z` = 105 mm | z_model = z_plan + tip_z |
| z_mcp | `mcp_z` (derived), free input `z_mcp_c1` (cfg 1 only) | same | the 2D formula `z_c2+z_c2_center` equals the 3D `if(cfg==2, z_c2_center, z_c2_center+L_c1)` for cfg 2 and 3 |
| lens position | `lens_gap` = 13.482 mm | `lens_gap` | 2D: `z_asm = tip_z+lens_gap+136.165[mm]`. 3D: `mov7.newposz = tip_z+lens_gap` |
| electrode voltages | `L1_v` .. `L9_v` | `L1_v` .. `L9_v` | |
| deflector voltages | `D1a_v D1b_v D2a_v D2b_v` | same | 2D applies the mean of each pair to one ring |
| v_mcp_front | `V_mcp_front` | — (`es/pot5` V0 = `-10000`) | |
| v_mcp_back | `V_mcp_back` | — (`es/pot6` V0 = `-5000`) | |
| v_mesh (screen mesh + cross) | `V_screen` | — (`es/pot7`, `es/pot8` V0 = `-1000`) | |
| v_tip | — (needle grounded, `es/gnd_needle`) | — (`es/gnd2`) | KNOWN_ISSUES #6 |
| mesh_gap | — (`meshline` at `mcp_z-12.7`) | — (`cyl23` disc at offset 18.5 mm, 0.2 mm thick, on work plane `wp2`, which sits on face `mov5(1)` of the moved MCP part) | KNOWN_ISSUES #8 |
| ion mass | `m_ion` (`pp1.mp = m_ion`) | — (`pp1.mp = 1.7e-24`) | KNOWN_ISSUES #5 |
| charge number | `Z_ion` (`pp1.Z = Z_ion`) | — (`pp1.Z = 1`) | |
| t_end | `t_end`, `dt_out` | — (literal tlist) | |
| 2D only | `R_cross`, `eps_holder`, `eps_surround`, `E_ion`, `N_ion` | | |

The 3D v4 model is missing the parameters `V_mcp_front`, `V_mcp_back`, `V_screen`, `m_ion`,
`Z_ion`, `t_end` and `dt_out`.

**Done 2026-11-10:** `scripts/add_3d_params.py` wrote `lens8newMCP_ks_v5_params.mph`. It adds
these 7 parameters with the 2D names and values equal to the old literals (`t_end = 250[us]`,
`dt_out = 0.5[us]`). It rebinds `es/pot5.V0`, `pot6.V0`, `pot7.V0`, `pot8.V0`, `cpt/pp1.mp` and
`pp1.Z`. Both `std2/time.tlist` and `sol2/t1.tlist` are now `range(0,dt_out,t_end)`. The
physics is unchanged, so v5 keeps v4's mesh and solutions. v4 itself was not saved.

**Note:** the solver copy `sol2/t1.tlist` has its own tlist. Set it together with the study
step, as `run_3d_v4.py` and `add_3d_params.py` do.

## 4. Electrodes: selections and physics nodes

The plan names `sel_e1`..`sel_e9` don't exist in either model. Electrode `L<k>` maps to:

| electrode | 2D boundary selection | 2D potential | 3D boundary selection | 3D potential | 3D wall |
|---|---|---|---|---|---|
| L1 | `geom1_L1_bnd` | `pot_L1` | `geom1_imp8_Imported1_8_bnd` | `pot3` | `wall2` |
| L2 | `geom1_L2_bnd` | `pot_L2` | `geom1_imp8_Imported1_6_bnd` | `pot9` | `wall4` |
| L3 | `geom1_L3_bnd` | `pot_L3` | `geom1_imp8_Imported1_7_bnd` | `pot10` | `wall9` |
| L4 | `geom1_L4_bnd` | `pot_L4` | `geom1_imp8_Imported1_9_bnd` | `pot11` | `wall_L4` |
| L5 | `geom1_L5_bnd` | `pot_L5` | `geom1_imp8_Imported1_1_bnd` | `pot12` | `wall_L5` |
| L6 | `geom1_L6_bnd` | `pot_L6` | `geom1_imp8_Imported1_4_bnd` | `pot13` | `wall_L6` |
| L7 | `geom1_L7_bnd` | `pot_L7` | `geom1_imp8_Imported1_2_bnd` | `pot14` | `wall_L7` |
| L8 | `geom1_L8_bnd` | `pot_L8` | `geom1_imp8_Imported1_5_bnd` | `pot15` | `wall_L8` |
| L9 | `geom1_L9_bnd` | `pot_L9` | `geom1_imp8_Imported1_3_bnd` | `pot16` | `wall_L9` |
| D1a / D1b | `geom1_D1_bnd` (one ring) | `pot_D1` = mean | `..._14_bnd` / `..._17_bnd` | `pot17` / `pot18` | `wall_D1a` / `wall_D1b` |
| D2a / D2b | `geom1_D2_bnd` (one ring) | `pot_D2` = mean | `..._16_bnd` / `..._15_bnd` | `pot19` / `pot20` | `wall_D2a` / `wall_D2b` |
| rods + bracket | — | — | `sel_asm_gnd` (component Union) | `gnd_asm` (Ground) | `wall_asm` |

- In 3D the imported part names carry labels: the selection `geom1_imp8_Imported1_<k>_bnd`
  has the label `"L<n> (Import lens assembly)"`, `"D1a (...)"`, and so on. The adapter
  should **look up the tag by label at load time** and assert the mapping above, so it
  does not depend on the import order. The 2D tags follow the pattern `geom1_<name>_bnd`.
- Deflectors exist only for cfg 3. 2D: `if_defl` (`cfg!=1&&cfg!=2`). 3D: `if4`/`del4`
  delete them for cfg 1 and 2. Their selections are empty in cfg 1 and 2.
- The adapter does not need to touch the potential nodes. Voltages go in through the
  parameters `L<k>_v` and `D..._v`, which every node already references.
- Other surfaces:

| surface | 2D | 3D |
|---|---|---|
| MCP front | `geom1_bnd_mcpfront` (`pot_mcpf`) | `geom1_sel3` (`pot5`) |
| MCP back | `geom1_bnd_mcpback` (`pot_mcpb`) | `geom1_sel4` (`pot6`) |
| screen mesh | `geom1_meshline_bnd` (`pot_mesh`; a transparent line) | `adj3` (`pot8`; disc domains `geom1_sel5`) |
| screen cross | `geom1_hub_bnd` (`pot_hub`, effective ring `R_cross`) | `adj2` (`pot7`) |
| needle | `geom1_needle_bnd` (`gnd_needle`) | `adj5` (`gnd2`) |
| tip face | `geom1_sel_tip` (edge) | `sel_tipface` (Intersection, 1 face) |
| particle domain | `geom1_sel_vac` | `ef1` on 58 domains by number |

## 5. Particle release

**2D (confirmed and verified):** node `cpt/relf1`, type `ReleaseFromDataFile`.

| property | value |
|---|---|
| `Filename` | absolute path |
| `icolp` | `JInt(0)` (positions start at column 0) |
| `InitialVelocity` | `"FromFile"` |
| `icolv` | `JInt(2)` (2D), `JInt(3)` (3D) |
| `ReleasedParticleProperties` | `pp1` |

- After setting the file, call `rel.importData()`. Integers must be passed as `jpype.JInt`.
- The file is whitespace-separated, uses `%` for comments, has one row per ion, and is in
  model units (mm for positions, m/s for velocities).
- `verify_release_file.py 2d` result: **PASS**. 6 particles came back in file row order
  with the expected r, z (= z_plan + tip_z), vr and vz. Worst error was 4e-8 m/s, i.e.
  exact. So `launch.write_release_file(df, path, "2d", z_shift_m=tip_z)` is correct
  as written.
- The stored model points `relf1` at `data/release_from_3d.txt` (the old 3D-beam
  equivalent). The adapter must always set `Filename` itself.

**3D:** the model has no data-file release. It uses `cpt/pbeam1` (ParticleBeam, N = 1000,
El = 1[eV], `xm` = 50[nm]), and its selection is **boundary 1013 by number**
(KNOWN_ISSUES #9, #13). Adapter plan: disable every active release feature and create
`relf1` (`ReleaseFromDataFile`) with `icolv = 3`. The 3D check, `verify_release_file.py 3d`
on the 3D model, gave **PASS**: 6 particles in row order with the expected x, y, z (= z_plan + tip_z), vx, vy, vz (max error 5e-8 m/s), with `pbeam1` disabled and a new `ReleaseFromDataFile` node using `icolp = 0` and `icolv = 3` (the std2 run for 0.1 µs took 36 s). So `launch.write_release_file(df, path, "3d", z_shift_m=tip_z)` is correct as written. `cpt.create(tag, "ReleaseFromDataFile")` takes no dimension argument.

**Particle species:** set `pp1.mp` and `pp1.Z` through the parameters `m_ion` and `Z_ion`
(2D already does this; 3D has literals). `ParticleSpecies = UserDefined`.

## 6. Walls and the axis

| model | axis | walls | electric force |
|---|---|---|---|
| 2D | `cpt/axi1` (AxialSymmetry), `WallCondition = Bounce` (plan §8 ✔) | `cpt/wall1`: `Freeze` on the exterior boundaries. No separate wall nodes on the electrodes; they are not part of the vacuum domain, so their surfaces are exterior | `ef1` on `geom1_sel_vac`, `E_src = root.comp1.es.Er` |
| 3D | — | `Freeze` everywhere: `wall1` (38 boundaries, by number), `wall2..wall_asm` on named selections, `wall5` (MCP and holder, `adj4`), `wall6` (cross, `adj2`), `wall7`/`wall8` (chambers) | `ef1`, `E_src = root.comp1.es.Ex` |

Plan §8 ✔ for the 3D walls. The 3D screen mesh disc (`geom1_sel5`) is **not** a wall, so
ions pass through it (transparent).

## 7. Reading results (no export nodes needed)

Neither model has export nodes; 3D only has `anim1` (Animation). Following plan §8, the
adapter reads data with the API and writes the `exp_*` files itself. Confirmed pattern
(from `compare_particles.py` and `verify_release_file.py`):

```python
ds = j.result().dataset().create("part_x", "Particle"); ds.set("solution", "sol2")
ev = j.result().numerical().create("pev_x", "Particle")
ev.set("data", "part_x")
ev.set("innerinput", "all")   # all output times; "first" = t0 only (confirmed)
ev.set("evaluate", "all")     # (used with innerinput all)
ev.set("expr", "qz"); arr = np.array([list(r) for r in ev.getReal()])   # [particle, time]
# remove both temporary nodes afterwards
```

- Expressions:
  - 2D: `qr`, `qz` (mm), `cpt.vr`, `cpt.vz`.
  - 3D: `qx`, `qy`, `qz`, `cpt.vx`, `cpt.vy`, `cpt.vz`.
  - Particles that have not been released, or that are frozen, return NaN or hold their
    last position (see `compare_particles.py`).
  - `cpt.Ep` (kinetic energy) and `V` along the trajectory are used for the energy check
    in KNOWN_ISSUES #1.
- Axis potential: use a CutPoint dataset (`CutPoint2D`/`CutPoint3D`, see
  `compare_axis.py::_points`) on `dset1`, then evaluate `V` and `es.normE`.
- Existing 3D datasets: `dset1`, `dset2`, `part1` (Particle on `sol2`), and cut planes
  `cpl1` (tip_z+1 mm) and `cpl2` (mcp_z-1 mm).

## 8. Materials (3D) and dielectrics (2D)

| model | material | selection |
|---|---|---|
| 3D | `mat1` 304L, eps 1 | 42 domains **by number** |
| 3D | `mat2` Pyrex, eps 4.6 | `geom1_sel1` (needle) |
| 3D | `mat6` ULTEM 1000, eps 3.15 | `geom1_sel12_dom` (the holder ring) |
| 3D | `mat7` Al2O3, eps 9.4 | `geom1_sel13` (cross posts) |
| 3D | `mat8` Al2O3, eps 9.4 | `geom1_sel14` (MCP surround) |
| 3D | `mat5` polyimide | `geom1_sel13`; overridden by `mat7`, so it covers 0 domains |
| 3D | `mat3` Leaded | 0 domains |
| 2D | `ccn2`, `ccn3` (no materials) | `geom1_ring_dom` (`eps_holder`), `geom1_surround_dom` (`eps_surround`). Conductors are excluded from `es` through `csel_cond` |

## 9. Gaps between the models and plan section 8 (input for task 9)

| # | gap | proposed handling |
|---|---|---|
| 1 | Named selections `sel_tip`, `sel_e1..9`, `sel_mesh_plane`, `sel_mesh_frame`, `sel_mcp_face`, `sel_walls` don't exist | Adapter-side map per fidelity (section 4 tables), with 3D tags resolved by label. No model edit needed |
| 2 | Studies are `std1`/`std2`, not `std_es`/`std_pt` | Adapter constants (section 2) |
| 3 | 3D: no data-file release; `pbeam1` on a numeric boundary | Adapter disables `pbeam1` and creates `relf1` in memory per job (verified, section 5) |
| 4 | 3D v4: MCP, screen, mass, charge and time are literals | Done in v5 (`scripts/add_3d_params.py`, section 3). `config/paths.yaml` still points `models.3d` at v4 |
| 5 | `v_tip` and `mesh_gap` don't exist in either model | Geometry/physics edits (KNOWN_ISSUES #6, #8). Both are needed before those become search variables |
| 6 | 3D numeric selections: `mat1`, `wall1`, `zc1`, `ccn1`/`init1`/`ef1` domains, `size3`, `pbeam1` | KNOWN_ISSUES #13. Safe while the geometry is unchanged; any cfg or geometry change can renumber them. The adapter only changes parameters that the geometry doesn't renumber (voltages, mass, tlist) |
| 7 | Changing `cfg` or `lens_gap` rebuilds the geometry | Changing `cfg` deletes or adds chambers and deflectors, and the 3D numeric selections above are then **unchecked**. Treat 3D cfg changes as unsafe until #6 is fixed; 2D is safe (all selections named) |
