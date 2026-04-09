from pydantic import BaseModel


class PasteTextMaterialRequest(BaseModel):
    user_id: int
    study_plan_id: int | None = None
    text: str
    original_filename: str | None = None


class MaterialRead(BaseModel):
    id: int
    user_id: int
    study_plan_id: int | None = None
    material_type: str
    original_filename: str | None = None
    extracted_text: str | None = None
