#!/bin/bash

# Kunjal Agents - Startup Script
# This script starts both the backend and frontend servers

set -e

echo "=========================================="
echo "  Kunjal Agents - Development Startup"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Please create a .env file with OPENROUTER_API_KEY"
    echo ""
fi

# Function to cleanup processes
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Start Backend
echo "🚀 Starting backend server..."
cd server
python api.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Failed to start backend server"
    exit 1
fi

echo "✅ Backend server running on http://localhost:8000"
echo ""

# Start Frontend
echo "🚀 Starting frontend server..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 3

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Failed to start frontend server"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Frontend server running on http://localhost:5173"
echo ""
echo "=========================================="
echo "  Both servers are running!"
echo "=========================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
