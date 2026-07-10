from app.core.security import CurrentUser
from app.tutors.schemas import TutorSearchFilters, TutorSummary


class TutorService:
    async def search_tutors(
        self,
        user: CurrentUser,
        filters: TutorSearchFilters,
    ) -> list[TutorSummary]:
        raise NotImplementedError("Tutor search is not implemented yet.")

    async def recommend_tutors(self, user: CurrentUser) -> list[TutorSummary]:
        raise NotImplementedError("Tutor recommendations are not implemented yet.")

