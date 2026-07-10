from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user
from app.tutors.schemas import TutorSearchFilters, TutorSummary
from app.tutors.service import TutorService


router = APIRouter()


@router.get("", response_model=list[TutorSummary])
async def search_tutors(
    subject: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> list[TutorSummary]:
    filters = TutorSearchFilters(subject=subject)
    return await TutorService().search_tutors(current_user, filters)

