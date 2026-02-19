#!/bin/bash
set -e

# Helper function for manual install
install_manual() {
    echo "Attempting to install BOSL2 manually..."
    mkdir -p libraries
    if [ -d "libraries/BOSL2" ]; then
        echo "libraries/BOSL2 already exists. Skipping."
        return
    fi

    if command -v git >/dev/null 2>&1; then
        echo "Using git..."
        if git clone --depth 1 https://github.com/BOSL2/BOSL2.git libraries/BOSL2; then
            return
        fi
        echo "Git clone failed. Trying curl..."
    fi

    echo "Using curl..."
    curl -L -o bosl2.zip https://github.com/BelfrySCAD/BOSL2/archive/refs/heads/master.zip
    unzip -q bosl2.zip -d libraries/
    if [ -d "libraries/BOSL2-master" ]; then
        mv libraries/BOSL2-master libraries/BOSL2
    fi
    rm -f bosl2.zip
}

echo "Starting Installation..."

if command -v npm >/dev/null 2>&1; then
    echo "Node.js/npm detected. Installing dependencies..."
    npm install
    echo "Running library setup..."
    node scripts/install_libraries.js
else
    echo "WARNING: Node.js/npm not found. Export scripts will not work."
    install_manual
fi

echo "Installation complete!"
