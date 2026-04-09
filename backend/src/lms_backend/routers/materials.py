from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.materials import create_material, list_materials_for_plan
from lms_backend.db.study_plans import get_study_plan
from lms_backend.db.users import get_user_by_id
from lms_backend.schemas.materials import MaterialRead, PasteTextMaterialRequest
from lms_backend.services.materials.ingestion import ingest_text, ingest_upload

router = APIRouter()


async def _validate_material_ownership(
    session: AsyncSession,
    user_id: int,
    study_plan_id: int | None,
) -> None:
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if study_plan_id is None:
        return
    plan = await get_study_plan(session, study_plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    if plan.user_id != user_id:
        raise HTTPException(status_code=400, detail="Study plan does not belong to the user")


@router.post("/upload", response_model=MaterialRead, status_code=201)
async def upload_material(
    user_id: int = Form(...),
    study_plan_id: int | None = Form(None),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> MaterialRead:
    await _validate_material_ownership(session, user_id, study_plan_id)
    material = await ingest_upload(user_id, study_plan_id, file)
    saved = await create_material(session, material)
    return MaterialRead.model_validate(saved, from_attributes=True)


@router.post("/paste-text", response_model=MaterialRead, status_code=201)
async def paste_text_material(
    payload: PasteTextMaterialRequest,
    session: AsyncSession = Depends(get_session),
) -> MaterialRead:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    await _validate_material_ownership(session, payload.user_id, payload.study_plan_id)
    material = await ingest_text(
        payload.user_id,
        payload.study_plan_id,
        payload.text,
        payload.original_filename,
    )
    saved = await create_material(session, material)
    return MaterialRead.model_validate(saved, from_attributes=True)


@router.get("/plan/{plan_id}", response_model=list[MaterialRead])
async def get_plan_materials(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[MaterialRead]:
    rows = await list_materials_for_plan(session, plan_id)
    return [MaterialRead.model_validate(row, from_attributes=True) for row in rows]
