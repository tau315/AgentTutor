from datetime import datetime, time

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base
from app.users.models import new_id


class AvailabilityWindow(Base):
    __tablename__ = "availability_windows"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_availability_weekday"),
        CheckConstraint("start_time < end_time", name="ck_availability_time_order"),
        UniqueConstraint(
            "tutor_profile_id", "weekday", "start_time", "end_time",
            name="uq_availability_window",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tutor_profile_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False)


class BlockedTime(Base):
    __tablename__ = "blocked_times"
    __table_args__ = (
        CheckConstraint("starts_at < ends_at", name="ck_blocked_time_order"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tutor_profile_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(250))
