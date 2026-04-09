from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from bot.services.backend_client import BackendClient, BackendClientError

router = Router()
backend = BackendClient()


@router.callback_query(F.data.startswith('session:'))
async def session_action(callback: CallbackQuery) -> None:
    _, action, raw_session_id = str(callback.data).split(':', 2)
    session_id = int(raw_session_id)
    try:
        if action == 'complete':
            await backend.complete_session(session_id)
            status_text = "Completed"
        elif action == 'skip':
            await backend.skip_session(session_id)
            status_text = "Skipped"
        else:
            status_text = "Updated"
        try:
            await callback.message.edit_text(f"{callback.message.text}\n\nStatus: {status_text}")
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.answer(status_text)
    except BackendClientError as exc:
        await callback.answer(f"Failed: {exc}", show_alert=True)
