from pydantic import BaseModel, Field

from lms_backend.schemas.study_sessions import StudySessionRead


class StudyPlanCreateRequest(BaseModel):
    user_id: int
    exam_name: str = Field(min_length=1, max_length=255)
    days_available: int = Field(ge=1, le=365)
    hours_per_day: float = Field(gt=0, le=24)
    start_date: str
    generation_mode: str = "hybrid"


class StudyPlanRead(BaseModel):
    id: int
    user_id: int
    exam_name: str
    days_available: int
    hours_per_day: float
    start_date: str
    end_date: str
    status: str
    generation_mode: str


class StudyPlanDetail(StudyPlanRead):
    current_day_number: int | None = None
    sessions: list[StudySessionRead]


class GenerationResponse(BaseModel):
    study_plan_id: int
    sessions_count: int
    generation_mode: str
