from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.schemas import AuditLogRead
from app.audit.service import AuditService
from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, require_roles


router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(limit: int = Query(default=100, ge=1, le=500), _: CurrentUser = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db_session)):
    return await AuditService(db).list_logs(limit)
