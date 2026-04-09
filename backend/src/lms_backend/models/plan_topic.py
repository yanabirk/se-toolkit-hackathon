from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from lms_backend.utils.datetime_utils import utcnow_naive


class PlanTopic(SQLModel, table=True):
    __tablename__ = "plan_topics"
    __table_args__ = (
        Index("ix_plan_topics_plan_priority", "study_plan_id", "priority"),
    )

    id: int | None = Field(default=None, primary_key=True)
    study_plan_id: int = Field(foreign_key="study_plans.id", index=True)
    topic_name: str
    priority: int = 1
    estimated_weight: float = 1.0
    source: str = "manual"
    created_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
