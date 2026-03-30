#!/bin/bash

# GOMALE OS Command Center - Deploy Script

echo "🚀 GOMALE OS Command Center Deployment"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Not in gomale-os-command-center directory"
    exit 1
fi

# Deploy Backend
echo ""
echo "📦 Step 1: Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend in background
echo "🚀 Starting backend server..."
nohup python main.py > ../server.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"

cd ..

# Deploy Frontend
echo ""
echo "📦 Step 2: Building frontend..."
cd frontend-new

# Install dependencies
npm install

# Build for production
npm run build

echo "✅ Frontend built"

# Start frontend
echo "🚀 Starting frontend..."
nohup npx serve@latest dist -l 3000 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   URL: http://localhost:3000"

cd ..

# Summary
echo ""
echo "========================================"
echo "✅ GOMALE OS Deployed Successfully!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "To stop:"
echo "  kill $(cat backend.pid)"
echo "  kill $(cat frontend.pid)"
echo ""
echo "Logs:"
echo "  Backend:  tail -f server.log"
echo "  Frontend: tail -f frontend.log"
