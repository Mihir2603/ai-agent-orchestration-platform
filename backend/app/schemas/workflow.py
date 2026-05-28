from pydantic import ConfigDict
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    graph: Dict[str, Any] = Field(default_factory=lambda: {"nodes": [], "edges": [], "entryNode": ""})
    max_iterations: int = 20
    timeout_seconds: int = 300


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    graph: Optional[Dict[str, Any]] = None
    max_iterations: Optional[int] = None
    timeout_seconds: Optional[int] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    is_template: bool
    template_type: str
    graph: Dict[str, Any]
    max_iterations: int
    timeout_seconds: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionCreate(BaseModel):
    task_input: str = Field(..., min_length=1)


class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    task_input: str
    result: str
    error: str
    total_tokens: int
    channel_source: str
    channel_user_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: str
    execution_id: Optional[str]
    agent_id: Optional[str]
    role: str
    content: str
    tool_name: str
    tokens_used: int
    meta: Dict[str, Any]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
