from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from lms_backend.utils.datetime_utils import utcnow_naive


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_telegram_user_id_created_at", "telegram_user_id", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True, unique=True)
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
    updated_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
