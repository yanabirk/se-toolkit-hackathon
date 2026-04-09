from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.plan_topic import PlanTopic


async def replace_plan_topics(
    session: AsyncSession, study_plan_id: int, topics: list[str], source: str
) -> list[PlanTopic]:
    await session.exec(delete(PlanTopic).where(PlanTopic.study_plan_id == study_plan_id))
    rows: list[PlanTopic] = []
    for index, topic in enumerate(topics, start=1):
        row = PlanTopic(
            study_plan_id=study_plan_id,
            topic_name=topic,
            priority=index,
            estimated_weight=1.0,
            source=source,
        )
        session.add(row)
        rows.append(row)
    await session.commit()
    for row in rows:
        await session.refresh(row)
    return rows


async def list_plan_topics(session: AsyncSession, study_plan_id: int) -> list[PlanTopic]:
    statement = select(PlanTopic).where(PlanTopic.study_plan_id == study_plan_id)
    return list((await session.exec(statement)).all())
