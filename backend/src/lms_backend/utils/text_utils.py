def strip_invalid_text_chars(text: str) -> str:
    return "".join(
        char
        for char in text.replace("\x00", "")
        if char == "\n" or char == "\t" or ord(char) >= 32
    )


def clean_text(text: str) -> str:
    sanitized = strip_invalid_text_chars(text).replace("\r", "")
    lines = [line.strip() for line in sanitized.split("\n")]
    compact = "\n".join(line for line in lines if line)
    return compact.strip()
