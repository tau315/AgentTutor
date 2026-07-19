from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling.models import AvailabilityWindow, BlockedTime


class SchedulingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_windows(self, tutor_profile_id: str) -> list[AvailabilityWindow]:
        result = await self.db.execute(
            select(AvailabilityWindow)
            .where(AvailabilityWindow.tutor_profile_id == tutor_profile_id)
            .order_by(AvailabilityWindow.weekday, AvailabilityWindow.start_time)
        )
        return list(result.scalars().all())

    async def replace_windows(
        self, tutor_profile_id: str, windows: list[AvailabilityWindow]
    ) -> list[AvailabilityWindow]:
        await self.db.execute(
            delete(AvailabilityWindow).where(
                AvailabilityWindow.tutor_profile_id == tutor_profile_id
            )
        )
        self.db.add_all(windows)
        await self.db.commit()
        return await self.list_windows(tutor_profile_id)

    async def list_blocks(self, tutor_profile_id: str) -> list[BlockedTime]:
        result = await self.db.execute(
            select(BlockedTime)
            .where(BlockedTime.tutor_profile_id == tutor_profile_id)
            .order_by(BlockedTime.starts_at)
        )
        return list(result.scalars().all())

    async def has_block(
        self, tutor_profile_id: str, starts_at: datetime, ends_at: datetime
    ) -> bool:
        result = await self.db.execute(
            select(BlockedTime.id).where(
                BlockedTime.tutor_profile_id == tutor_profile_id,
                BlockedTime.starts_at < ends_at,
                BlockedTime.ends_at > starts_at,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None
