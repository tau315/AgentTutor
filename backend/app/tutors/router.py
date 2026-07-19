from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, require_roles
from app.tutors.schemas import (
    AdminTutorUpdate,
    TutorProfileUpdate,
    TutorSearchFilters,
    TutorSort,
    TutorSummary,
)
from app.tutors.service import TutorService


router = APIRouter()


@router.get("/admin/all", response_model=list[TutorSummary])
async def admin_list_tutors(_: CurrentUser = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db_session)):
    return await TutorService(db).admin_list()


@router.patch("/admin/{tutor_id}", response_model=TutorSummary)
async def admin_update_tutor(tutor_id: str, data: AdminTutorUpdate, _: CurrentUser = Depends(require_roles(Role.admin)), db: AsyncSession = Depends(get_db_session)):
    return await TutorService(db).admin_update(tutor_id, data)


@router.get("", response_model=list[TutorSummary])
async def search_tutors(
    subject: str | None = Query(default=None, max_length=100),
    expertise: str | None = Query(default=None, max_length=150),
    sort: TutorSort = TutorSort.relevance,
    db: AsyncSession = Depends(get_db_session),
) -> list[TutorSummary]:
    filters = TutorSearchFilters(subject=subject, expertise=expertise, sort=sort)
    return await TutorService(db).search_tutors(filters)


@router.get("/me", response_model=TutorSummary)
async def get_my_tutor_profile(
    current_user: CurrentUser = Depends(require_roles(Role.tutor)),
    db: AsyncSession = Depends(get_db_session),
) -> TutorSummary:
    return await TutorService(db).get_my_profile(current_user)


@router.patch("/me", response_model=TutorSummary)
async def update_my_tutor_profile(
    data: TutorProfileUpdate,
    current_user: CurrentUser = Depends(require_roles(Role.tutor)),
    db: AsyncSession = Depends(get_db_session),
) -> TutorSummary:
    return await TutorService(db).update_my_profile(current_user, data)


@router.get("/{tutor_id}", response_model=TutorSummary)
async def get_tutor(
    tutor_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> TutorSummary:
    return await TutorService(db).get_tutor(tutor_id)
