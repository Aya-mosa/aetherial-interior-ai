#!/bin/bash
echo "✦ Starting Aetherial AI Interior Architect"

# Start backend
echo "→ Starting FastAPI backend on port 8000..."
cd backend && uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "→ Starting Next.js frontend on port 3000..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo "✦ Running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
