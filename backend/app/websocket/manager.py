"""
WebSocket connection manager.

Clients can subscribe to:
  - Global feed  (channel="global")
  - Specific execution feed (channel="exec:{execution_id}")
"""

from __future__ import annotations
import asyncio
import json
import logging
from collections import defaultdict
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # channel_name -> set of websocket connections
        self._channels: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str = "global"):
        await websocket.accept()
        async with self._lock:
            self._channels[channel].add(websocket)
        logger.info("WS connect: channel=%s total=%d", channel, len(self._channels[channel]))

    async def disconnect(self, websocket: WebSocket, channel: str = "global"):
        async with self._lock:
            self._channels[channel].discard(websocket)
        logger.info("WS disconnect: channel=%s remaining=%d", channel, len(self._channels[channel]))

    async def broadcast(self, data: dict, channel: str = "global"):
        """Send data to all subscribers of a channel."""
        payload = json.dumps(data, default=str)
        dead: list[WebSocket] = []
        for ws in list(self._channels.get(channel, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._channels[channel].discard(ws)

    async def broadcast_execution(self, execution_id: str, data: dict):
        """Broadcast to both the execution channel and global channel."""
        await self.broadcast(data, channel=f"exec:{execution_id}")
        await self.broadcast(data, channel="global")

    async def send_to(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except Exception as exc:
            logger.warning("Failed to send WS message: %s", exc)


# Singleton used throughout the app
ws_manager = ConnectionManager()
