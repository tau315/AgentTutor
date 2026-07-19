from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.messaging.models import Conversation
from app.users.models import TutorProfile


class MessagingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _details(self):
        return select(Conversation).execution_options(populate_existing=True).options(
            selectinload(Conversation.student),
            selectinload(Conversation.tutor_profile).selectinload(TutorProfile.user),
            selectinload(Conversation.messages),
        )

    async def list_for_user(self, user_id: str, role: str) -> list[Conversation]:
        query = self._details()
        if role == "student":
            query = query.where(Conversation.student_id == user_id)
        elif role == "tutor":
            query = query.join(Conversation.tutor_profile).where(TutorProfile.user_id == user_id)
        result = await self.db.execute(query.order_by(Conversation.created_at.desc()))
        return list(result.scalars().unique().all())

    async def get(self, conversation_id: str) -> Conversation | None:
        result = await self.db.execute(self._details().where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    async def find(self, student_id: str, tutor_id: str) -> Conversation | None:
        result = await self.db.execute(self._details().where(Conversation.student_id == student_id, Conversation.tutor_profile_id == tutor_id))
        return result.scalar_one_or_none()
