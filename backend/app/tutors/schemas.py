from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TutorSort(StrEnum):
    relevance = "relevance"
    rating = "rating"
    price_low = "price_low"
    name = "name"


class TutorSearchFilters(BaseModel):
    subject: str | None = None
    expertise: str | None = None
    sort: TutorSort = TutorSort.relevance


class TutorSubjectInput(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    expertise: str | None = Field(default=None, max_length=150)


class TutorSubjectRead(TutorSubjectInput):
    id: str

    model_config = ConfigDict(from_attributes=True)


class TutorSummary(BaseModel):
    id: str
    display_name: str
    bio: str | None
    subjects: list[TutorSubjectRead]
    hourly_rate: Decimal | None
    rating: float
    is_active: bool


class TutorProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=3000)
    hourly_rate: Decimal | None = Field(default=None, ge=0, le=10000)
    is_active: bool | None = None
    subjects: list[TutorSubjectInput] | None = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def subjects_must_be_unique(self):
        if self.subjects is None:
            return self
        names = [item.subject.strip().casefold() for item in self.subjects]
        if len(names) != len(set(names)):
            raise ValueError("Each subject can only appear once")
        return self


class AdminTutorUpdate(BaseModel):
    is_active: bool | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
