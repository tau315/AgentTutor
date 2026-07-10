from fastapi import APIRouter, Depends

from app.agent.schemas import AgentMessageRequest, AgentMessageResponse
from app.agent.service import AgentService
from app.core.security import CurrentUser, get_current_user


router = APIRouter()


@router.post("/chat", response_model=AgentMessageResponse)
async def chat(
    request: AgentMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> AgentMessageResponse:
    return await AgentService().respond(current_user, request)

