from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user
from app.sessions.schemas import SessionSummary
from app.sessions.service import SessionService


router = APIRouter()


@router.get("/upcoming", response_model=list[SessionSummary])
async def upcoming_sessions(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[SessionSummary]:
    return await SessionService().list_upcoming(current_user)

