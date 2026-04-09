from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import MAIN_MENU_BUTTON, main_menu_keyboard
from bot.services.backend_client import BackendClient, BackendClientError
from bot.utils.ui import cleanup_user_message, clear_state_preserving_screen, render_screen

router = Router()
backend = BackendClient()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    await clear_state_preserving_screen(state)
    try:
        await backend.upsert_telegram_user(message.from_user)
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to contact backend: {exc}",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    await render_screen(
        message,
        state,
        "Study planner is ready.\n\nPick what you want to do next.",
        reply_markup=main_menu_keyboard(),
        keyboard_key="main",
        force_new=True,
    )
    await cleanup_user_message(message)


@router.message(F.text == MAIN_MENU_BUTTON)
async def main_menu_handler(message: Message, state: FSMContext) -> None:
    await clear_state_preserving_screen(state)
    await render_screen(
        message,
        state,
        "What would you like to do?",
        reply_markup=main_menu_keyboard(),
        keyboard_key="main",
        force_new=True,
    )
    await cleanup_user_message(message)
