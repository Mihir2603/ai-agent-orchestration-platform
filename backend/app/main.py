"""
AI Agent Orchestration Platform — FastAPI entry point.

Startup sequence:
  1. Init SQLite DB (create tables)
  2. Seed template workflows (idempotent)
  3. Auto-start any active Telegram channels
  4. Mount REST routers + WebSocket endpoint
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.api import agents, workflows, executions, channels
from app.websocket.manager import ws_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Export API keys into os.environ so all LangChain/OpenAI libraries can pick them up
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.ANTHROPIC_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
if settings.GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initialising database …")
    await init_db()

    logger.info("Seeding template workflows …")
    await _seed_templates()

    logger.info("Checking for active channel bots …")
    await _start_channel_bots()

    logger.info("Platform ready 🚀")
    yield
    # Shutdown
    from app.channels.telegram import stop_all_bots
    await stop_all_bots()


app = FastAPI(
    title="AI Agent Orchestration Platform",
    description="Create, configure, and orchestrate AI agents into collaborative workflows.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───────────────────────────────────────────────────────────────────

app.include_router(agents.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(executions.router, prefix="/api")
app.include_router(channels.router, prefix="/api")


# ─── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_global(websocket: WebSocket, channel: str = Query("global")):
    """
    Connect to the real-time event stream.

    Query params:
      channel=global          — all events
      channel=exec:<uuid>     — events for a specific execution
    """
    await ws_manager.connect(websocket, channel)
    try:
        await websocket.send_json({"type": "connected", "channel": channel})
        while True:
            # Keep alive — client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, channel)


# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ─── Helper functions ─────────────────────────────────────────────────────────

async def _seed_templates():
    """Load pre-built workflow templates from templates/ directory (idempotent)."""
    import json
    import glob as _glob

    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    template_files = _glob.glob(os.path.join(template_dir, "*.json"))

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from app.models.workflow import Workflow

        for path in template_files:
            with open(path, encoding="utf-8") as f:
                tpl = json.load(f)

            # Check if template already exists
            existing = await db.execute(
                select(Workflow).where(
                    Workflow.is_template == True,  # noqa: E712
                    Workflow.template_type == tpl.get("template_type", ""),
                )
            )
            if existing.scalars().first():
                continue

            wf = Workflow(
                name=tpl["name"],
                description=tpl.get("description", ""),
                is_template=True,
                template_type=tpl.get("template_type", ""),
                graph=tpl.get("graph", {}),
                max_iterations=tpl.get("max_iterations", 20),
                timeout_seconds=tpl.get("timeout_seconds", 300),
            )
            db.add(wf)
            logger.info("Seeded template: %s", tpl["name"])

        await db.commit()


async def _start_channel_bots():
    """Auto-start any active Telegram channels stored in the DB."""
    from sqlalchemy import select
    from app.models.message import Channel
    from app.channels.telegram import start_telegram_bot

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Channel).where(Channel.channel_type == "telegram", Channel.is_active == True)  # noqa: E712
        )
        for ch in result.scalars().all():
            token = (ch.config or {}).get("bot_token", "")
            if token:
                asyncio.create_task(start_telegram_bot(token, ch.agent_id))
                logger.info("Auto-started Telegram bot for agent %s", ch.agent_id)


# ─── Static files (serve built frontend) ─────────────────────────────────────

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
