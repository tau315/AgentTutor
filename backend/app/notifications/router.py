from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import CurrentUser, get_current_user
from app.notifications.schemas import NotificationRead
from app.notifications.service import NotificationService


router = APIRouter()


@router.get("", response_model=list[NotificationRead])
async def list_notifications(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await NotificationService(db).list_for_user(current_user)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(notification_id: str, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await NotificationService(db).mark_read(current_user, notification_id)
