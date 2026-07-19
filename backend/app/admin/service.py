from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import Report
from app.admin.schemas import ReportCreate, ReportRead, ReportUpdate
from app.audit.service import AuditService
from app.core.errors import AppError
from app.core.security import CurrentUser


class AdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_report(self, user: CurrentUser, data: ReportCreate) -> ReportRead:
        item = Report(reporter_id=user.id, **data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return ReportRead.model_validate(item)

    async def list_reports(self) -> list[ReportRead]:
        result = await self.db.execute(select(Report).order_by(Report.created_at.desc()))
        return [ReportRead.model_validate(item) for item in result.scalars().all()]

    async def update_report(self, admin: CurrentUser, report_id: str, data: ReportUpdate) -> ReportRead:
        item = await self.db.get(Report, report_id)
        if item is None:
            raise AppError("Report not found", status.HTTP_404_NOT_FOUND)
        item.status = data.status.value
        item.admin_notes = data.admin_notes
        await AuditService(self.db).record(admin.id, "report.updated", "report", item.id, {"status": item.status}, commit=False)
        await self.db.commit()
        return ReportRead.model_validate(item)
