from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import CurrentUser, get_current_user
from app.users.schemas import UserProfile
from app.users.service import UserService


router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfile:
    return await UserService(db).get_profile(current_user)