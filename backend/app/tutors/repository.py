from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.tutors.schemas import TutorSearchFilters, TutorSort
from app.users.models import TutorProfile, TutorSubject, User


class TutorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _with_details(self):
        return (
            select(TutorProfile)
            .join(TutorProfile.user)
            .options(selectinload(TutorProfile.user), selectinload(TutorProfile.subjects))
        )

    async def search(self, filters: TutorSearchFilters) -> list[TutorProfile]:
        query = self._with_details().where(
            TutorProfile.is_active.is_(True), User.is_active.is_(True)
        )

        if filters.subject:
            query = query.where(
                TutorProfile.subjects.any(
                    TutorSubject.subject.ilike(f"%{filters.subject.strip()}%")
                )
            )
        if filters.expertise:
            query = query.where(
                TutorProfile.subjects.any(
                    TutorSubject.expertise.ilike(f"%{filters.expertise.strip()}%")
                )
            )

        if filters.sort == TutorSort.price_low:
            query = query.order_by(TutorProfile.hourly_rate.asc().nulls_last())
        elif filters.sort == TutorSort.name:
            query = query.order_by(User.display_name.asc().nulls_last())
        elif filters.sort == TutorSort.rating:
            query = query.order_by(TutorProfile.rating.desc())
        elif filters.subject:
            relevance = case(
                (
                    TutorProfile.subjects.any(
                        TutorSubject.subject.ilike(filters.subject.strip())
                    ),
                    2,
                ),
                else_=0,
            )
            query = query.order_by(relevance.desc(), TutorProfile.rating.desc())
        else:
            query = query.order_by(TutorProfile.rating.desc())

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_public_by_id(self, tutor_id: str) -> TutorProfile | None:
        result = await self.db.execute(
            self._with_details().where(
                TutorProfile.id == tutor_id,
                TutorProfile.is_active.is_(True),
                User.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> TutorProfile | None:
        result = await self.db.execute(
            self._with_details().where(TutorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_any_by_id(self, tutor_id: str) -> TutorProfile | None:
        result = await self.db.execute(
            self._with_details().where(TutorProfile.id == tutor_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[TutorProfile]:
        result = await self.db.execute(
            self._with_details().order_by(TutorProfile.is_active.desc(), User.display_name)
        )
        return list(result.scalars().unique().all())

    async def commit(self) -> None:
        await self.db.commit()
