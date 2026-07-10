from enum import StrEnum

from pydantic import BaseModel


class SessionStatus(StrEnum):
    requested = "requested"
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"


class SessionSummary(BaseModel):
    id: str
    tutor_id: str
    student_id: str
    starts_at: str
    ends_at: str
    status: SessionStatus

