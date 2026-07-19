from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(
        String, nullable=False, default="America/New_York"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )

    student_profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    tutor_profile: Mapped["TutorProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    grade_level: Mapped[str | None] = mapped_column(String(50))
    learning_goals: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="student_profile")


class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    bio: Mapped[str | None] = mapped_column(Text)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship(back_populates="tutor_profile")
    subjects: Mapped[list["TutorSubject"]] = relationship(
        back_populates="tutor_profile",
        cascade="all, delete-orphan",
        order_by="TutorSubject.subject",
    )


class TutorSubject(Base):
    __tablename__ = "tutor_subjects"
    __table_args__ = (
        UniqueConstraint("tutor_profile_id", "subject", name="uq_tutor_subject"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tutor_profile_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    expertise: Mapped[str | None] = mapped_column(String(150), index=True)

    tutor_profile: Mapped[TutorProfile] = relationship(back_populates="subjects")
