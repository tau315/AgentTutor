from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import ReportCreate, ReportRead, ReportUpdate
from app.admin.service import AdminService
from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, get_current_user, require_roles


router = APIRouter()


@router.post("/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(data: ReportCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return await AdminService(db).create_report(current_user, data)


@router.get("/reports", response_model=list[ReportRead])
async def list_reports(_: CurrentUser = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db_session)):
    return await AdminService(db).list_reports()


@router.patch("/reports/{report_id}", response_model=ReportRead)
async def update_report(report_id: str, data: ReportUpdate, admin: CurrentUser = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db_session)):
    return await AdminService(db).update_report(admin, report_id, data)
