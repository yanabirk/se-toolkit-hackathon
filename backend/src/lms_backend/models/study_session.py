from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from lms_backend.utils.datetime_utils import utcnow_naive
from lms_backend.utils.enums import SessionSource, SessionStatus, SessionType


class StudySession(SQLModel, table=True):
    __tablename__ = "study_sessions"
    __table_args__ = (
        Index("ix_study_sessions_plan_day_order", "study_plan_id", "day_number", "session_order"),
    )

    id: int | None = Field(default=None, primary_key=True)
    study_plan_id: int = Field(foreign_key="study_plans.id", index=True)
    day_number: int
    session_order: int
    title: str
    description: str = ""
    duration_minutes: int
    session_type: str = Field(default=SessionType.STUDY.value)
    status: str = Field(default=SessionStatus.PENDING.value)
    source: str = Field(default=SessionSource.SYSTEM.value)
    completed_at: str | None = None
    created_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
    updated_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
