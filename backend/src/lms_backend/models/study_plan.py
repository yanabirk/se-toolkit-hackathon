from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from lms_backend.utils.datetime_utils import utcnow_naive
from lms_backend.utils.enums import GenerationMode, StudyPlanStatus


class StudyPlan(SQLModel, table=True):
    __tablename__ = "study_plans"
    __table_args__ = (
        Index("ix_study_plans_user_created_at", "user_id", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    exam_name: str
    days_available: int
    hours_per_day: float
    start_date: str
    end_date: str
    status: str = Field(default=StudyPlanStatus.DRAFT.value)
    generation_mode: str = Field(default=GenerationMode.HYBRID.value)
    created_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
    updated_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
