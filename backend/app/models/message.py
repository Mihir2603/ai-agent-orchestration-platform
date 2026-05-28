from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


def _now():
    return datetime.now(timezone.utc)


class Message(Base):
    """Stores every message exchanged during a workflow execution."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String, ForeignKey("workflow_executions.id"), nullable=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    role = Column(String(50), default="assistant")  # user|assistant|tool|system
    content = Column(Text, default="")
    tool_name = Column(String(200), default="")
    tool_call_id = Column(String(200), default="")
    tokens_used = Column(Integer, default=0)
    meta = Column(JSON, default=dict)   # extra data (node_id, etc.)
    created_at = Column(DateTime(timezone=True), default=_now)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "agent_id": self.agent_id,
            "role": self.role,
            "content": self.content,
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
            "tokens_used": self.tokens_used,
            "meta": self.meta or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Channel(Base):
    """Integration channels for an agent (Telegram, Slack, etc.)."""
    __tablename__ = "channels"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    channel_type = Column(String(50), nullable=False)  # telegram|slack|webhook
    name = Column(String(200), default="")
    is_active = Column(Boolean, default=True)
    config = Column(JSON, default=dict)   # bot_token, chat_id, etc. (encrypted in prod)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    agent = relationship("Agent", back_populates="channels")

    def to_dict(self):
        # Never expose secrets in the dict
        safe_config = {k: ("***" if "token" in k.lower() or "key" in k.lower() or "secret" in k.lower() else v)
                       for k, v in (self.config or {}).items()}
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "channel_type": self.channel_type,
            "name": self.name,
            "is_active": self.is_active,
            "config": safe_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
