import asyncio
from datetime import datetime, timedelta, timezone

from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.jobs.queue import JobQueue
from app.notifications.service import NotificationService
from app.agent.models import Reminder
from app.sessions.repository import SessionRepository


async def handle_job(job: dict, queue: JobQueue) -> None:
    if job["type"] == "notification_delivery":
        logger.info("In-app notification delivered notification_id=%s", job["payload"]["notification_id"])
        return
    if job["type"] == "session_reminder":
        async with AsyncSessionLocal() as db:
            session = await SessionRepository(db).get(job["payload"]["session_id"])
            if session and session.status == "booked":
                notifications = await NotificationService(db).create_many(
                    [session.student_id, session.tutor_profile.user_id],
                    "session_reminder",
                    "Tutoring session tomorrow",
                    f"Your {session.subject} session starts at {session.starts_at.isoformat()}.",
                    session.id,
                )
                for notification in notifications:
                    await queue.enqueue(
                        "notification_delivery",
                        {"notification_id": notification.id},
                    )
        return
    if job["type"] == "user_reminder":
        async with AsyncSessionLocal() as db:
            reminder = await db.get(Reminder, job["payload"]["reminder_id"])
            if reminder and reminder.status == "scheduled":
                notifications = await NotificationService(db).create_many(
                    [reminder.user_id],
                    "reminder",
                    "Reminder",
                    reminder.body,
                    reminder.id,
                )
                reminder.status = "delivered"
                await db.commit()
                for notification in notifications:
                    await queue.enqueue("notification_delivery", {"notification_id": notification.id})


async def run_worker() -> None:
    queue = JobQueue()
    logger.info("Background worker started")
    try:
        while True:
            await queue.move_due_jobs()
            job = await queue.next_job()
            if job:
                try:
                    await handle_job(job, queue)
                except Exception:
                    logger.exception("Background job failed type=%s", job.get("type"))
                    attempt = int(job.get("attempt", 0)) + 1
                    if attempt <= 3:
                        await queue.enqueue(
                            job["type"],
                            job["payload"],
                            datetime.now(timezone.utc) + timedelta(seconds=2**attempt),
                            attempt,
                        )
            else:
                await asyncio.sleep(1)
    finally:
        await queue.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
