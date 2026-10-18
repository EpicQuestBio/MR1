#!/usr/bin/env bash

# Copyright (C) 2026 Lawrence R. Kincheloe III / Molecular Reality Corp
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# =============================================================================
# MR1 Nanopore Reader - Development Environment Setup & Diagnostics
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"

LAUNCH_VIEWER="no"
INSTALL_PLUGIN="no"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --viewer)
            LAUNCH_VIEWER="yes"
            shift
            ;;
        --install-kicad-plugin|--plugin)
            INSTALL_PLUGIN="yes"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}  MR1 Nanopore Reader - Environment Setup & Tool Verification${NC}"
echo -e "${BLUE}=================================================================${NC}"

# 1. Virtual Environment & Python Check
echo -e "${YELLOW}>> Ensuring Python virtual environment (.venv)...${NC}"
if [ -f "${REPO_ROOT}/setup_env.sh" ]; then
    bash "${REPO_ROOT}/setup_env.sh" --check >/dev/null 2>&1 || bash "${REPO_ROOT}/setup_env.sh"
fi

if [ -f "${REPO_ROOT}/.venv/Scripts/python.exe" ]; then
    PYTHON_CMD="${REPO_ROOT}/.venv/Scripts/python.exe"
elif [ -f "${REPO_ROOT}/.venv/bin/python" ]; then
    PYTHON_CMD="${REPO_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo -e "${RED}[MISSING]${NC} Python 3 is required."
    exit 1
fi
PY_VER=$(${PYTHON_CMD} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo -e "${GREEN}[OK]${NC} (${PYTHON_CMD} v${PY_VER})"

# 2. Python Packages Verification (build123d, ocp_vscode, wireviz)
echo -n "Checking build123d in environment... "
if ${PYTHON_CMD} -c "import build123d" >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[NOT FOUND]${NC} Installing via requirements.txt..."
    ${PYTHON_CMD} -m pip install -q -r "${REPO_ROOT}/requirements.txt"
fi

echo -n "Checking ocp_vscode in environment... "
if ${PYTHON_CMD} -c "import ocp_vscode" >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[NOT FOUND]${NC} Installing via requirements.txt..."
    ${PYTHON_CMD} -m pip install -q -r "${REPO_ROOT}/requirements.txt"
fi

echo -n "Checking WireViz & Graphviz... "
if ${PYTHON_CMD} -c "import wireviz" >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[MISSING]${NC} Installing wireviz..."
    ${PYTHON_CMD} -m pip install -q wireviz
fi

# 3. KiCad CLI Check
echo -n "Checking KiCad CLI (kicad-cli)... "
KICAD_FOUND="no"
if command -v kicad-cli >/dev/null 2>&1 || command -v kicad-cli.exe >/dev/null 2>&1; then
    KICAD_FOUND="yes"
elif [ -f "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" ] || [ -f "C:/Program Files/KiCad/9.0/bin/kicad-cli.exe" ]; then
    KICAD_FOUND="yes"
fi

if [ "${KICAD_FOUND}" = "yes" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[WARNING]${NC} kicad-cli not found. KiCad Gerber/BOM exports will be skipped unless installed."
fi

# 4. PlatformIO Core Check
echo -n "Checking PlatformIO (pio)... "
if command -v pio >/dev/null 2>&1 || command -v pio.exe >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[WARNING]${NC} PlatformIO not found. Firmware compilation will be skipped."
fi

# 5. Node.js Check
echo -n "Checking Node.js & npm... "
if command -v npm >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
    if [ ! -d "${REPO_ROOT}/node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install --silent
    fi
else
    echo -e "${YELLOW}[OPTIONAL]${NC} Node.js not detected."
fi

# 6. OpenAuto-CFD KiCad Plugin Installation (if requested)
if [ "${INSTALL_PLUGIN}" = "yes" ]; then
    echo -e "\n${BLUE}>> Installing OpenAuto-CFD KiCad Action Plugin...${NC}"
    ${PYTHON_CMD} "${REPO_ROOT}/plugins/openauto_cfd_plugin.py" --install
fi

echo -e "\n${GREEN}Environment verification completed successfully.${NC}"
echo "You can now run: ./scripts/export_all.sh --all"

if [ "${LAUNCH_VIEWER}" = "yes" ]; then
    echo -e "\n${BLUE}>> Launching ocp_vscode standalone viewer...${NC}"
    ${PYTHON_CMD} -m ocp_vscode &
fi