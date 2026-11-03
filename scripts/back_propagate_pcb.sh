#!/usr/bin/env bash
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

# =============================================================================
# MR1 Nanopore Reader - PCB Back-Propagation & Synchronization Utility
# =============================================================================
# Reads manual edits from Amplifier/Amplifier.kicad_pcb (pin positions,
# grounding, driven guards), back-propagates them into the single source of
# truth (src/stack_spec.py), regenerates mating Interposer landing pads/routes,
# synchronizes footprint libraries, and verifies CAD geometry and test suite.
#
# Usage:
#   ./scripts/back_propagate_pcb.sh                   # sync and run full rebuild
#   ./scripts/back_propagate_pcb.sh --check           # check-only (dry run)
#   ./scripts/back_propagate_pcb.sh --skip-tests      # sync without running test suite
#   ./scripts/back_propagate_pcb.sh --pcb path/to.pcb # custom PCB path
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RUN_PY="${SCRIPT_DIR}/run_python.sh"
DEFAULT_PCB="${REPO_ROOT}/Amplifier/Amplifier.kicad_pcb"
PCB_PATH="${DEFAULT_PCB}"
CHECK_ONLY=false
SKIP_TESTS=false

print_usage() {
    cat << 'EOF'
Usage: ./scripts/back_propagate_pcb.sh [OPTIONS]

Back-propagates manual PCB layout changes into procedural generation scripts:
  1. Imports pin coordinates and guarding from Amplifier PCB into src/stack_spec.py
  2. Verifies Amplifier PCB consistency with stack_spec
  3. Synchronizes KiCad footprint libraries in Amplifier/ and Interposer/
  4. Regenerates Interposer PCB landing pads and dynamic escape routes
  5. Validates build123d CAD alignment and collision checks
  6. Executes rebuild verification pipeline (rebuild_all.py)

Options:
  --check          Dry-run check only; verify consistency without writing files
  --skip-tests     Skip running the full test suite at the end of rebuild
  --pcb <path>     Path to source Amplifier.kicad_pcb (default: Amplifier/Amplifier.kicad_pcb)
  -h, --help       Show this help message and exit
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --pcb)
            if [[ -n "${2:-}" ]]; then
                PCB_PATH="$2"
                shift 2
            else
                echo "[ERROR] --pcb requires a path argument." >&2
                exit 1
            fi
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown option: $1" >&2
            print_usage
            exit 1
            ;;
    esac
done

if [[ ! -f "${PCB_PATH}" ]]; then
    echo "[ERROR] PCB file not found: ${PCB_PATH}" >&2
    exit 1
fi

echo "========================================================================"
echo "  MR1 PCB Back-Propagation & Procedural Synchronization Utility"
echo "========================================================================"
echo "Source PCB : ${PCB_PATH}"
echo "Check-only : ${CHECK_ONLY}"
echo "Skip-tests : ${SKIP_TESTS}"
echo "========================================================================"

# Step 1: Ingest PCB pin placements into stack_spec.py
echo -e "\n[STEP 1/5] Back-propagating PCB pin placements into src/stack_spec.py..."
if [ "${CHECK_ONLY}" = true ]; then
    "${RUN_PY}" "${SCRIPT_DIR}/build_amplifier_kicad.py" --check --pcb "${PCB_PATH}"
else
    "${RUN_PY}" "${SCRIPT_DIR}/build_amplifier_kicad.py" --sync-spec --pcb "${PCB_PATH}"
    "${RUN_PY}" "${SCRIPT_DIR}/build_amplifier_kicad.py" --check --pcb "${PCB_PATH}"
fi

# Step 2: Synchronize footprint libraries
echo -e "\n[STEP 2/5] Synchronizing KiCad coax and fluid footprints..."
if [ "${CHECK_ONLY}" = true ]; then
    "${RUN_PY}" "${SCRIPT_DIR}/generate_footprint.py" --check
else
    "${RUN_PY}" "${SCRIPT_DIR}/generate_footprint.py"
    "${RUN_PY}" "${SCRIPT_DIR}/generate_footprint.py" --check
fi

# Step 3: Regenerate Interposer PCB mating pads and routes
echo -e "\n[STEP 3/5] Synchronizing Interposer PCB mating pads and routes..."
if [ "${CHECK_ONLY}" = true ]; then
    "${RUN_PY}" "${SCRIPT_DIR}/build_interposer_kicad.py" --check
else
    "${RUN_PY}" "${SCRIPT_DIR}/build_interposer_kicad.py" --write
    "${RUN_PY}" "${SCRIPT_DIR}/build_interposer_kicad.py" --check
fi

# Step 4: Verify build123d CAD alignment with stack_spec
echo -e "\n[STEP 4/5] Verifying build123d CAD geometry against stack_spec..."
"${RUN_PY}" "${SCRIPT_DIR}/generate_footprint.py" --check-cad

# Step 5: Run full rebuild pipeline
echo -e "\n[STEP 5/5] Executing rebuild pipeline..."
REBUILD_ARGS=(--check)
if [ "${SKIP_TESTS}" = true ]; then
    REBUILD_ARGS+=(--skip-tests)
fi
"${RUN_PY}" "${SCRIPT_DIR}/rebuild_all.py" "${REBUILD_ARGS[@]}"

echo -e "\n========================================================================"
echo "[SUCCESS] PCB changes back-propagated and verified across all pipelines!"
echo "========================================================================"
