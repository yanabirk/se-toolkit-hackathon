from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from lms_backend.services.storage.paths import StoragePaths


async def save_upload_file(
    user_id: int, study_plan_id: int | None, uploaded_file: UploadFile
) -> Path:
    extension = Path(uploaded_file.filename or "upload.bin").suffix
    target = StoragePaths.materials_dir(user_id, study_plan_id) / f"{uuid4().hex}{extension}"
    content = await uploaded_file.read()
    target.write_bytes(content)
    return target
