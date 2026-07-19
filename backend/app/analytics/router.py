from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas import AnalyticsOverview
from app.analytics.service import AnalyticsService
from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, require_roles


router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(_: CurrentUser = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db_session)):
    return await AnalyticsService(db).dashboard_metrics()
