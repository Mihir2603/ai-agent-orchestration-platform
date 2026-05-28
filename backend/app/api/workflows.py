import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db, AsyncSessionLocal
from app.models.workflow import Workflow, WorkflowExecution
from app.models.agent import Agent
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    ExecutionCreate, ExecutionResponse,
)
from app.runtime.engine import run_workflow
from app.websocket.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


# ─── Workflow CRUD ─────────────────────────────────────────────────────────────

@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    return [w.to_dict() for w in result.scalars().all()]


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    wf = Workflow(**payload.model_dump())
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf.to_dict()


@router.get("/templates", response_model=List[WorkflowResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Workflow).where(Workflow.is_template == True).order_by(Workflow.name)  # noqa: E712
    )
    return [w.to_dict() for w in result.scalars().all()]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf.to_dict()


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str, payload: WorkflowUpdate, db: AsyncSession = Depends(get_db)
):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(wf, field, value)
    await db.commit()
    await db.refresh(wf)
    return wf.to_dict()


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(wf)
    await db.commit()


# ─── Workflow Execution ────────────────────────────────────────────────────────

@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    payload: ExecutionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Collect agents referenced in the graph
    graph = wf.graph or {}
    agent_ids = list({
        n.get("data", {}).get("agentId", "")
        for n in graph.get("nodes", [])
        if n.get("data", {}).get("agentId")
    })
    agents = []
    for aid in agent_ids:
        a = await db.get(Agent, aid)
        if a:
            agents.append(a.to_dict())

    agents_map = {a["id"]: a for a in agents}

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        status="pending",
        task_input=payload.task_input,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    exec_id = execution.id

    # Kick off async execution
    background_tasks.add_task(
        _run_execution_task, exec_id, wf.to_dict(), agents_map, payload.task_input, wf.max_iterations
    )

    return execution.to_dict()


async def _run_execution_task(
    exec_id: str,
    workflow: dict,
    agents_map: dict,
    task_input: str,
    max_iterations: int,
):
    """Background task that actually runs the LangGraph workflow."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(WorkflowExecution, exec_id)
        if not execution:
            return

        execution.status = "running"
        execution.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            output = await run_workflow(
                workflow=workflow,
                agents_map=agents_map,
                task_input=task_input,
                execution_id=exec_id,
                db_session_factory=AsyncSessionLocal,
                max_iterations=max_iterations,
            )
            execution.status = "completed"
            execution.result = output
        except Exception as exc:
            logger.exception("Execution %s failed", exec_id)
            execution.status = "failed"
            execution.error = str(exc)
        finally:
            execution.completed_at = datetime.now(timezone.utc)
            await db.commit()

        await ws_manager.broadcast_execution(
            exec_id,
            {
                "type": "execution_status",
                "execution_id": exec_id,
                "status": execution.status,
                "result": execution.result[:500] if execution.result else "",
                "error": execution.error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
