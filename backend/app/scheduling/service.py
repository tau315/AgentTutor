from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import CurrentUser
from app.scheduling.models import AvailabilityWindow, BlockedTime
from app.scheduling.repository import SchedulingRepository
from app.scheduling.schemas import (
    AvailabilityReplace,
    AvailabilityResult,
    AvailabilityWindowRead,
    BlockedTimeCreate,
    BlockedTimeRead,
)
from app.tutors.repository import TutorRepository


class SchedulingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.schedules = SchedulingRepository(db)
        self.tutors = TutorRepository(db)

    async def get_my_availability(self, user: CurrentUser) -> list[AvailabilityWindowRead]:
        tutor = await self._owned_tutor(user.id)
        return [AvailabilityWindowRead.model_validate(item) for item in await self.schedules.list_windows(tutor.id)]

    async def replace_my_availability(
        self, user: CurrentUser, data: AvailabilityReplace
    ) -> list[AvailabilityWindowRead]:
        tutor = await self._owned_tutor(user.id)
        windows = [
            AvailabilityWindow(tutor_profile_id=tutor.id, **item.model_dump())
            for item in data.windows
        ]
        saved = await self.schedules.replace_windows(tutor.id, windows)
        return [AvailabilityWindowRead.model_validate(item) for item in saved]

    async def list_my_blocks(self, user: CurrentUser) -> list[BlockedTimeRead]:
        tutor = await self._owned_tutor(user.id)
        return [BlockedTimeRead.model_validate(item) for item in await self.schedules.list_blocks(tutor.id)]

    async def add_block(self, user: CurrentUser, data: BlockedTimeCreate) -> BlockedTimeRead:
        tutor = await self._owned_tutor(user.id)
        block = BlockedTime(
            tutor_profile_id=tutor.id,
            starts_at=data.starts_at.astimezone(timezone.utc),
            ends_at=data.ends_at.astimezone(timezone.utc),
            reason=data.reason,
        )
        self.db.add(block)
        await self.db.commit()
        await self.db.refresh(block)
        return BlockedTimeRead.model_validate(block)

    async def delete_block(self, user: CurrentUser, block_id: str) -> None:
        tutor = await self._owned_tutor(user.id)
        block = await self.db.get(BlockedTime, block_id)
        if block is None or block.tutor_profile_id != tutor.id:
            raise AppError("Blocked time not found", status.HTTP_404_NOT_FOUND)
        await self.db.delete(block)
        await self.db.commit()

    async def check(self, tutor_id: str, starts_at: datetime, ends_at: datetime) -> AvailabilityResult:
        if starts_at >= ends_at:
            return AvailabilityResult(available=False, reason="End time must follow start time")
        starts_utc = starts_at.astimezone(timezone.utc)
        ends_utc = ends_at.astimezone(timezone.utc)
        windows = await self.schedules.list_windows(tutor_id)
        for window in windows:
            zone = ZoneInfo(window.timezone)
            local_start = starts_utc.astimezone(zone)
            local_end = ends_utc.astimezone(zone)
            fits = (
                local_start.date() == local_end.date()
                and local_start.weekday() == window.weekday
                and local_start.time().replace(tzinfo=None) >= window.start_time
                and local_end.time().replace(tzinfo=None) <= window.end_time
            )
            if fits:
                if await self.schedules.has_block(tutor_id, starts_utc, ends_utc):
                    return AvailabilityResult(available=False, reason="Tutor blocked this time")
                return AvailabilityResult(available=True)
        return AvailabilityResult(available=False, reason="Time is outside weekly availability")

    async def _owned_tutor(self, user_id: str):
        tutor = await self.tutors.get_by_user_id(user_id)
        if tutor is None:
            raise AppError("Tutor profile not found", status.HTTP_404_NOT_FOUND)
        return tutor
