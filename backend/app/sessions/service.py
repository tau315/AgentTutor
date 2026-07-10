from app.core.security import CurrentUser
from app.sessions.schemas import SessionSummary


class SessionService:
    async def list_upcoming(self, user: CurrentUser) -> list[SessionSummary]:
        raise NotImplementedError("Upcoming sessions are not implemented yet.")

    async def book_session(self, user: CurrentUser, data: dict) -> SessionSummary:
        raise NotImplementedError("Session booking is not implemented yet.")

    async def reschedule_session(self, user: CurrentUser, session_id: str, data: dict) -> SessionSummary:
        raise NotImplementedError("Session rescheduling is not implemented yet.")

    async def cancel_session(self, user: CurrentUser, session_id: str) -> SessionSummary:
        raise NotImplementedError("Session cancellation is not implemented yet.")

