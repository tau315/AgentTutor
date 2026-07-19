from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentActionRisk(StrEnum):
    read = "read"
    write_requires_confirmation = "write_requires_confirmation"


class AgentContext(BaseModel):
    user_id: str
    role: str
    timezone: str


class AgentMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: str | None = None


class AgentMessageRead(BaseModel):
    id: str
    role: str
    content: str
    tool_name: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentConversationRead(BaseModel):
    id: str
    summary: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[AgentMessageRead]


class AgentMessageResponse(BaseModel):
    message: str
    conversation_id: str
    requires_confirmation: bool = False
    pending_action_id: str | None = None
    proposed_action: str | None = None
    tool_name: str | None = None


class AgentToolDefinition(BaseModel):
    name: str
    description: str
    risk: AgentActionRisk
    allowed_roles: list[str]


class ToolPlan(BaseModel):
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    clarification: str | None = None
    direct_answer: str | None = None


class ActionDecisionResponse(BaseModel):
    action_id: str
    status: str
    message: str
    result: dict[str, Any] | None = None


class KnowledgeDocumentCreate(BaseModel):
    category: str = Field(pattern="^(platform|homework)$")
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20000)


class KnowledgeDocumentRead(BaseModel):
    id: str
    category: str
    title: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MemoryCreate(BaseModel):
    kind: str = Field(pattern="^(preference|learning_goal)$")
    content: str = Field(min_length=1, max_length=1000)


class MemoryRead(BaseModel):
    id: str
    kind: str
    content: str
    sensitive: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
