from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.users.schemas import validate_timezone


class SignupRole(StrEnum):
    student = "student"
    tutor = "tutor"


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: SignupRole = SignupRole.student
    timezone: str = "America/New_York"

    _valid_timezone = field_validator("timezone")(validate_timezone)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
