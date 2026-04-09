from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from lms_backend.utils.datetime_utils import utcnow_naive


class Material(SQLModel, table=True):
    __tablename__ = "materials"
    __table_args__ = (
        Index("ix_materials_plan_created_at", "study_plan_id", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    study_plan_id: int | None = Field(default=None, foreign_key="study_plans.id", index=True)
    material_type: str
    original_filename: str | None = None
    mime_type: str | None = None
    file_path: str | None = None
    raw_text: str | None = None
    extracted_text: str | None = None
    created_at: str = Field(default_factory=lambda: utcnow_naive().isoformat())
