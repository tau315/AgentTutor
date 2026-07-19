from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.users.schemas import validate_timezone


def aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Include a UTC offset, for example 2026-07-20T17:00:00-04:00")
    return value


class AvailabilityWindowInput(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    timezone: str

    _valid_timezone = field_validator("timezone")(validate_timezone)

    @model_validator(mode="after")
    def end_must_follow_start(self):
        if self.start_time >= self.end_time:
            raise ValueError("end_time must be later than start_time")
        return self


class AvailabilityWindowRead(AvailabilityWindowInput):
    id: str
    model_config = ConfigDict(from_attributes=True)


class AvailabilityReplace(BaseModel):
    windows: list[AvailabilityWindowInput] = Field(max_length=50)

    @model_validator(mode="after")
    def windows_must_not_overlap(self):
        for index, first in enumerate(self.windows):
            for second in self.windows[index + 1 :]:
                if (
                    first.weekday == second.weekday
                    and first.timezone == second.timezone
                    and first.start_time < second.end_time
                    and first.end_time > second.start_time
                ):
                    raise ValueError("Weekly availability windows cannot overlap")
        return self


class BlockedTimeCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    reason: str | None = Field(default=None, max_length=250)

    _starts_aware = field_validator("starts_at")(aware_datetime)
    _ends_aware = field_validator("ends_at")(aware_datetime)

    @model_validator(mode="after")
    def end_must_follow_start(self):
        if self.starts_at >= self.ends_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class BlockedTimeRead(BlockedTimeCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class AvailabilityCheck(BaseModel):
    tutor_id: str
    starts_at: datetime
    ends_at: datetime
    _starts_aware = field_validator("starts_at")(aware_datetime)
    _ends_aware = field_validator("ends_at")(aware_datetime)


class AvailabilityResult(BaseModel):
    available: bool
    reason: str | None = None
