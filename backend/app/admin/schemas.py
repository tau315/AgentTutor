from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReportStatus(StrEnum):
    open = "open"
    reviewing = "reviewing"
    resolved = "resolved"
    dismissed = "dismissed"


class ReportCreate(BaseModel):
    target_user_id: str | None = None
    reason: str = Field(min_length=1, max_length=150)
    details: str | None = Field(default=None, max_length=5000)


class ReportUpdate(BaseModel):
    status: ReportStatus
    admin_notes: str | None = Field(default=None, max_length=5000)


class ReportRead(BaseModel):
    id: str
    reporter_id: str
    target_user_id: str | None
    reason: str
    details: str | None
    status: ReportStatus
    admin_notes: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
