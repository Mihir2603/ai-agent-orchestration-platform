from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.runtime.tools import TOOL_DESCRIPTIONS

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return [a.to_dict() for a in result.scalars().all()]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = Agent(**payload.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent.to_dict()


@router.get("/tools", summary="List available tools")
async def list_tools():
    return [{"name": k, "description": v} for k, v in TOOL_DESCRIPTIONS.items()]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.to_dict()


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, payload: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(agent, field, value)
    await db.commit()
    await db.refresh(agent)
    return agent.to_dict()


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    await db.commit()
