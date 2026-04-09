from datetime import date, datetime

from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.llm_request import LlmRequest
from lms_backend.models.material import Material
from lms_backend.models.plan_topic import PlanTopic
from lms_backend.models.study_plan import StudyPlan
from lms_backend.models.study_session import StudySession
from lms_backend.schemas.study_plans import StudyPlanCreateRequest
from lms_backend.utils.datetime_utils import calculate_end_date, utcnow_naive
from lms_backend.utils.enums import StudyPlanStatus


async def create_study_plan(
    session: AsyncSession, payload: StudyPlanCreateRequest
) -> StudyPlan:
    start_date = payload.start_date
    start_date_obj = datetime.fromisoformat(payload.start_date)
    end_date = calculate_end_date(start_date_obj, payload.days_available).date().isoformat()
    plan = StudyPlan(
        user_id=payload.user_id,
        exam_name=payload.exam_name,
        days_available=payload.days_available,
        hours_per_day=payload.hours_per_day,
        start_date=start_date,
        end_date=end_date,
        status=StudyPlanStatus.DRAFT.value,
        generation_mode=payload.generation_mode,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def get_study_plan(session: AsyncSession, plan_id: int) -> StudyPlan | None:
    return await session.get(StudyPlan, plan_id)


async def list_user_study_plans(session: AsyncSession, user_id: int) -> list[StudyPlan]:
    statement = (
        select(StudyPlan)
        .where(StudyPlan.user_id == user_id)
        .order_by(StudyPlan.created_at.desc())
    )
    return list((await session.exec(statement)).all())


async def activate_study_plan(session: AsyncSession, plan: StudyPlan) -> StudyPlan:
    plan.status = StudyPlanStatus.ACTIVE.value
    plan.updated_at = utcnow_naive().isoformat()
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def delete_study_plan(session: AsyncSession, plan_id: int) -> bool:
    plan = await session.get(StudyPlan, plan_id)
    if plan is None:
        return False
    await session.exec(delete(StudySession).where(StudySession.study_plan_id == plan_id))
    await session.exec(delete(Material).where(Material.study_plan_id == plan_id))
    await session.exec(delete(PlanTopic).where(PlanTopic.study_plan_id == plan_id))
    await session.exec(delete(LlmRequest).where(LlmRequest.study_plan_id == plan_id))
    await session.delete(plan)
    await session.commit()
    return True
