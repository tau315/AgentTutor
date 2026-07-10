from app.core.security import CurrentUser


class AnalyticsService:
    async def dashboard_metrics(self, user: CurrentUser) -> dict:
        raise NotImplementedError("Analytics dashboards are not implemented yet.")

