from app.core.security import CurrentUser
from app.users.schemas import UserProfile


class UserService:
    async def get_profile(self, user: CurrentUser) -> UserProfile:
        raise NotImplementedError("User profile lookup is not implemented yet.")

    async def update_profile(self, user: CurrentUser, data: dict) -> UserProfile:
        raise NotImplementedError("User profile updates are not implemented yet.")

