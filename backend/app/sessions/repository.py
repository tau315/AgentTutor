from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.sessions.models import Session
from app.sessions.schemas import SessionScope
from app.users.models import TutorProfile


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _details(self):
        return select(Session).options(
            selectinload(Session.student),
            selectinload(Session.tutor_profile).selectinload(TutorProfile.user),
            selectinload(Session.events),
        )

    async def get(self, session_id: str) -> Session | None:
        result = await self.db.execute(self._details().where(Session.id == session_id))
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: str, role: str, scope: SessionScope, now: datetime
    ) -> list[Session]:
        query = self._details()
        if role == "student":
            query = query.where(Session.student_id == user_id)
        elif role == "tutor":
            query = query.join(Session.tutor_profile).where(TutorProfile.user_id == user_id)
        if scope == SessionScope.upcoming:
            query = query.where(Session.ends_at >= now, Session.status.in_(["requested", "booked"]))
        elif scope == SessionScope.history:
            query = query.where(or_(Session.ends_at < now, Session.status.in_(["rejected", "cancelled", "completed"])))
        result = await self.db.execute(query.order_by(Session.starts_at.asc()))
        return list(result.scalars().unique().all())

    async def find_conflict(
        self,
        student_id: str,
        tutor_profile_id: str,
        starts_at: datetime,
        ends_at: datetime,
        exclude_session_id: str | None = None,
    ) -> Session | None:
        query = select(Session).where(
            Session.status.in_(["requested", "booked"]),
            Session.starts_at < ends_at,
            Session.ends_at > starts_at,
            or_(Session.student_id == student_id, Session.tutor_profile_id == tutor_profile_id),
        )
        if exclude_session_id:
            query = query.where(Session.id != exclude_session_id)
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()
