from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base
from app.users.models import TutorProfile, User, new_id


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    tutor_profile_id: Mapped[str] = mapped_column(ForeignKey("tutor_profiles.id"), nullable=False, index=True)
    requested_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="requested", index=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped[User] = relationship(foreign_keys=[student_id])
    tutor_profile: Mapped[TutorProfile] = relationship()
    requested_by: Mapped[User] = relationship(foreign_keys=[requested_by_user_id])
    events: Mapped[list["SessionEvent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="SessionEvent.created_at"
    )

    __table_args__ = (
        ExcludeConstraint(
            ("tutor_profile_id", "="),
            (func.tstzrange(starts_at, ends_at, "[)"), "&&"),
            where=text("status IN ('requested', 'booked')"),
            using="gist",
            name="excl_tutor_session_overlap",
        ),
        ExcludeConstraint(
            ("student_id", "="),
            (func.tstzrange(starts_at, ends_at, "[)"), "&&"),
            where=text("status IN ('requested', 'booked')"),
            using="gist",
            name="excl_student_session_overlap",
        ),
    )


class SessionEvent(Base):
    __tablename__ = "session_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    session: Mapped[Session] = relationship(back_populates="events")
