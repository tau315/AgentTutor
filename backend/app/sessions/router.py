from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, get_current_user, require_roles
from app.sessions.schemas import SessionDecision, SessionRequest, SessionReschedule, SessionScope, SessionSummary
from app.sessions.service import SessionService


router = APIRouter()


@router.get("", response_model=list[SessionSummary])
async def list_sessions(scope: SessionScope = SessionScope.upcoming, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await SessionService(db).list_sessions(current_user, scope)


@router.get("/upcoming", response_model=list[SessionSummary])
async def upcoming_sessions(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await SessionService(db).list_sessions(current_user, SessionScope.upcoming)


@router.post("", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
async def request_session(data: SessionRequest, current_user: CurrentUser = Depends(require_roles(Role.student)), db: AsyncSession = Depends(get_db_session)):
    return await SessionService(db).request_session(current_user, data)


@router.post("/{session_id}/accept", response_model=SessionSummary)
async def accept_session(session_id: str, data: SessionDecision, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await SessionService(db).decide(current_user, session_id, True, data)


@router.post("/{session_id}/reject", response_model=SessionSummary)
async def reject_session(session_id: str, data: SessionDecision, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await SessionService(db).decide(current_user, session_id, False, data)


@router.post("/{session_id}/cancel", response_model=SessionSummary)
async def cancel_session(session_id: str, data: SessionDecision, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await SessionService(db).cancel(current_user, session_id, data)


@router.post("/{session_id}/reschedule", response_model=SessionSummary)
async def reschedule_session(session_id: str, data: SessionReschedule, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await SessionService(db).reschedule(current_user, session_id, data)
