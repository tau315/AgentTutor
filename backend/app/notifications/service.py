from app.core.security import CurrentUser


class NotificationService:
    async def create_notification(self, user: CurrentUser, data: dict) -> dict:
        raise NotImplementedError("Notifications are not implemented yet.")

    async def create_reminder(self, user: CurrentUser, data: dict) -> dict:
        raise NotImplementedError("Reminders are not implemented yet.")

