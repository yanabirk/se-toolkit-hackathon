from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import Message

from bot.keyboards import PROGRESS_BUTTON, main_menu_keyboard
from bot.services.backend_client import BackendClient, BackendClientError
from bot.utils.ui import cleanup_user_message, render_screen

router = Router()
backend = BackendClient()


async def _show_progress(message: Message, state: FSMContext, tg_user: object | None) -> None:
    if tg_user is None:
        return
    try:
        user = await backend.upsert_telegram_user(tg_user)
        plans = await backend.get_user_plans(user["id"])
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to load progress: {exc}",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        return
    if not plans:
        await render_screen(
            message,
            state,
            "No plans yet.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        return

    latest = plans[0]
    try:
        progress = await backend.get_plan_progress(latest["id"])
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to load progress: {exc}",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        return
    await render_screen(
        message,
        state,
        "\n".join(
            [
                f"Progress for: {latest['exam_name']}",
                f"Completed: {progress['completed']}/{progress['total']} ({progress['completion_percent']}%)",
                f"Pending: {progress['pending']}",
                f"Skipped: {progress['skipped']}",
            ]
        ),
        reply_markup=main_menu_keyboard(),
        keyboard_key="main",
        force_new=True,
    )


@router.callback_query(F.data == "menu:progress")
async def progress_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await _show_progress(callback.message, state, callback.from_user)
    await callback.answer()


@router.message(Command("progress"))
@router.message(F.text == PROGRESS_BUTTON)
async def progress_command(message: Message, state: FSMContext) -> None:
    await _show_progress(message, state, message.from_user)
    await cleanup_user_message(message)
