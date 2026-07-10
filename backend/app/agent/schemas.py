from enum import StrEnum

from pydantic import BaseModel


class AgentActionRisk(StrEnum):
    read = "read"
    write_requires_confirmation = "write_requires_confirmation"


class AgentContext(BaseModel):
    user_id: str
    role: str
    timezone: str


class AgentMessageRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class AgentMessageResponse(BaseModel):
    message: str
    conversation_id: str
    requires_confirmation: bool = False
    pending_action_id: str | None = None


class AgentToolDefinition(BaseModel):
    name: str
    description: str
    risk: AgentActionRisk

