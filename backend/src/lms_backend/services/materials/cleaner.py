from lms_backend.settings import settings
from lms_backend.utils.text_utils import clean_text, strip_invalid_text_chars


def clamp_text(text: str) -> str:
    return clean_text(text)[: settings.max_material_chars]


def clean_filename(filename: str | None) -> str | None:
    if filename is None:
        return None
    cleaned = strip_invalid_text_chars(filename).strip()
    return cleaned or "upload.bin"
