from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import CurrentUser
from app.users.models import StudentProfile, TutorProfile
from app.users.repository import UserRepository
from app.users.schemas import (
    AdminUserUpdate,
    StudentProfileRead,
    StudentProfileUpdate,
    UserProfile,
    UserProfileUpdate,
)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def get_profile(self, current_user: CurrentUser) -> UserProfile:
        user = await self._get_user(current_user.id)
        return UserProfile.model_validate(user)

    async def update_profile(
        self, current_user: CurrentUser, data: UserProfileUpdate
    ) -> UserProfile:
        user = await self._get_user(current_user.id)
        updates = data.model_dump(exclude_unset=True)
        if updates.get("timezone") is None:
            updates.pop("timezone", None)
        for field, value in updates.items():
            setattr(user, field, value)
        await self.users.commit()
        return UserProfile.model_validate(user)

    async def get_student_profile(
        self, current_user: CurrentUser
    ) -> StudentProfileRead:
        profile = await self.users.get_student_profile(current_user.id)
        if profile is None:
            raise AppError("Student profile not found", status.HTTP_404_NOT_FOUND)
        return StudentProfileRead.model_validate(profile)

    async def update_student_profile(
        self, current_user: CurrentUser, data: StudentProfileUpdate
    ) -> StudentProfileRead:
        profile = await self.users.get_student_profile(current_user.id)
        if profile is None:
            profile = StudentProfile(user_id=current_user.id)
            self.db.add(profile)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self.users.commit()
        return StudentProfileRead.model_validate(profile)

    async def list_users(self) -> list[UserProfile]:
        return [UserProfile.model_validate(user) for user in await self.users.list_all()]

    async def admin_update_user(
        self, user_id: str, data: AdminUserUpdate
    ) -> UserProfile:
        user = await self._get_user(user_id)
        updates = data.model_dump(exclude_unset=True)
        if "role" in updates and updates["role"] is not None:
            updates["role"] = updates["role"].value
        for field, value in updates.items():
            setattr(user, field, value)

        if user.role == "student" and await self.users.get_student_profile(user.id) is None:
            self.db.add(StudentProfile(user_id=user.id))
        if user.role == "tutor" and await self.users.get_tutor_profile_for_user(user.id) is None:
            self.db.add(TutorProfile(user_id=user.id))

        await self.users.commit()
        return UserProfile.model_validate(user)

    async def _get_user(self, user_id: str):
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppError("User not found", status.HTTP_404_NOT_FOUND)
        return user
