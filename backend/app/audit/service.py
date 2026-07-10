from app.core.security import CurrentUser


class AuditService:
    async def record_agent_action(self, user: CurrentUser, action: dict) -> None:
        raise NotImplementedError("Audit logging is not implemented yet.")

