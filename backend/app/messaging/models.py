from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base
from app.users.models import TutorProfile, User, new_id


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("student_id", "tutor_profile_id", name="uq_conversation_participants"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    tutor_profile_id: Mapped[str] = mapped_column(ForeignKey("tutor_profiles.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped[User] = relationship()
    tutor_profile: Mapped[TutorProfile] = relationship()
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
