from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.study_plans import get_study_plan
from lms_backend.services.planner.plan_generator import (
    analyze_materials_and_topics,
    generate_plan,
)

router = APIRouter()


@router.post("/{plan_id}/generate")
async def generate_study_plan(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    plan = await get_study_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    generated_sessions = await generate_plan(session, plan)
    return {
        "study_plan_id": plan_id,
        "sessions_count": len(generated_sessions),
        "generation_mode": plan.generation_mode,
    }


@router.post("/{plan_id}/analyze-materials")
async def analyze_materials(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    plan = await get_study_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    topics = await analyze_materials_and_topics(session, plan)
    return {"study_plan_id": plan_id, "extracted_topics": topics}


@router.post("/{plan_id}/regenerate")
async def regenerate_study_plan(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    plan = await get_study_plan(session, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    generated_sessions = await generate_plan(session, plan)
    return {
        "study_plan_id": plan_id,
        "sessions_count": len(generated_sessions),
        "generation_mode": plan.generation_mode,
    }
