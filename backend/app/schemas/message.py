from pydantic import ConfigDict
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ChannelCreate(BaseModel):
    agent_id: str
    channel_type: str   # telegram | slack | webhook
    name: str = ""
    config: Dict[str, Any] = {}


class ChannelUpdate(BaseModel):
    agent_id: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class ChannelResponse(BaseModel):
    id: str
    agent_id: str
    channel_type: str
    name: str
    is_active: bool
    config: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
