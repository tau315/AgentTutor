from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import Role


def validate_timezone(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Use a valid IANA time zone, such as America/New_York") from exc
    return value


class UserProfile(BaseModel):
    id: str
    email: str
    role: Role
    display_name: str | None
    timezone: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    timezone: str | None = None

    _valid_timezone = field_validator("timezone")(validate_timezone)


class StudentProfileRead(BaseModel):
    user_id: str
    grade_level: str | None
    learning_goals: str | None

    model_config = ConfigDict(from_attributes=True)


class StudentProfileUpdate(BaseModel):
    grade_level: str | None = Field(default=None, max_length=50)
    learning_goals: str | None = Field(default=None, max_length=2000)


class AdminUserUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None
