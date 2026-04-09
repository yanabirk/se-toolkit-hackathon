from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.study_sessions import list_sessions_for_plan, update_session_status
from lms_backend.schemas.study_sessions import SessionStatusUpdateResponse, StudySessionRead
from lms_backend.utils.enums import SessionStatus

router = APIRouter()


@router.get('/plan/{plan_id}', response_model=list[StudySessionRead])
async def get_plan_sessions(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[StudySessionRead]:
    rows = await list_sessions_for_plan(session, plan_id)
    return [StudySessionRead.model_validate(row, from_attributes=True) for row in rows]


@router.patch('/{session_id}/complete', response_model=SessionStatusUpdateResponse)
async def complete_session(
    session_id: int,
    session: AsyncSession = Depends(get_session),
) -> SessionStatusUpdateResponse:
    row = await update_session_status(session, session_id, SessionStatus.COMPLETED.value)
    if row is None:
        raise HTTPException(status_code=404, detail='Study session not found')
    return SessionStatusUpdateResponse(id=row.id or 0, status=row.status)


@router.patch('/{session_id}/skip', response_model=SessionStatusUpdateResponse)
async def skip_session(
    session_id: int,
    session: AsyncSession = Depends(get_session),
) -> SessionStatusUpdateResponse:
    row = await update_session_status(session, session_id, SessionStatus.SKIPPED.value)
    if row is None:
        raise HTTPException(status_code=404, detail='Study session not found')
    return SessionStatusUpdateResponse(id=row.id or 0, status=row.status)
