from datetime import datetime, timedelta, timezone

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import CurrentUser, Role
from app.audit.service import AuditService
from app.core.logging import logger
from app.jobs.queue import JobQueue
from app.notifications.service import NotificationService
from app.scheduling.service import SchedulingService
from app.sessions.models import Session, SessionEvent
from app.sessions.repository import SessionRepository
from app.sessions.schemas import SessionDecision, SessionRequest, SessionReschedule, SessionScope, SessionSummary
from app.tutors.repository import TutorRepository


class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.sessions = SessionRepository(db)
        self.tutors = TutorRepository(db)

    async def list_sessions(self, user: CurrentUser, scope: SessionScope) -> list[SessionSummary]:
        items = await self.sessions.list_for_user(user.id, user.role.value, scope, datetime.now(timezone.utc))
        return [self._summary(item) for item in items]

    async def request_session(self, user: CurrentUser, data: SessionRequest) -> SessionSummary:
        tutor = await self.tutors.get_public_by_id(data.tutor_id)
        if tutor is None:
            raise AppError("Tutor not found", status.HTTP_404_NOT_FOUND)
        starts_at = data.starts_at.astimezone(timezone.utc)
        ends_at = data.ends_at.astimezone(timezone.utc)
        if starts_at <= datetime.now(timezone.utc):
            raise AppError("Sessions must be requested in the future")
        await self._validate_time(user.id, tutor.id, starts_at, ends_at)
        item = Session(
            student_id=user.id,
            tutor_profile_id=tutor.id,
            requested_by_user_id=user.id,
            subject=data.subject.strip(),
            notes=data.notes,
            starts_at=starts_at,
            ends_at=ends_at,
            status="requested",
        )
        item.events.append(SessionEvent(actor_user_id=user.id, action="requested"))
        self.db.add(item)
        await self._commit_conflict_safe()
        item = await self._get(item.id)
        await self._after_change(user.id, item, "session.requested")
        return self._summary(item)

    async def decide(self, user: CurrentUser, session_id: str, accept: bool, data: SessionDecision) -> SessionSummary:
        item = await self._get(session_id)
        if item.status != "requested":
            raise AppError("Only requested sessions can be accepted or rejected")
        is_tutor = item.tutor_profile.user_id == user.id
        is_student = item.student_id == user.id
        if not (is_tutor or is_student) or item.requested_by_user_id == user.id:
            raise AppError("The other participant must make this decision", status.HTTP_403_FORBIDDEN)
        item.status = "booked" if accept else "rejected"
        item.cancellation_reason = None if accept else data.reason
        item.events.append(SessionEvent(actor_user_id=user.id, action=item.status, details=data.reason))
        await self.db.commit()
        item = await self._get(item.id)
        await self._after_change(user.id, item, f"session.{item.status}")
        return self._summary(item)

    async def cancel(self, user: CurrentUser, session_id: str, data: SessionDecision) -> SessionSummary:
        item = await self._get(session_id)
        self._require_participant_or_admin(user, item)
        if item.status not in {"requested", "booked"}:
            raise AppError("This session can no longer be cancelled")
        item.status = "cancelled"
        item.cancellation_reason = data.reason
        item.events.append(SessionEvent(actor_user_id=user.id, action="cancelled", details=data.reason))
        await self.db.commit()
        item = await self._get(item.id)
        await self._after_change(user.id, item, "session.cancelled")
        return self._summary(item)

    async def reschedule(self, user: CurrentUser, session_id: str, data: SessionReschedule) -> SessionSummary:
        item = await self._get(session_id)
        self._require_participant_or_admin(user, item)
        if item.status not in {"requested", "booked"}:
            raise AppError("This session can no longer be rescheduled")
        starts_at = data.starts_at.astimezone(timezone.utc)
        ends_at = data.ends_at.astimezone(timezone.utc)
        await self._validate_time(item.student_id, item.tutor_profile_id, starts_at, ends_at, item.id)
        old_time = f"{item.starts_at.isoformat()} to {item.ends_at.isoformat()}"
        item.starts_at = starts_at
        item.ends_at = ends_at
        item.requested_by_user_id = user.id
        item.status = "requested"
        item.events.append(SessionEvent(actor_user_id=user.id, action="rescheduled", details=f"Previous time: {old_time}"))
        await self._commit_conflict_safe()
        item = await self._get(item.id)
        await self._after_change(user.id, item, "session.rescheduled")
        return self._summary(item)

    async def _after_change(self, actor_id: str, item: Session, action: str) -> None:
        title_by_action = {
            "session.requested": "New tutoring request",
            "session.booked": "Tutoring session booked",
            "session.rejected": "Tutoring request rejected",
            "session.cancelled": "Tutoring session cancelled",
            "session.rescheduled": "New session time proposed",
        }
        title = title_by_action[action]
        body = f"{item.subject}: {item.starts_at.isoformat()} to {item.ends_at.isoformat()}"
        await AuditService(self.db).record(
            actor_id, action, "session", item.id, {"status": item.status}, commit=False
        )
        notifications = await NotificationService(self.db).create_many(
            [item.student_id, item.tutor_profile.user_id],
            action.removeprefix("session."),
            title,
            body,
            item.id,
        )
        queue = JobQueue()
        try:
            for notification in notifications:
                await queue.enqueue(
                    "notification_delivery", {"notification_id": notification.id}
                )
            if action == "session.booked":
                await queue.enqueue(
                    "session_reminder",
                    {"session_id": item.id},
                    item.starts_at - timedelta(hours=24),
                )
        except Exception:
            logger.exception("Could not enqueue session jobs session_id=%s", item.id)
        finally:
            await queue.close()

    async def _validate_time(self, student_id: str, tutor_id: str, starts_at: datetime, ends_at: datetime, exclude_id: str | None = None) -> None:
        availability = await SchedulingService(self.db).check(tutor_id, starts_at, ends_at)
        if not availability.available:
            raise AppError(availability.reason or "Tutor is unavailable", status.HTTP_409_CONFLICT)
        conflict = await self.sessions.find_conflict(student_id, tutor_id, starts_at, ends_at, exclude_id)
        if conflict:
            who = "student" if conflict.student_id == student_id else "tutor"
            raise AppError(f"The {who} already has a session during this time", status.HTTP_409_CONFLICT)

    async def _commit_conflict_safe(self) -> None:
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise AppError("This time was just booked by another request", status.HTTP_409_CONFLICT) from exc

    async def _get(self, session_id: str) -> Session:
        item = await self.sessions.get(session_id)
        if item is None:
            raise AppError("Session not found", status.HTTP_404_NOT_FOUND)
        return item

    @staticmethod
    def _require_participant_or_admin(user: CurrentUser, item: Session) -> None:
        if user.role == Role.admin:
            return
        if item.student_id != user.id and item.tutor_profile.user_id != user.id:
            raise AppError("You cannot manage this session", status.HTTP_403_FORBIDDEN)

    @staticmethod
    def _summary(item: Session) -> SessionSummary:
        return SessionSummary(
            id=item.id,
            tutor_id=item.tutor_profile_id,
            tutor_name=item.tutor_profile.user.display_name or "Unnamed tutor",
            student_id=item.student_id,
            student_name=item.student.display_name or item.student.email,
            subject=item.subject,
            notes=item.notes,
            starts_at=item.starts_at,
            ends_at=item.ends_at,
            status=item.status,
            requested_by_user_id=item.requested_by_user_id,
            cancellation_reason=item.cancellation_reason,
            events=item.events,
        )
