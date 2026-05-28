import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.message import Channel
from app.models.agent import Agent
from app.schemas.message import ChannelCreate, ChannelUpdate, ChannelResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=List[ChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
    return [c.to_dict() for c in result.scalars().all()]


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(payload: ChannelCreate, db: AsyncSession = Depends(get_db)):
    # Verify agent exists
    agent = await db.get(Agent, payload.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    channel = Channel(**payload.model_dump())
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    # If Telegram channel, attempt to start the bot
    if channel.channel_type == "telegram" and channel.is_active:
        token = payload.config.get("bot_token", "")
        if token:
            try:
                from app.channels.telegram import start_telegram_bot
                asyncio.create_task(start_telegram_bot(token, channel.agent_id))
                logger.info("Telegram bot started for agent %s", channel.agent_id)
            except Exception as e:
                logger.warning("Could not start Telegram bot: %s", e)

    return channel.to_dict()


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    ch = await db.get(Channel, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ch.to_dict()


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str, payload: ChannelUpdate, db: AsyncSession = Depends(get_db)
):
    ch = await db.get(Channel, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(ch, field, value)
    await db.commit()
    await db.refresh(ch)
    return ch.to_dict()


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    ch = await db.get(Channel, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    await db.delete(ch)
    await db.commit()
