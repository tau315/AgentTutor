from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.users.repository import UserRepository
from app.users.schemas import UserProfile


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.users = UserRepository(db)

    async def get_profile(self, current_user: CurrentUser) -> UserProfile:
        user = await self.users.get_by_id(current_user.id)

        if user is None:
            raise ValueError("User not found")

        return UserProfile(
            id=user.id,
            email=user.email,
            display_name=None,
            timezone=user.timezone,
        )

    async def update_profile(self, current_user: CurrentUser, data: dict) -> UserProfile:
        raise NotImplementedError("User profile updates are not implemented yet.")