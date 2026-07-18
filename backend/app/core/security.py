from dataclasses import dataclass
from enum import StrEnum

from passlib.context import CryptContext

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.users.repository import UserRepository
class Role(StrEnum):
    student = "student"
    tutor = "tutor"
    admin = "admin"


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    role: Role
    timezone: str = "America/New_York"


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "exp": expires_at,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
    except JWTError:
        raise credentials_error

    if user_id is None:
        raise credentials_error

    user = await UserRepository(db).get_by_id(user_id)

    if user is None:
        raise credentials_error

    return CurrentUser(
        id=user.id,
        email=user.email,
        role=Role(user.role),
        timezone=user.timezone,
    )