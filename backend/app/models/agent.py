from sqlalchemy import Column, String, Text, Float, Boolean, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


def _now():
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    role = Column(String(500), nullable=False, default="")
    description = Column(Text, default="")
    system_prompt = Column(Text, nullable=False, default="You are a helpful assistant.")
    model = Column(String(100), default="gpt-4o-mini")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)

    # Capabilities
    tools = Column(JSON, default=list)          # list of tool names
    memory_enabled = Column(Boolean, default=False)
    memory_window = Column(Integer, default=10)  # last N messages to keep

    # Guardrails
    guardrails = Column(JSON, default=dict)      # {max_iterations, forbidden_topics, ...}

    # Schedule
    schedule_enabled = Column(Boolean, default=False)
    schedule_cron = Column(String(100), default="")
    schedule_task = Column(Text, default="")

    # Meta
    avatar_color = Column(String(20), default="#6366f1")
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    channels = relationship("Channel", back_populates="agent", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="agent")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": self.tools or [],
            "memory_enabled": self.memory_enabled,
            "memory_window": self.memory_window,
            "guardrails": self.guardrails or {},
            "schedule_enabled": self.schedule_enabled,
            "schedule_cron": self.schedule_cron,
            "schedule_task": self.schedule_task,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
