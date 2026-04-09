from pydantic import BaseModel


class AnalyzeMaterialsResponse(BaseModel):
    study_plan_id: int
    extracted_topics: list[str]
