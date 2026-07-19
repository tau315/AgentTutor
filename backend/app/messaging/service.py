from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import CurrentUser, Role
from app.admin.models import Report
from app.messaging.models import Conversation, Message
from app.messaging.repository import MessagingRepository
from app.messaging.schemas import ConversationCreate, ConversationRead, MessageCreate
from app.notifications.service import NotificationService
from app.tutors.repository import TutorRepository
from app.users.repository import UserRepository


class MessagingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.conversations = MessagingRepository(db)

    async def list_threads(self, user: CurrentUser) -> list[ConversationRead]:
        if user.role == Role.admin:
            raise AppError(
                "Admins may only open conversations connected to an active report",
                status.HTTP_403_FORBIDDEN,
            )
        items = await self.conversations.list_for_user(user.id, user.role.value)
        return [self._read(item) for item in items]

    async def admin_review_thread(
        self, conversation_id: str, report_id: str
    ) -> ConversationRead:
        thread = await self._get(conversation_id)
        report = await self.db.get(Report, report_id)
        participant_ids = {thread.student_id, thread.tutor_profile.user_id}
        if (
            report is None
            or report.status not in {"open", "reviewing"}
            or report.target_user_id not in participant_ids
        ):
            raise AppError(
                "An active report involving a participant is required",
                status.HTTP_403_FORBIDDEN,
            )
        return self._read(thread)

    async def create_thread(self, user: CurrentUser, data: ConversationCreate) -> ConversationRead:
        if user.role == Role.student and data.tutor_id:
            tutor = await TutorRepository(self.db).get_public_by_id(data.tutor_id)
            if tutor is None:
                raise AppError("Tutor not found", status.HTTP_404_NOT_FOUND)
            student_id, tutor_id = user.id, tutor.id
        elif user.role == Role.tutor and data.student_id:
            tutor = await TutorRepository(self.db).get_by_user_id(user.id)
            student = await UserRepository(self.db).get_by_id(data.student_id)
            if tutor is None or student is None or student.role != "student":
                raise AppError("Student not found", status.HTTP_404_NOT_FOUND)
            student_id, tutor_id = student.id, tutor.id
        else:
            raise AppError("Conversation target does not match your role", status.HTTP_403_FORBIDDEN)
        existing = await self.conversations.find(student_id, tutor_id)
        if existing:
            return self._read(existing)
        item = Conversation(student_id=student_id, tutor_profile_id=tutor_id)
        self.db.add(item)
        await self.db.commit()
        return self._read(await self._get(item.id))

    async def send_message(self, user: CurrentUser, conversation_id: str, data: MessageCreate) -> ConversationRead:
        thread = await self._get(conversation_id)
        self._require_participant(user, thread)
        self.db.add(Message(conversation_id=thread.id, sender_id=user.id, body=data.body.strip()))
        await self.db.commit()
        recipient_id = thread.tutor_profile.user_id if user.id == thread.student_id else thread.student_id
        await NotificationService(self.db).create_many(
            [recipient_id],
            "message",
            "New message",
            data.body.strip()[:200],
            thread.id,
        )
        return self._read(await self._get(thread.id))

    async def get_thread(self, user: CurrentUser, conversation_id: str) -> ConversationRead:
        thread = await self._get(conversation_id)
        self._require_participant(user, thread)
        return self._read(thread)

    async def _get(self, conversation_id: str) -> Conversation:
        item = await self.conversations.get(conversation_id)
        if item is None:
            raise AppError("Conversation not found", status.HTTP_404_NOT_FOUND)
        return item

    @staticmethod
    def _require_participant(user: CurrentUser, item: Conversation) -> None:
        if item.student_id != user.id and item.tutor_profile.user_id != user.id:
            raise AppError("You cannot view this conversation", status.HTTP_403_FORBIDDEN)

    @staticmethod
    def _read(item: Conversation) -> ConversationRead:
        return ConversationRead(
            id=item.id,
            student_id=item.student_id,
            student_name=item.student.display_name or item.student.email,
            tutor_id=item.tutor_profile_id,
            tutor_name=item.tutor_profile.user.display_name or "Unnamed tutor",
            created_at=item.created_at,
            messages=item.messages,
        )
