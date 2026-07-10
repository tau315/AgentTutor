from dataclasses import dataclass
from enum import StrEnum


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


async def get_current_user() -> CurrentUser:
    """Placeholder auth dependency.

    Replace this with JWT validation before any real feature work ships.
    """
    return CurrentUser(id="dev-user", email="dev@example.com", role=Role.student)

