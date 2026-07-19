from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.scheduling.schemas import aware_datetime


class SessionStatus(StrEnum):
    requested = "requested"
    booked = "booked"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"


class SessionScope(StrEnum):
    upcoming = "upcoming"
    history = "history"
    all = "all"


class SessionRequest(BaseModel):
    tutor_id: str
    subject: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=3000)
    starts_at: datetime
    ends_at: datetime
    _starts_aware = field_validator("starts_at")(aware_datetime)
    _ends_aware = field_validator("ends_at")(aware_datetime)

    @model_validator(mode="after")
    def valid_range(self):
        if self.starts_at >= self.ends_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class SessionReschedule(BaseModel):
    starts_at: datetime
    ends_at: datetime
    _starts_aware = field_validator("starts_at")(aware_datetime)
    _ends_aware = field_validator("ends_at")(aware_datetime)

    @model_validator(mode="after")
    def valid_range(self):
        if self.starts_at >= self.ends_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class SessionDecision(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class SessionEventRead(BaseModel):
    id: str
    action: str
    details: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SessionSummary(BaseModel):
    id: str
    tutor_id: str
    tutor_name: str
    student_id: str
    student_name: str
    subject: str
    notes: str | None
    starts_at: datetime
    ends_at: datetime
    status: SessionStatus
    requested_by_user_id: str
    cancellation_reason: str | None
    events: list[SessionEventRead] = []
