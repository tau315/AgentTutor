from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas import AnalyticsOverview
from app.audit.models import AuditLog
from app.sessions.models import Session
from app.users.models import TutorProfile, User


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dashboard_metrics(self) -> AnalyticsOverview:
        async def count(model, *filters) -> int:
            return int((await self.db.execute(select(func.count()).select_from(model).where(*filters))).scalar_one())
        tool_logs = list((await self.db.scalars(select(AuditLog).where(AuditLog.action == "agent.tool_result"))).all())
        durations = [float(item.details.get("duration_ms", 0)) for item in tool_logs]
        return AnalyticsOverview(
            user_count=await count(User),
            tutor_count=await count(TutorProfile),
            active_tutor_count=await count(TutorProfile, TutorProfile.is_active.is_(True)),
            session_count=await count(Session),
            booked_session_count=await count(Session, Session.status == "booked"),
            ai_usage_count=await count(AuditLog, AuditLog.action.like("agent.%")),
            agent_tool_calls=len(tool_logs),
            failed_agent_tool_calls=sum(item.details.get("status") != "success" for item in tool_logs),
            average_tool_latency_ms=round(sum(durations) / len(durations), 2) if durations else 0,
        )
