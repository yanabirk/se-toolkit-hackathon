from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.llm_request import LlmRequest


async def create_llm_request(session: AsyncSession, row: LlmRequest) -> LlmRequest:
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
