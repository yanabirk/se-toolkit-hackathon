from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.material import Material


async def create_material(session: AsyncSession, material: Material) -> Material:
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return material


async def list_materials_for_plan(
    session: AsyncSession, study_plan_id: int
) -> list[Material]:
    statement = (
        select(Material)
        .where(Material.study_plan_id == study_plan_id)
        .order_by(Material.created_at.desc())
    )
    return list((await session.exec(statement)).all())
