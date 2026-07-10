from app.core.security import CurrentUser


class SchedulingService:
    async def check_availability(self, user: CurrentUser, filters: dict) -> list[dict]:
        raise NotImplementedError("Availability checks are not implemented yet.")

    async def detect_conflicts(self, user: CurrentUser, session_data: dict) -> list[dict]:
        raise NotImplementedError("Schedule conflict checks are not implemented yet.")

