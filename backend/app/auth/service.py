from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, SignupRequest, TokenResponse
from app.core.security import create_access_token, hash_password, verify_password
from app.users.models import User
from app.users.repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.users = UserRepository(db)

    async def signup(self, data: SignupRequest) -> TokenResponse:
        existing_user = await self.users.get_by_email(data.email)

        if existing_user is not None:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            timezone=data.timezone,
        )

        saved_user = await self.users.create(user)
        token = create_access_token(saved_user.id)

        return TokenResponse(access_token=token)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(data.email)

        if user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(user.id)

        return TokenResponse(access_token=token)