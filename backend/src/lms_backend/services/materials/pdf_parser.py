from pathlib import Path

from pypdf import PdfReader

from lms_backend.utils.text_utils import clean_text


def parse_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    text_parts: list[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return clean_text("\n".join(text_parts))
