from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.workflow import WorkflowExecution
from app.models.message import Message
from app.schemas.workflow import ExecutionResponse, MessageResponse

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=List[ExecutionResponse])
async def list_executions(
    limit: int = 50,
    workflow_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(WorkflowExecution).order_by(WorkflowExecution.created_at.desc()).limit(limit)
    if workflow_id:
        q = q.where(WorkflowExecution.workflow_id == workflow_id)
    result = await db.execute(q)
    return [e.to_dict() for e in result.scalars().all()]


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    ex = await db.get(WorkflowExecution, execution_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex.to_dict()


@router.get("/{execution_id}/messages", response_model=List[MessageResponse])
async def get_execution_messages(execution_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message)
        .where(Message.execution_id == execution_id)
        .order_by(Message.created_at)
    )
    return [m.to_dict() for m in result.scalars().all()]


@router.delete("/{execution_id}", status_code=204)
async def delete_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    ex = await db.get(WorkflowExecution, execution_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    await db.delete(ex)
    await db.commit()
