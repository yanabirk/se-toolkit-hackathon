from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.study_plans import list_user_study_plans
from lms_backend.schemas.study_plans import StudyPlanRead

router = APIRouter()


@router.get("/{user_id}/study-plans", response_model=list[StudyPlanRead])
async def list_user_plans(
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[StudyPlanRead]:
    plans = await list_user_study_plans(session, user_id)
    return [StudyPlanRead.model_validate(plan, from_attributes=True) for plan in plans]
