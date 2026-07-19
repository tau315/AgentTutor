from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    id: str
    kind: str
    title: str
    body: str
    resource_id: str | None
    read_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
