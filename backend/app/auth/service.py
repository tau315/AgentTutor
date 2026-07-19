from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, SignupRequest, SignupRole, TokenResponse
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.users.models import StudentProfile, TutorProfile, User
from app.users.repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def signup(self, data: SignupRequest) -> TokenResponse:
        existing_user = await self.users.get_by_email(data.email)
        if existing_user is not None:
            raise AppError("Email already registered", status.HTTP_409_CONFLICT)

        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role=data.role.value,
            timezone=data.timezone,
        )
        saved_user = await self.users.create(user)

        if data.role == SignupRole.student:
            self.db.add(StudentProfile(user_id=saved_user.id))
        else:
            self.db.add(TutorProfile(user_id=saved_user.id))

        await self.users.commit()
        return TokenResponse(access_token=create_access_token(saved_user.id))

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise AppError("Invalid email or password", status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            raise AppError("This account is inactive", status.HTTP_403_FORBIDDEN)

        return TokenResponse(access_token=create_access_token(user.id))
