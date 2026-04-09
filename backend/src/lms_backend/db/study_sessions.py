from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.study_session import StudySession
from lms_backend.utils.datetime_utils import utcnow_naive
from lms_backend.utils.enums import SessionStatus


async def replace_sessions(
    session: AsyncSession, plan_id: int, sessions_payload: list[dict[str, object]]
) -> list[StudySession]:
    existing_rows = await list_sessions_for_plan(session, plan_id)
    existing_by_slot = {
        (row.day_number, row.session_order): row
        for row in existing_rows
    }
    payload_slots = {
        (int(payload["day_number"]), int(payload["session_order"]))
        for payload in sessions_payload
    }
    created: list[StudySession] = []
    for payload in sessions_payload:
        slot = (int(payload["day_number"]), int(payload["session_order"]))
        row = existing_by_slot.get(slot)
        if row is None:
            row = StudySession(study_plan_id=plan_id, **payload)
            session.add(row)
            created.append(row)
            continue
        row.title = str(payload["title"])
        row.description = str(payload.get("description", ""))
        row.duration_minutes = int(payload["duration_minutes"])
        row.session_type = str(payload.get("session_type", row.session_type))
        row.source = str(payload.get("source", row.source))
        row.updated_at = utcnow_naive().isoformat()
        session.add(row)
        created.append(row)
    for row in existing_rows:
        slot = (row.day_number, row.session_order)
        if slot not in payload_slots:
            await session.delete(row)
    await session.commit()
    for row in created:
        await session.refresh(row)
    return created


async def list_sessions_for_plan(
    session: AsyncSession, plan_id: int
) -> list[StudySession]:
    statement = (
        select(StudySession)
        .where(StudySession.study_plan_id == plan_id)
        .order_by(StudySession.day_number, StudySession.session_order)
    )
    return list((await session.exec(statement)).all())


async def update_session_status(
    session: AsyncSession, session_id: int, status: str
) -> StudySession | None:
    study_session = await session.get(StudySession, session_id)
    if study_session is None:
        return None
    study_session.status = status
    study_session.updated_at = utcnow_naive().isoformat()
    if status == SessionStatus.COMPLETED.value:
        study_session.completed_at = utcnow_naive().isoformat()
    else:
        study_session.completed_at = None
    session.add(study_session)
    await session.commit()
    await session.refresh(study_session)
    return study_session
