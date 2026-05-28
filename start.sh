#!/usr/bin/env bash
# ─── Start both backend and frontend dev servers ─────────────────────────────
set -e

echo "🚀 Starting AI Agent Orchestration Platform…"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down…"
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Backend
cd backend
if [ ! -d ".venv" ]; then
    echo "⚠️  Run ./setup.sh first!"
    exit 1
fi
source .venv/bin/activate
mkdir -p data outputs
echo "▶  Backend starting on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 3

# Frontend
cd frontend
echo "▶  Frontend starting on http://localhost:5173"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Platform is running!                                ║"
echo "║  Frontend: http://localhost:5173                     ║"
echo "║  API docs: http://localhost:8000/api/docs            ║"
echo "║  Press Ctrl+C to stop                                ║"
echo "╚══════════════════════════════════════════════════════╝"

wait
