from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base
from app.users.models import new_id


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
