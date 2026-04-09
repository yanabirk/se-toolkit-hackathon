from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import Message

from bot.keyboards import TODAY_BUTTON, main_menu_keyboard, session_list_keyboard
from bot.services.backend_client import BackendClient
from bot.services.backend_client import BackendClientError
from bot.utils.formatters import format_session_browser
from bot.utils.ui import cleanup_user_message, ensure_reply_keyboard, render_screen

router = Router()
backend = BackendClient()


async def _show_today(message: Message, state: FSMContext, tg_user: object | None) -> None:
    if tg_user is None:
        return
    try:
        user = await backend.upsert_telegram_user(tg_user)
        plans = await backend.get_user_plans(user["id"])
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to load today's plan: {exc}",
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
        plan = await backend.get_plan(latest["id"])
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to load today's plan: {exc}",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        return
    today_number = int(plan.get("current_day_number") or 1)
    today_sessions = [s for s in plan["sessions"] if s["day_number"] == today_number]
    if not today_sessions:
        text = "📅 Nothing is scheduled for today yet."
        markup = None
    else:
        text = format_session_browser(plan, today_sessions, context="today")
        markup = session_list_keyboard(int(plan["id"]), today_sessions, context="today")
    await ensure_reply_keyboard(message, state)
    await render_screen(
        message,
        state,
        text,
        reply_markup=markup,
        keyboard_key=f"today_sessions:{latest['id']}",
        force_new=True,
    )


@router.callback_query(F.data == "menu:today")
async def today_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await _show_today(callback.message, state, callback.from_user)
    await callback.answer()


@router.message(Command("today"))
@router.message(F.text == TODAY_BUTTON)
async def today_command(message: Message, state: FSMContext) -> None:
    await _show_today(message, state, message.from_user)
    await cleanup_user_message(message)
