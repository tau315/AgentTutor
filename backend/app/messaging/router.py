from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, get_current_user, require_roles
from app.messaging.schemas import ConversationCreate, ConversationRead, MessageCreate
from app.messaging.service import MessagingService


router = APIRouter()


@router.get("/admin/{conversation_id}", response_model=ConversationRead)
async def review_thread(conversation_id: str, report_id: str, _: CurrentUser = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db_session)):
    return await MessagingService(db).admin_review_thread(conversation_id, report_id)


@router.get("", response_model=list[ConversationRead])
async def list_threads(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await MessagingService(db).list_threads(current_user)


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_thread(data: ConversationCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await MessagingService(db).create_thread(current_user, data)


@router.post("/{conversation_id}/messages", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def send_message(conversation_id: str, data: MessageCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await MessagingService(db).send_message(current_user, conversation_id, data)
