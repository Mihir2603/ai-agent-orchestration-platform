from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


def _now():
    return datetime.now(timezone.utc)


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    is_template = Column(Boolean, default=False)
    template_type = Column(String(100), default="")

    # ReactFlow graph JSON: {nodes, edges, entryNode, viewport}
    graph = Column(JSON, nullable=False, default=dict)

    # Runtime settings
    max_iterations = Column(Integer, default=20)
    timeout_seconds = Column(Integer, default=300)

    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_template": self.is_template,
            "template_type": self.template_type,
            "graph": self.graph or {},
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    status = Column(String(50), default="pending")   # pending|running|completed|failed|cancelled
    task_input = Column(Text, default="")
    result = Column(Text, default="")
    error = Column(Text, default="")
    total_tokens = Column(Integer, default=0)
    channel_source = Column(String(100), default="api")  # api|telegram|slack
    channel_user_id = Column(String(200), default="")

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    messages = relationship("Message", back_populates="execution", cascade="all, delete-orphan",
                            order_by="Message.created_at")

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "task_input": self.task_input,
            "result": self.result,
            "error": self.error,
            "total_tokens": self.total_tokens,
            "channel_source": self.channel_source,
            "channel_user_id": self.channel_user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
