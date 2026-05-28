#!/usr/bin/env bash
# ─── AI Agent Orchestration Platform — One-command setup ─────────────────────
set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║    AI Agent Orchestration Platform — Setup           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Check prerequisites ───────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }
command -v node    >/dev/null 2>&1 || { echo "❌ Node.js 18+ required";   exit 1; }
command -v npm     >/dev/null 2>&1 || { echo "❌ npm required";            exit 1; }

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python $PYTHON_VER"
echo "✓ Node $(node --version)"

# ── Backend setup ─────────────────────────────────────────────────────────────
echo ""
echo "📦 Installing backend dependencies…"
cd backend

# Create virtualenv if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Backend dependencies installed"

# .env setup
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Created backend/.env from .env.example"
    echo "   Please set OPENAI_API_KEY (and optionally TELEGRAM_BOT_TOKEN) in backend/.env"
fi

cd ..

# ── Frontend setup ────────────────────────────────────────────────────────────
echo ""
echo "📦 Installing frontend dependencies…"
cd frontend
npm install --silent
echo "✓ Frontend dependencies installed"
cd ..

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅ Setup complete!                                  ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  1. Edit backend/.env and add your OPENAI_API_KEY   ║"
echo "║  2. Run:  ./start.sh                                 ║"
echo "║  3. Open: http://localhost:5173                      ║"
echo "╚══════════════════════════════════════════════════════╝"
