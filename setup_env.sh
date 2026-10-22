#!/usr/bin/env bash

# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

# =============================================================================
# MR1 Nanopore Reader ? Python Virtual Environment Manager
# =============================================================================
# Usage:
#   ./setup_env.sh          # Setup or update .venv and install requirements
#   ./setup_env.sh --recreate # Delete existing .venv and rebuild clean
#   ./setup_env.sh --check  # Verify active/existing environment
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
VENV_DIR="${REPO_ROOT}/.venv"
REQ_FILE="${REPO_ROOT}/requirements.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}  MR1 Nanopore Reader ? Python VENV Setup & Manager${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Handle --recreate flag
if [ "$1" == "--recreate" ]; then
    if [ -d "${VENV_DIR}" ]; then
        echo -e "${YELLOW}>> Removing existing virtual environment at ${VENV_DIR}...${NC}"
        rm -rf "${VENV_DIR}"
    fi
fi

# Locate Python 3 base interpreter
if command -v python3 >/dev/null 2>&1; then
    BASE_PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    BASE_PYTHON="python"
else
    echo -e "${RED}[ERROR] Python 3 not found on system PATH.${NC}" >&2
    exit 1
fi

PY_VER=$(${BASE_PYTHON} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "System Python: ${CYAN}${BASE_PYTHON} (v${PY_VER})${NC}"

# 1. Create .venv if missing
if [ ! -d "${VENV_DIR}" ]; then
    echo -e ">> Creating virtual environment in ${CYAN}${VENV_DIR}${NC}..."
    ${BASE_PYTHON} -m venv "${VENV_DIR}"
    echo -e "${GREEN}[OK] Virtual environment created.${NC}"
else
    echo -e ">> Existing virtual environment found at ${CYAN}${VENV_DIR}${NC}."
fi

# 2. Determine VENV python & pip paths (cross-platform: Linux/macOS vs Windows Git-Bash)
if [ -f "${VENV_DIR}/bin/python" ]; then
    VENV_PYTHON="${VENV_DIR}/bin/python"
    VENV_PIP="${VENV_DIR}/bin/pip"
    ACTIVATE_PATH="${VENV_DIR}/bin/activate"
elif [ -f "${VENV_DIR}/Scripts/python.exe" ]; then
    VENV_PYTHON="${VENV_DIR}/Scripts/python.exe"
    VENV_PIP="${VENV_DIR}/Scripts/pip.exe"
    ACTIVATE_PATH="${VENV_DIR}/Scripts/activate"
else
    echo -e "${RED}[ERROR] Could not find python binary inside ${VENV_DIR}.${NC}" >&2
    exit 1
fi

# 3. Upgrade pip
echo -e ">> Upgrading pip inside venv..."
"${VENV_PYTHON}" -m pip install --quiet --upgrade pip

# 4. Install / Update requirements
if [ -f "${REQ_FILE}" ]; then
    echo -e ">> Installing dependencies from ${CYAN}requirements.txt${NC}..."
    "${VENV_PIP}" install --quiet -r "${REQ_FILE}"
    echo -e "${GREEN}[OK] Python packages installed successfully.${NC}"
else
    echo -e "${YELLOW}[WARN] requirements.txt not found at ${REQ_FILE}.${NC}"
fi

# 5. Diagnostic Verification
echo -e "\n${BLUE}--- Installed Packages in VENV ---${NC}"
"${VENV_PYTHON}" -c "
import sys
for pkg in ['build123d', 'ocp_viewer', 'wireviz', 'platformio']:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, '__version__', 'installed')
        print(f'  ? {pkg:15s}: {ver}')
    except ImportError:
        print(f'  ? {pkg:15s}: NOT INSTALLED')
"

# 6. Check System Toolchains
echo -e "\n${BLUE}--- External Toolchains ---${NC}"
echo -n "  KiCad CLI (kicad-cli): "
if command -v kicad-cli >/dev/null 2>&1 || [ -f "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" ] || [ -f "C:/Program Files/KiCad/9.0/bin/kicad-cli.exe" ]; then
    echo -e "${GREEN}Detected${NC}"
else
    echo -e "${YELLOW}Optional / Not Found${NC}"
fi

echo -n "  Graphviz (dot):        "
if command -v dot >/dev/null 2>&1 || [ -f "C:/Program Files/Graphviz/bin/dot.exe" ]; then
    echo -e "${GREEN}Detected${NC}"
else
    echo -e "${YELLOW}Optional / Not Found${NC}"
fi

echo -e "\n${GREEN}=================================================================${NC}"
echo -e "${GREEN}  Virtual Environment is Ready!${NC}"
echo -e "${GREEN}=================================================================${NC}"
echo -e "To activate this environment in your shell, run:"
echo -e "  ${CYAN}source ${ACTIVATE_PATH}${NC}"
echo -e "Or execute directly with venv:"
echo -e "  ${CYAN}${VENV_PYTHON} run_tests.py${NC}"
echo -e "  ${CYAN}${VENV_PYTHON} scripts/export_manager.py --all${NC}\n"