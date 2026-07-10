from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user
from app.users.schemas import UserProfile
from app.users.service import UserService


router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> UserProfile:
    return await UserService().get_profile(current_user)

