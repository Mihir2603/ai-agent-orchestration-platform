"""
Telegram channel integration.

• Uses python-telegram-bot v21 in async mode (long polling).
• Each unique Telegram user gets a conversation history window.
• Runs the gateway agent (configured in the channel settings) against
  every incoming message and replies with the agent's response.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Dict, List

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

logger = logging.getLogger(__name__)

# conversation_history[chat_id] -> list of BaseMessage (last N)
_conversation_histories: Dict[str, List[BaseMessage]] = defaultdict(list)
_MAX_HISTORY = 20

# Running bot applications (token -> Application)
_running_bots: Dict[str, object] = {}


async def start_telegram_bot(bot_token: str, agent_id: str):
    """
    Start a Telegram bot that routes all messages to the given agent.
    Safe to call multiple times — skips if the token is already running.
    """
    if bot_token in _running_bots:
        logger.info("Telegram bot already running for this token")
        return

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        from app.database import AsyncSessionLocal
        from app.models.agent import Agent
        from app.models.workflow import WorkflowExecution
        from app.models.message import Message
        from app.runtime.engine import run_single_agent
    except ImportError as e:
        logger.error("Telegram dependencies not available: %s", e)
        return

    app = Application.builder().token(bot_token).build()

    async def _get_agent(ctx_db):
        return await ctx_db.get(Agent, agent_id)

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        async with AsyncSessionLocal() as db:
            agent = await _get_agent(db)
            agent_name = agent.name if agent else "Assistant"
        await update.message.reply_text(
            f"👋 Hi! I'm **{agent_name}**, your AI assistant.\n\n"
            "Send me any message and I'll respond. "
            "Use /clear to reset our conversation history.",
            parse_mode="Markdown",
        )

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "💡 *Commands*\n"
            "/start — Introduction\n"
            "/help  — This message\n"
            "/clear — Clear conversation history\n\n"
            "Just type anything to chat!",
            parse_mode="Markdown",
        )

    async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        _conversation_histories[chat_id].clear()
        await update.message.reply_text("🗑️ Conversation history cleared.")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        chat_id = str(update.effective_chat.id)
        user_text = update.message.text
        user_name = update.effective_user.first_name or "User"

        await update.message.chat.send_action("typing")

        # Persist user message
        execution_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as db:
            agent = await _get_agent(db)
            if not agent:
                await update.message.reply_text("⚠️ Agent not configured. Please contact the admin.")
                return

            # Save user message
            db.add(Message(
                execution_id=None,
                agent_id=agent_id,
                role="user",
                content=user_text,
                meta={"channel": "telegram", "chat_id": chat_id, "user": user_name},
            ))
            await db.commit()

            # Keep history window
            history = _conversation_histories[chat_id]
            history.append(HumanMessage(content=user_text))
            if len(history) > _MAX_HISTORY:
                history[:] = history[-_MAX_HISTORY:]

            # Build agent config with real-time datetime injected into system prompt
            import datetime as _dt
            now = _dt.datetime.now(_dt.timezone.utc).strftime("%A, %d %B %Y %H:%M:%S UTC")
            agent_cfg = agent.to_dict()
            agent_cfg["system_prompt"] = (
                f"Current date and time: {now}\n\n" + agent_cfg.get("system_prompt", "")
            )

            try:
                response_text = await run_single_agent(
                    agent_cfg=agent_cfg,
                    user_message=user_text,
                    conversation_history=history[:-1],  # exclude the just-added user msg
                    execution_id=execution_id,
                    db_session_factory=AsyncSessionLocal,
                )
            except Exception as exc:
                logger.exception("Agent error for chat %s: %s", chat_id, exc)
                response_text = "⚠️ Sorry, I encountered an error. Please try again."

            # Add assistant response to history
            history.append(AIMessage(content=response_text))

        # Telegram has 4096 char limit per message
        if len(response_text) > 4000:
            for i in range(0, len(response_text), 4000):
                await update.message.reply_text(response_text[i:i+4000])
        else:
            await update.message.reply_text(response_text)

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    _running_bots[bot_token] = app

    logger.info("Starting Telegram bot polling for agent %s", agent_id)
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info("Telegram bot is live!")


async def stop_all_bots():
    """Gracefully stop all running bots (called on app shutdown)."""
    for token, app in list(_running_bots.items()):
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            logger.info("Telegram bot stopped")
        except Exception as exc:
            logger.warning("Error stopping bot: %s", exc)
    _running_bots.clear()
