#!/bin/bash
# Start script for Render deployment

set -e  # Exit on error

# Render sets PORT automatically, but default to 8000 if not set
PORT=${PORT:-8000}

echo "=========================================="
echo "Starting Yuto Portfolio Backend"
echo "PORT: $PORT"
echo "Working directory: $(pwd)"
PYTHON_CMD=$(which python3 2>/dev/null || which python 2>/dev/null || echo "python")
echo "Python: $PYTHON_CMD"
echo "=========================================="

# Change to backend directory
cd backend || {
    echo "Error: backend directory not found"
    exit 1
}

echo "Changed to backend directory: $(pwd)"
echo "Starting uvicorn server..."

# Check if uvicorn is available
if command -v uvicorn &> /dev/null; then
    echo "Using uvicorn from PATH"
    exec uvicorn app:app --host 0.0.0.0 --port $PORT
elif python3 -m uvicorn --help &> /dev/null; then
    echo "Using python3 -m uvicorn"
    exec python3 -m uvicorn app:app --host 0.0.0.0 --port $PORT
else
    echo "Error: uvicorn not found. Trying python -m uvicorn"
    exec python -m uvicorn app:app --host 0.0.0.0 --port $PORT
fi
