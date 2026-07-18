from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, SignupRequest, TokenResponse
from app.auth.service import AuthService
from app.core.database import get_db_session
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    return await AuthService(db).signup(request)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    request = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )
    return await AuthService(db).login(request)