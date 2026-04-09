from typing import Any

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

from lms_backend.utils.datetime_utils import utcnow_naive


class LlmRequest(SQLModel, table=True):
    __tablename__ = "llm_requests"
    __table_args__ = (
        Index("ix_llm_requests_study_plan_created_at", "study_plan_id", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    study_plan_id: int | None = Field(default=None, foreign_key="study_plans.id", index=True)
    provider: str
    model: str
    prompt_version: str = "v1"
    request_payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    response_payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    status: str
    created_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
