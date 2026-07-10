from pydantic import BaseModel


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    timezone: str

