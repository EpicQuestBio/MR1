# openscad-legacy (FROZEN)

> **Deprecated. Kept for history only. Do not use it as a geometry reference.**

The active design is the `build123d` model in `src/`, driven by `src/stack_spec.py`
(pin map, coax rings, spacer stack, fluid ports). This directory is **not** part of
`make export`, `scripts/rebuild_all.py` or `run_tests.py`. Its geometry will drift and
may disagree with the current PCBs.

`scripts/export_all.js` refuses to run unless `MR1_ALLOW_LEGACY_SCAD=1` is set.
See `REFACTOR_PLAN.md` (P6).
