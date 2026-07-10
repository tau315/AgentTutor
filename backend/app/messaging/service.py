from app.core.security import CurrentUser


class MessagingService:
    async def list_threads(self, user: CurrentUser) -> list[dict]:
        raise NotImplementedError("Message threads are not implemented yet.")

    async def send_message(self, user: CurrentUser, data: dict) -> dict:
        raise NotImplementedError("Sending messages is not implemented yet.")

