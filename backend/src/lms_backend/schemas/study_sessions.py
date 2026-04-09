from pydantic import BaseModel


class StudySessionRead(BaseModel):
    id: int
    study_plan_id: int
    day_number: int
    session_order: int
    title: str
    description: str
    duration_minutes: int
    session_type: str
    status: str
    source: str


class SessionStatusUpdateResponse(BaseModel):
    id: int
    status: str
