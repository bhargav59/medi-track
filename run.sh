#!/bin/bash
# ============================================
#  Medi-Track Nepal — macOS/Linux Launcher
#  Run:  chmod +x run.sh && ./run.sh
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "Starting Medi-Track Nepal..."

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Install dependencies if needed
if ! "$VENV_DIR/bin/python" -c "import flet" 2>/dev/null; then
    echo "Installing dependencies..."
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Launch
"$VENV_DIR/bin/python" "$SCRIPT_DIR/main.py"
