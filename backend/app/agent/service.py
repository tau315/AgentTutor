from uuid import uuid4

from app.agent.schemas import AgentContext, AgentMessageRequest, AgentMessageResponse
from app.agent.tools import build_tool_registry
from app.core.security import CurrentUser


class AgentService:
    def __init__(self) -> None:
        self.tools = build_tool_registry()

    async def respond(self, user: CurrentUser, request: AgentMessageRequest) -> AgentMessageResponse:
        context = AgentContext(
            user_id=user.id,
            role=user.role.value,
            timezone=user.timezone,
        )
        _ = context

        raise NotImplementedError("Agent planning and tool execution are not implemented yet.")

    def new_conversation_id(self) -> str:
        return str(uuid4())

