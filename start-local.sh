#!/bin/bash
# Quick start script for local development

echo "=========================================="
echo "🚀 Starting Yuto Portfolio Locally"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  .env file not found in backend/"
    echo "Creating .env file template..."
    echo "ANTHROPIC_API_KEY=your_key_here" > backend/.env
    echo "DISABLE_RAG=false" >> backend/.env
    echo "PRELOAD_RAG=false" >> backend/.env
    echo ""
    echo "⚠️  Please edit backend/.env and add your ANTHROPIC_API_KEY"
    echo "   Press Enter to continue anyway, or Ctrl+C to exit and add your key..."
    read
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
fi

# Start backend server
echo ""
echo "=========================================="
echo "🔥 Starting backend server on port 8000"
echo "   Backend will be available at: http://localhost:8000"
echo "   Health check: http://localhost:8000/health"
echo ""
echo "   Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

