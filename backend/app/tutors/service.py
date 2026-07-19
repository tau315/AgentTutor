from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import CurrentUser
from app.tutors.repository import TutorRepository
from app.tutors.schemas import AdminTutorUpdate, TutorProfileUpdate, TutorSearchFilters, TutorSummary
from app.users.models import TutorSubject


class TutorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.tutors = TutorRepository(db)

    async def search_tutors(
        self, filters: TutorSearchFilters
    ) -> list[TutorSummary]:
        profiles = await self.tutors.search(filters)
        return [self._to_summary(profile) for profile in profiles]

    async def get_tutor(self, tutor_id: str) -> TutorSummary:
        profile = await self.tutors.get_public_by_id(tutor_id)
        if profile is None:
            raise AppError("Tutor not found", status.HTTP_404_NOT_FOUND)
        return self._to_summary(profile)

    async def get_my_profile(self, user: CurrentUser) -> TutorSummary:
        profile = await self._get_owned_profile(user.id)
        return self._to_summary(profile)

    async def admin_list(self) -> list[TutorSummary]:
        return [self._to_summary(item) for item in await self.tutors.list_all()]

    async def admin_update(self, tutor_id: str, data: AdminTutorUpdate) -> TutorSummary:
        profile = await self.tutors.get_any_by_id(tutor_id)
        if profile is None:
            raise AppError("Tutor not found", status.HTTP_404_NOT_FOUND)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self.tutors.commit()
        return self._to_summary(await self.tutors.get_any_by_id(tutor_id))

    async def update_my_profile(
        self, user: CurrentUser, data: TutorProfileUpdate
    ) -> TutorSummary:
        profile = await self._get_owned_profile(user.id)
        updates = data.model_dump(exclude_unset=True, exclude={"subjects", "display_name"})
        for field, value in updates.items():
            setattr(profile, field, value)

        if "display_name" in data.model_fields_set:
            profile.user.display_name = data.display_name

        if data.subjects is not None:
            profile.subjects.clear()
            profile.subjects.extend(
                TutorSubject(
                    subject=item.subject.strip(),
                    expertise=item.expertise.strip() if item.expertise else None,
                )
                for item in data.subjects
            )

        if profile.is_active and (
            not profile.user.display_name
            or profile.hourly_rate is None
            or not profile.subjects
        ):
            raise AppError(
                "Add a display name, hourly rate, and at least one subject before activating your profile"
            )

        await self.tutors.commit()
        profile = await self._get_owned_profile(user.id)
        return self._to_summary(profile)

    async def _get_owned_profile(self, user_id: str):
        profile = await self.tutors.get_by_user_id(user_id)
        if profile is None:
            raise AppError("Tutor profile not found", status.HTTP_404_NOT_FOUND)
        return profile

    @staticmethod
    def _to_summary(profile) -> TutorSummary:
        return TutorSummary(
            id=profile.id,
            display_name=profile.user.display_name or "Unnamed tutor",
            bio=profile.bio,
            subjects=profile.subjects,
            hourly_rate=profile.hourly_rate,
            rating=profile.rating,
            is_active=profile.is_active,
        )
