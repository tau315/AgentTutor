from pydantic import BaseModel


class TutorSearchFilters(BaseModel):
    subject: str | None = None
    available_after: str | None = None
    expertise: str | None = None


class TutorSummary(BaseModel):
    id: str
    display_name: str
    subjects: list[str]
    rating: float | None = None

