from pathlib import Path

from docx import Document

from lms_backend.utils.text_utils import clean_text


def parse_docx(path: Path) -> str:
    document = Document(str(path))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return clean_text(text)
