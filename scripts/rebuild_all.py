#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
scripts/rebuild_all.py
======================
One-shot rebuild and verification pipeline for the MR1 Nanopore Reader:
  1. Validates stack specifications (pin map, ring feeders, pogo gap budget, fluid ports)
  2. Regenerates KiCad coax & alias footprints in Amplifier/ and Interposer/
  3. Verifies build123d CAD geometry agreement with stack_spec
  4. Generates deliverable manifests and footprint exports
  5. Runs the full test suite (unit tests, formal proofs, and CAD collision checks)

Usage:
    ./scripts/run_python.sh scripts/rebuild_all.py          # full rebuild & test
    ./scripts/run_python.sh scripts/rebuild_all.py --check  # check only (fail on drift/error)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src import stack_spec as spec  # noqa: E402
from scripts.generate_footprint import (  # noqa: E402
    build_footprint_file,
    check_library,
    cross_check_cad,
    write_library,
)


def log_step(name: str):
    print(f"\n{'='*70}\n[STEP] {name}\n{'='*70}")


def run_pipeline(check_only: bool = False, skip_tests: bool = False) -> int:
    t_start = time.time()
    steps = []

    # 1. Validate stack specification
    log_step("1. Validating stack_spec.py")
    problems = spec.validate()
    if problems:
        print("[FAIL] stack_spec validation failed:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("[OK] stack_spec is valid (gap window, pin map, coax ring feeders).")
    steps.append(("Stack Specification", "PASS"))

    # 2. Footprint generation / check
    log_step("2. Synchronizing KiCad Footprints")
    if check_only:
        drift = check_library(verbose=True)
        if drift:
            print(f"[FAIL] Footprint library drift detected ({len(drift)} item(s)).", file=sys.stderr)
            return 1
        print("[OK] Footprint libraries are clean (no drift).")
        steps.append(("Footprint Libraries Check", "PASS"))
    else:
        written = write_library(verbose=True)
        build_footprint_file(sync_libraries=False, verbose=False)
        print(f"[OK] Footprint libraries written ({len(written)} updated).")
        steps.append(("Footprint Libraries Write", "PASS"))

    # 3. Verify CAD geometry matches stack_spec
    log_step("3. Verifying build123d CAD vs stack_spec")
    cad_mismatches = cross_check_cad()
    if cad_mismatches:
        print(f"[FAIL] CAD geometry mismatch with stack_spec:", file=sys.stderr)
        for m in cad_mismatches:
            print(f"  - {m}", file=sys.stderr)
        return 1
    print("[OK] build123d CAD geometry matches stack_spec perfectly.")
    steps.append(("CAD vs Spec Verification", "PASS"))

    # 4. Synchronize & Verify PCB Pin Placements
    log_step("4. Verifying PCB Pin Placements")
    from scripts.build_amplifier_kicad import verify_amplifier_pcb
    from scripts.build_interposer_kicad import verify_interposer_pcb
    amp_issues = verify_amplifier_pcb()
    if amp_issues:
        print("[FAIL] Amplifier PCB pin drift detected:", file=sys.stderr)
        for iss in amp_issues:
            print(f"  - {iss}", file=sys.stderr)
        print("[!] To import PCB changes into stack_spec, run: ./scripts/run_python.sh scripts/build_amplifier_kicad.py --sync-spec", file=sys.stderr)
        print("[!] To push stack_spec to PCB, run: ./scripts/run_python.sh scripts/build_amplifier_kicad.py --write", file=sys.stderr)
        return 1
    else:
        print("[OK] Amplifier PCB pins are in sync with stack_spec.")
    steps.append(("Amplifier PCB Pins", "PASS"))

    int_issues = verify_interposer_pcb()
    if int_issues:
        print("[FAIL] Interposer PCB verification failed:", file=sys.stderr)
        for iss in int_issues:
            print(f"  - {iss}", file=sys.stderr)
        return 1
    print("[OK] Interposer PCB is in sync with passive specification.")
    steps.append(("Interposer PCB Pins", "PASS"))

    # 5. Manifest update
    log_step("5. Updating Export Manifest")
    if not check_only:
        ret = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "export_manager.py"), "--manifest"], check=False)
        if ret.returncode != 0:
            print("[WARN] Export manifest generation returned non-zero code.", file=sys.stderr)
            steps.append(("Export Manifest", "WARN"))
        else:
            print("[OK] Export manifest updated.")
            steps.append(("Export Manifest", "PASS"))
    else:
        steps.append(("Export Manifest", "SKIPPED (check-only)"))

    # 6. Full test suite execution
    if not skip_tests:
        log_step("6. Running Full Test Suite (run_tests.py)")
        test_ret = subprocess.run([sys.executable, str(REPO_ROOT / "run_tests.py")], check=False)
        if test_ret.returncode != 0:
            print("[FAIL] Full test suite encountered failures.", file=sys.stderr)
            return test_ret.returncode
        print("[OK] Full test suite passed.")
        steps.append(("Full Test Suite", "PASS"))
    else:
        steps.append(("Full Test Suite", "SKIPPED"))

    t_total = time.time() - t_start
    print(f"\n{'='*70}\nREBUILD SUMMARY ({t_total:.2f}s)\n{'='*70}")
    for name, status in steps:
        print(f"  {name:<30} : {status}")
    print(f"{'='*70}\n[SUCCESS] Rebuild pipeline finished successfully!\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-shot rebuild pipeline for MR1.")
    parser.add_argument("--check", action="store_true", help="Run in check-only mode (fail on drift without modifying files)")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running the full test suite")
    args = parser.parse_args(argv)
    return run_pipeline(check_only=args.check, skip_tests=args.skip_tests)


if __name__ == "__main__":
    raise SystemExit(main())
