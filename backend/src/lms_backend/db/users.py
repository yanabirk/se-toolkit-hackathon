from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.user import User
from lms_backend.schemas.users import TelegramUserUpsertRequest
from lms_backend.utils.datetime_utils import utcnow_naive


async def upsert_telegram_user(
    session: AsyncSession, payload: TelegramUserUpsertRequest
) -> User:
    statement = select(User).where(User.telegram_user_id == payload.telegram_user_id)
    user = (await session.exec(statement)).first()
    if user is None:
        user = User(
            telegram_user_id=payload.telegram_user_id,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        session.add(user)
    else:
        user.username = payload.username
        user.first_name = payload.first_name
        user.last_name = payload.last_name
        user.updated_at = utcnow_naive().isoformat()
        session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)
