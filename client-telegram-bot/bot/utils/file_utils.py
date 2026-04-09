from pathlib import Path

from aiogram.types import Document, Message, PhotoSize


async def download_telegram_file(message: Message, destination: Path) -> Path:
    await message.bot.download(message.document or message.photo[-1], destination)
    return destination


def detect_file_name(message: Message) -> str:
    if message.document is not None:
        return message.document.file_name or "upload.bin"
    if message.photo:
        return "image.jpg"
    return "upload.bin"
