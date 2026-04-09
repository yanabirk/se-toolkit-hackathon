from pathlib import Path

from fastapi import UploadFile

from lms_backend.models.material import Material
from lms_backend.services.materials.cleaner import clamp_text, clean_filename
from lms_backend.services.materials.docx_parser import parse_docx
from lms_backend.services.materials.image_ocr import parse_image
from lms_backend.services.materials.pdf_parser import parse_pdf
from lms_backend.services.materials.text_parser import parse_text
from lms_backend.services.storage.file_storage import save_upload_file
from lms_backend.utils.enums import MaterialType


def _detect_material_type(filename: str | None, content_type: str | None) -> str:
    filename = (filename or "").lower()
    content_type = (content_type or "").lower()
    if filename.endswith(".pdf") or content_type == "application/pdf":
        return MaterialType.PDF.value
    if filename.endswith(".docx"):
        return MaterialType.DOCX.value
    if content_type.startswith("image/"):
        return MaterialType.IMAGE.value
    return MaterialType.TEXT.value


async def ingest_upload(
    user_id: int,
    study_plan_id: int | None,
    uploaded_file: UploadFile,
) -> Material:
    path = await save_upload_file(user_id, study_plan_id, uploaded_file)
    original_filename = clean_filename(uploaded_file.filename)
    mime_type = clean_filename(uploaded_file.content_type)
    material_type = _detect_material_type(original_filename, mime_type)
    extracted_text = extract_text_from_path(path, material_type)
    return Material(
        user_id=user_id,
        study_plan_id=study_plan_id,
        material_type=material_type,
        original_filename=original_filename,
        mime_type=mime_type,
        file_path=str(path),
        extracted_text=clamp_text(extracted_text),
    )


async def ingest_text(
    user_id: int,
    study_plan_id: int | None,
    text: str,
    original_filename: str | None = None,
) -> Material:
    parsed = clamp_text(parse_text(text))
    return Material(
        user_id=user_id,
        study_plan_id=study_plan_id,
        material_type=MaterialType.TEXT.value,
        original_filename=clean_filename(original_filename),
        raw_text=clamp_text(text),
        extracted_text=parsed,
    )


def extract_text_from_path(path: Path, material_type: str) -> str:
    if material_type == MaterialType.PDF.value:
        return parse_pdf(path)
    if material_type == MaterialType.DOCX.value:
        return parse_docx(path)
    if material_type == MaterialType.IMAGE.value:
        return parse_image(path)
    return path.read_text(encoding="utf-8", errors="ignore")
