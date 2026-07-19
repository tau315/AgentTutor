from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.audit.schemas import AuditLogRead


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record(self, actor_user_id: str | None, action: str, resource_type: str, resource_id: str | None = None, details: dict | None = None, commit: bool = True) -> AuditLog:
        item = AuditLog(actor_user_id=actor_user_id, action=action, resource_type=resource_type, resource_id=resource_id, details=details or {})
        self.db.add(item)
        if commit:
            await self.db.commit()
        return item

    async def list_logs(self, limit: int = 100) -> list[AuditLogRead]:
        result = await self.db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
        return [AuditLogRead.model_validate(item) for item in result.scalars().all()]
