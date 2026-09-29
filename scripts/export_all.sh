#!/usr/bin/env bash
# =============================================================================
# Sentinel Nanopore Reader ? Universal Project Export Script
# =============================================================================
# Usage:
#   ./scripts/export_all.sh [options]
#
# Options:
#   --all       Export all deliverables (CAD, KiCad, Wiring, Firmware, Manifest)
#   --cad       Export 3D STEP/STL and 2D DXF models via build123d
#   --kicad     Export Gerbers, Drill, POS, BOM, and PDF schematics
#   --wiring    Export WireViz wiring harness and fluid tubing diagrams
#   --firmware  Compile and stage ESP32-S3 firmware binaries
#   --manifest  Generate/update exports/manifest.json with SHA-256 hashes
#   --check     Verify integrity of all deliverables on disk against manifest
#   --help      Display this help message
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}  Sentinel Nanopore Reader ? Project Export System${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Find Python (prefer .venv)
if [ -f "${REPO_ROOT}/.venv/Scripts/python.exe" ]; then
    PYTHON_CMD="${REPO_ROOT}/.venv/Scripts/python.exe"
elif [ -f "${REPO_ROOT}/.venv/bin/python" ]; then
    PYTHON_CMD="${REPO_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo -e "${RED}[ERROR] Python is not installed or not on PATH.${NC}" >&2
    exit 1
fi

# Pass arguments directly to Python export manager
${PYTHON_CMD} "${REPO_ROOT}/scripts/export_manager.py" "$@"

EXIT_CODE=$?
if [ ${EXIT_CODE} -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS] Export pipeline finished successfully.${NC}"
else
    echo -e "${RED}[ERROR] Export pipeline failed with exit code ${EXIT_CODE}.${NC}" >&2
    exit ${EXIT_CODE}
fi