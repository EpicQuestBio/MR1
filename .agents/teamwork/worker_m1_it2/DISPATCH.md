## 2026-10-15T02:02:40Z
You are Worker 2 (Milestone 1 Remediation Worker).
Your working directory is: /home/loki/Projects/daemon-pore/.agents/teamwork/worker_m1_it2

Read:
- Original Request: /home/loki/Projects/daemon-pore/.agents/teamwork/ORIGINAL_REQUEST.md
- Project Scope: /home/loki/Projects/daemon-pore/PROJECT.md
- Explorer 1 Handoff: /home/loki/Projects/daemon-pore/.agents/teamwork/explorer_m1_it2_1/handoff.md
- Explorer 2 Handoff: /home/loki/Projects/daemon-pore/.agents/teamwork/explorer_m1_it2_2/handoff.md
- Explorer 3 Handoff: /home/loki/Projects/daemon-pore/.agents/teamwork/explorer_m1_it2_3/handoff.md

You exclusively own and may edit the following files:
- `src/housing.py`
- `Amplifier/Amplifier.kicad_pcb`
- `Interposer/Interposer.kicad_pcb`
- `scripts/build_interposer_kicad.py`
- `tests/test_legacy_feature_parity.py`
- `tests/test_interposer_kicad.py`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your specific tasks:
1. In `src/housing.py`:
   Update the cavity cutout in `Housing_Lid_Reader()` to cut through-all:
   ```python
   with Locations((0.0, -27.5, 0.0)):
       Box(13.5, 3.0, 100.0, mode=Mode.SUBTRACT)
   ```
   Ensure the upper neck cylinder (Z in [22.6, 30.2]mm) is completely clear with 0.00 mm³ obstruction.
2. In `Amplifier/Amplifier.kicad_pcb`:
   Refill copper zones to eliminate all stale copper fill points in the cavity zone using `kicad-cli pcb drc --refill-zones --save-board Amplifier/Amplifier.kicad_pcb` (or text clipping if needed), verifying 0 copper points exist in [157.75, 171.25] x [81.475, 84.475]mm.
3. In `Interposer/Interposer.kicad_pcb`:
   Synchronize `Edge.Cuts` contour to match the 13.5mm x 3.0mm cavity with continuous closure (0 degree != 2 endpoints).
4. In `scripts/build_interposer_kicad.py`:
   Add CLI argument handling using `argparse`: default execution is a dry-run (exit 0 without writing files), requiring `--write` to write to `Interposer/`, and supporting `--out-dir`.
5. In `tests/test_legacy_feature_parity.py`:
   Extend `cable_probe` to cover the full vertical extent through the neck ($Z \in [-10.0, 30.2]\text{ mm}$) and add an explicit test probe in the upper neck ($Z \in [22.0, 30.2]\text{ mm}$).
6. In `tests/test_interposer_kicad.py`:
   Add `test_pcb_cavity_copper_clearance` asserting 0 traces, vias, or copper fill points in $[157.75, 171.25] \times [81.475, 84.475]\text{ mm}$, and add `test_interposer_pcb_edge_cuts_continuity`.
7. Verify all changes by running:
   `.venv/bin/python -m unittest tests/test_geometry.py tests/test_golden_stl_bounds.py tests/test_legacy_feature_parity.py tests/test_interposer_kicad.py`
   `.venv/bin/python run_tests.py`
   Ensure 100% passing tests with 0 failures, 0 regressions, and 0 CAD collisions.
8. Write `changes.md` and `handoff.md` in `/home/loki/Projects/daemon-pore/.agents/teamwork/worker_m1_it2/` and send a completion message back.
