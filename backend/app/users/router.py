from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, get_current_user, require_roles
from app.users.schemas import (
    AdminUserUpdate,
    StudentProfileRead,
    StudentProfileUpdate,
    UserProfile,
    UserProfileUpdate,
)
from app.users.service import UserService


router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfile:
    return await UserService(db).get_profile(current_user)


@router.patch("/me", response_model=UserProfile)
async def update_me(
    data: UserProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfile:
    return await UserService(db).update_profile(current_user, data)


@router.get("/me/student-profile", response_model=StudentProfileRead)
async def get_my_student_profile(
    current_user: CurrentUser = Depends(require_roles(Role.student)),
    db: AsyncSession = Depends(get_db_session),
) -> StudentProfileRead:
    return await UserService(db).get_student_profile(current_user)


@router.patch("/me/student-profile", response_model=StudentProfileRead)
async def update_my_student_profile(
    data: StudentProfileUpdate,
    current_user: CurrentUser = Depends(require_roles(Role.student)),
    db: AsyncSession = Depends(get_db_session),
) -> StudentProfileRead:
    return await UserService(db).update_student_profile(current_user, data)


@router.get("", response_model=list[UserProfile])
async def list_users(
    _: CurrentUser = Depends(require_roles(Role.admin)),
    db: AsyncSession = Depends(get_db_session),
) -> list[UserProfile]:
    return await UserService(db).list_users()


@router.patch("/{user_id}", response_model=UserProfile)
async def admin_update_user(
    user_id: str,
    data: AdminUserUpdate,
    _: CurrentUser = Depends(require_roles(Role.admin)),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfile:
    return await UserService(db).admin_update_user(user_id, data)
