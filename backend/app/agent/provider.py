import asyncio
import json
from urllib import error, request

from app.core.config import settings


class OllamaProvider:
    async def structured_chat(self, messages: list[dict], schema: dict) -> dict:
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0},
        }
        return await asyncio.to_thread(self._post, payload)

    @staticmethod
    def _post(payload: dict) -> dict:
        http_request = request.Request(
            f"{settings.llm_base_url.rstrip('/')}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError) as exc:
            raise RuntimeError("The configured Ollama service is unavailable") from exc
        return json.loads(body["message"]["content"])
