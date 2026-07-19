from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import CurrentUser, Role, require_roles
from app.scheduling.schemas import (
    AvailabilityCheck,
    AvailabilityReplace,
    AvailabilityResult,
    AvailabilityWindowRead,
    BlockedTimeCreate,
    BlockedTimeRead,
)
from app.scheduling.service import SchedulingService


router = APIRouter()


@router.get("/availability/me", response_model=list[AvailabilityWindowRead])
async def my_availability(current_user: CurrentUser = Depends(require_roles(Role.tutor)), db: AsyncSession = Depends(get_db_session)):
    return await SchedulingService(db).get_my_availability(current_user)


@router.put("/availability/me", response_model=list[AvailabilityWindowRead])
async def replace_availability(data: AvailabilityReplace, current_user: CurrentUser = Depends(require_roles(Role.tutor)), db: AsyncSession = Depends(get_db_session)):
    return await SchedulingService(db).replace_my_availability(current_user, data)


@router.get("/blocks/me", response_model=list[BlockedTimeRead])
async def my_blocks(current_user: CurrentUser = Depends(require_roles(Role.tutor)), db: AsyncSession = Depends(get_db_session)):
    return await SchedulingService(db).list_my_blocks(current_user)


@router.post("/blocks/me", response_model=BlockedTimeRead, status_code=status.HTTP_201_CREATED)
async def add_block(data: BlockedTimeCreate, current_user: CurrentUser = Depends(require_roles(Role.tutor)), db: AsyncSession = Depends(get_db_session)):
    return await SchedulingService(db).add_block(current_user, data)


@router.delete("/blocks/me/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block(block_id: str, current_user: CurrentUser = Depends(require_roles(Role.tutor)), db: AsyncSession = Depends(get_db_session)):
    await SchedulingService(db).delete_block(current_user, block_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/availability/check", response_model=AvailabilityResult)
async def check_availability(data: AvailabilityCheck, db: AsyncSession = Depends(get_db_session)):
    return await SchedulingService(db).check(data.tutor_id, data.starts_at, data.ends_at)
