from pydantic import ConfigDict
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = ""
    description: str = ""
    system_prompt: str = "You are a helpful assistant."
    model: str = "gpt-4o-mini"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=100, le=32000)
    tools: List[str] = []
    memory_enabled: bool = False
    memory_window: int = 10
    guardrails: Dict[str, Any] = {}
    schedule_enabled: bool = False
    schedule_cron: str = ""
    schedule_task: str = ""
    avatar_color: str = "#6366f1"


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[str]] = None
    memory_enabled: Optional[bool] = None
    memory_window: Optional[int] = None
    guardrails: Optional[Dict[str, Any]] = None
    schedule_enabled: Optional[bool] = None
    schedule_cron: Optional[str] = None
    schedule_task: Optional[str] = None
    avatar_color: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    system_prompt: str
    model: str
    temperature: float
    max_tokens: int
    tools: List[str]
    memory_enabled: bool
    memory_window: int
    guardrails: Dict[str, Any]
    schedule_enabled: bool
    schedule_cron: str
    schedule_task: str
    avatar_color: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
