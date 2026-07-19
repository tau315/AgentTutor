from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import CurrentUser
from app.notifications.models import Notification
from app.agent.models import Reminder
from app.jobs.queue import JobQueue
from app.notifications.schemas import NotificationRead


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_user(self, user: CurrentUser) -> list[NotificationRead]:
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100)
        )
        return [NotificationRead.model_validate(item) for item in result.scalars().all()]

    async def create_many(self, user_ids: list[str], kind: str, title: str, body: str, resource_id: str | None = None) -> list[Notification]:
        items = [Notification(user_id=user_id, kind=kind, title=title, body=body, resource_id=resource_id) for user_id in set(user_ids)]
        self.db.add_all(items)
        await self.db.commit()
        return items

    async def mark_read(self, user: CurrentUser, notification_id: str) -> NotificationRead:
        item = await self.db.get(Notification, notification_id)
        if item is None or item.user_id != user.id:
            raise AppError("Notification not found", status.HTTP_404_NOT_FOUND)
        item.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        return NotificationRead.model_validate(item)

    async def schedule_reminder(self, user: CurrentUser, body: str, remind_at: datetime) -> Reminder:
        if remind_at.tzinfo is None or remind_at.utcoffset() is None:
            raise AppError("Reminder time must include a UTC offset")
        remind_at = remind_at.astimezone(timezone.utc)
        if remind_at <= datetime.now(timezone.utc):
            raise AppError("Reminder time must be in the future")
        item = Reminder(user_id=user.id, body=body, remind_at=remind_at)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        queue = JobQueue()
        try:
            await queue.enqueue("user_reminder", {"reminder_id": item.id}, remind_at)
        finally:
            await queue.close()
        return item
