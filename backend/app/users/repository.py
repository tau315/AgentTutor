from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.users.models import StudentProfile, TutorProfile, User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.db.get(User, user_id)

    async def list_all(self) -> list[User]:
        result = await self.db.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_student_profile(self, user_id: str) -> StudentProfile | None:
        return await self.db.get(StudentProfile, user_id)

    async def get_tutor_profile_for_user(self, user_id: str) -> TutorProfile | None:
        result = await self.db.execute(
            select(TutorProfile)
            .options(selectinload(TutorProfile.subjects), selectinload(TutorProfile.user))
            .where(TutorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def commit(self) -> None:
        await self.db.commit()
