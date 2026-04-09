from pydantic import BaseModel


class ProgressSummaryRead(BaseModel):
    total: int
    completed: int
    skipped: int
    pending: int
    completion_percent: int
