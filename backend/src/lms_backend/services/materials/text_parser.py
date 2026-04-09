from lms_backend.utils.text_utils import clean_text


def parse_text(content: str) -> str:
    return clean_text(content)
