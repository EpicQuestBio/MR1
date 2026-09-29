#!/usr/bin/env bash
# =============================================================================
# Sentinel Nanopore Reader ? End-to-End Test Suite Runner
# =============================================================================
# Runs:
# 1. Python Unit Tests (golden bounds, geometry generation, connectors)
# 2. Collision Clearance Suites (cartridge stack, housing, standoff, routing)
# 3. Firmware Protocol & Packet Serialization Tests
# 4. Export Deliverables E2E Verification Tests
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}  Running Sentinel Nanopore Reader E2E Test Suite${NC}"
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
    echo -e "${RED}[ERROR] Python is not installed.${NC}" >&2
    exit 1
fi

echo -e "${YELLOW}>> Running Unit Tests & Collision Checking Suites...${NC}"
${PYTHON_CMD} "${REPO_ROOT}/run_tests.py"

echo -e "${YELLOW}>> Verifying Export Deliverables Integrity (E2E)...${NC}"
${PYTHON_CMD} "${REPO_ROOT}/tests/test_exports_e2e.py"

echo -e "${GREEN}=================================================================${NC}"
echo -e "${GREEN}  ALL TESTS AND VERIFICATIONS PASSED CLEANLY (0 ERRORS)${NC}"
echo -e "${GREEN}=================================================================${NC}"