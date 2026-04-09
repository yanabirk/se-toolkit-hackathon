from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.study_plans import (
    create_study_plan,
    delete_study_plan,
    get_study_plan,
    list_user_study_plans,
)
from lms_backend.db.study_sessions import list_sessions_for_plan
from lms_backend.db.users import get_user_by_id
from lms_backend.schemas.progress import ProgressSummaryRead
from lms_backend.schemas.study_plans import (
    StudyPlanCreateRequest,
    StudyPlanDetail,
    StudyPlanRead,
)
from lms_backend.schemas.study_sessions import StudySessionRead
from lms_backend.services.planner.progress_service import build_progress_summary

router = APIRouter()


def _resolve_current_day_number(start_date: str, days_available: int) -> int | None:
    try:
        start = datetime.fromisoformat(start_date).date()
    except ValueError:
        return None
    delta_days = (date.today() - start).days
    return min(max(1, delta_days + 1), days_available)


@router.post("", response_model=StudyPlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: StudyPlanCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> StudyPlanRead:
    user = await get_user_by_id(session, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    plan = await create_study_plan(session, payload)
    return StudyPlanRead.model_validate(plan, from_attributes=True)


@router.get("/{plan_id}", response_model=StudyPlanDetail)
async def read_plan(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> StudyPlanDetail:
    plan = await get_study_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    sessions = await list_sessions_for_plan(session, plan_id)
    return StudyPlanDetail(
        **plan.model_dump(),
        current_day_number=_resolve_current_day_number(plan.start_date, plan.days_available),
        sessions=[StudySessionRead.model_validate(item, from_attributes=True) for item in sessions],
    )


@router.get("/user/{user_id}", response_model=list[StudyPlanRead], include_in_schema=False)
async def list_plans(
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[StudyPlanRead]:
    plans = await list_user_study_plans(session, user_id)
    return [StudyPlanRead.model_validate(plan, from_attributes=True) for plan in plans]


@router.get("/{plan_id}/sessions", response_model=list[StudySessionRead])
async def read_plan_sessions(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[StudySessionRead]:
    plan = await get_study_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    sessions = await list_sessions_for_plan(session, plan_id)
    return [StudySessionRead.model_validate(item, from_attributes=True) for item in sessions]


@router.get("/{plan_id}/progress", response_model=ProgressSummaryRead)
async def get_plan_progress(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProgressSummaryRead:
    plan = await get_study_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    sessions = await list_sessions_for_plan(session, plan_id)
    return ProgressSummaryRead(**build_progress_summary(sessions))


@router.delete("/{plan_id}")
async def remove_plan(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    deleted = await delete_study_plan(session, plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return {"deleted": True}
