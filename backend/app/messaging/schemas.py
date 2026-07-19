from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConversationCreate(BaseModel):
    tutor_id: str | None = None
    student_id: str | None = None

    @model_validator(mode="after")
    def one_target(self):
        if bool(self.tutor_id) == bool(self.student_id):
            raise ValueError("Provide either tutor_id or student_id")
        return self


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class MessageRead(BaseModel):
    id: str
    sender_id: str
    body: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationRead(BaseModel):
    id: str
    student_id: str
    student_name: str
    tutor_id: str
    tutor_name: str
    created_at: datetime
    messages: list[MessageRead]
