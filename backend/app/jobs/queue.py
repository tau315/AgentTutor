import json
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings


READY_QUEUE = "agenttutor:jobs:ready"
SCHEDULED_QUEUE = "agenttutor:jobs:scheduled"


class JobQueue:
    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def enqueue(self, job_type: str, payload: dict[str, Any], run_at: datetime | None = None, attempt: int = 0) -> None:
        job = json.dumps({"type": job_type, "payload": payload, "attempt": attempt})
        if run_at and run_at > datetime.now(timezone.utc):
            await self.redis.zadd(SCHEDULED_QUEUE, {job: run_at.timestamp()})
        else:
            await self.redis.lpush(READY_QUEUE, job)

    async def move_due_jobs(self) -> int:
        now = datetime.now(timezone.utc).timestamp()
        moved = 0
        while True:
            jobs = await self.redis.zpopmin(SCHEDULED_QUEUE, count=1)
            if not jobs:
                break
            job, score = jobs[0]
            if score > now:
                await self.redis.zadd(SCHEDULED_QUEUE, {job: score})
                break
            await self.redis.lpush(READY_QUEUE, job)
            moved += 1
        return moved

    async def next_job(self) -> dict[str, Any] | None:
        result = await self.redis.rpop(READY_QUEUE)
        return json.loads(result) if result else None

    async def close(self) -> None:
        await self.redis.aclose()
