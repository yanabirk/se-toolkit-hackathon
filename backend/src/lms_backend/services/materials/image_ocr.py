from pathlib import Path

from lms_backend.utils.text_utils import clean_text


def parse_image(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return "Image OCR is not configured on this server."

    text = pytesseract.image_to_string(Image.open(path))
    return clean_text(text)
