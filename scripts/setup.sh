#!/usr/bin/env bash
# AEGIS Automated Environment Bootstrapper (POSIX / Linux / macOS)
# Usage: bash scripts/setup.sh

set -e

echo "=========================================================="
echo "   AEGIS Gateway: Automated Developer Environment Setup   "
echo "=========================================================="

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[INFO] Detected ${PYTHON_VERSION}"

# 1. Ensure .env exists
if [ ! -f ".env" ]; then
    echo "[INFO] Creating .env from .env.example..."
    cp .env.example .env
else
    echo "[INFO] .env already exists."
fi

# 2. Ensure data directory exists
mkdir -p data
echo "[INFO] Ensured data/ directory exists."

# 3. Editable package install
echo "[INFO] Installing package in editable mode..."
python3 -m pip install -e .

# 4. Set PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 5. Run test suite
echo "[INFO] Running verification tests..."
python3 -m pytest tests/ -v --tb=short

echo ""
echo "[SUCCESS] AEGIS environment initialized and verified!"
echo "Start Backend API:  uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload"
echo "Start SOC Console:  streamlit run frontend/dashboard.py --server.port 8501"
