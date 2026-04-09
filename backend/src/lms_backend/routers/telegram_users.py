from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.users import upsert_telegram_user
from lms_backend.schemas.users import TelegramUserUpsertRequest, UserRead

router = APIRouter()


@router.post('/upsert', response_model=UserRead)
async def upsert_user(
    payload: TelegramUserUpsertRequest,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    user = await upsert_telegram_user(session, payload)
    return UserRead.model_validate(user, from_attributes=True)
