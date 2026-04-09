from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards import plan_actions_keyboard, session_detail_keyboard, session_list_keyboard
from bot.services.backend_client import BackendClient, BackendClientError
from bot.states import PlanStates
from bot.utils.formatters import (
    format_plan_overview,
    format_session_browser,
    format_session_detail,
)
from bot.utils.ui import ensure_reply_keyboard, render_screen

router = Router()
backend = BackendClient()


def _find_session(plan: dict, session_id: int) -> dict | None:
    for session in plan.get("sessions", []):
        if int(session.get("id", 0)) == session_id:
            return session
    return None


def _sessions_for_context(plan: dict, context: str) -> list[dict]:
    if context == "today":
        today_number = int(plan.get("current_day_number") or 1)
        return [s for s in plan.get("sessions", []) if int(s["day_number"]) == today_number]
    return list(plan.get("sessions", []))


async def _edit_callback_message(
    callback: CallbackQuery,
    text: str,
    *,
    state: FSMContext,
    reply_markup=None,
) -> None:
    await ensure_reply_keyboard(callback.message, state)
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=reply_markup)


async def _render_session_list(
    callback: CallbackQuery,
    *,
    plan: dict,
    context: str,
    state: FSMContext,
) -> None:
    sessions = _sessions_for_context(plan, context)
    await _edit_callback_message(
        callback,
        format_session_browser(plan, sessions, context=context),
        state=state,
        reply_markup=(
            session_list_keyboard(int(plan["id"]), sessions, context=context)
            if sessions
            else None
        ),
    )


async def _render_session_detail(
    callback: CallbackQuery,
    *,
    plan: dict,
    context: str,
    session_id: int,
    state: FSMContext,
) -> None:
    session = _find_session(plan, session_id)
    if session is None:
        await callback.answer("Session not found", show_alert=True)
        return
    await _edit_callback_message(
        callback,
        format_session_detail(plan, session, context=context),
        state=state,
        reply_markup=session_detail_keyboard(
            context=context,
            plan_id=int(plan["id"]),
            session_id=session_id,
            status=str(session.get("status", "pending")),
        ),
    )


async def _render_plan_overview(
    callback: CallbackQuery,
    *,
    plan_id: int,
    state: FSMContext,
) -> None:
    plan = await backend.get_plan(plan_id)
    progress = await backend.get_plan_progress(plan_id)
    materials = await backend.get_plan_materials(plan_id)
    await state.set_state(PlanStates.plan_actions)
    await state.update_data(selected_plan_id=plan_id)
    await render_screen(
        callback.message,
        state,
        format_plan_overview(plan, progress=progress, materials=materials),
        reply_markup=plan_actions_keyboard(),
        keyboard_key="plan_actions",
        force_new=True,
    )


@router.callback_query(F.data.startswith("session:"))
async def session_action(callback: CallbackQuery, state: FSMContext) -> None:
    parts = str(callback.data).split(":")

    if len(parts) == 3:
        _, action, raw_session_id = parts
        session_id = int(raw_session_id)
        try:
            if action == "complete":
                await backend.complete_session(session_id)
                status_text = "Completed"
            elif action == "skip":
                await backend.skip_session(session_id)
                status_text = "Skipped"
            else:
                status_text = "Updated"
            try:
                await callback.message.edit_text(
                    f"{callback.message.text}\n\nStatus: {status_text}"
                )
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass
            await callback.answer(status_text)
        except BackendClientError as exc:
            await callback.answer(f"Failed: {exc}", show_alert=True)
        return

    if len(parts) < 4:
        await callback.answer()
        return

    _, action, context, *rest = parts
    try:
        if action == "list":
            plan_id = int(rest[0])
            plan = await backend.get_plan(plan_id)
            await _render_session_list(callback, plan=plan, context=context, state=state)
            await callback.answer()
            return

        plan_id = int(rest[0])
        session_id = int(rest[1])

        if action == "complete":
            await backend.complete_session(session_id)
            plan = await backend.get_plan(plan_id)
            await _render_session_detail(
                callback,
                plan=plan,
                context=context,
                session_id=session_id,
                state=state,
            )
            await callback.answer("Marked as completed")
            return

        if action == "skip":
            await backend.skip_session(session_id)
            plan = await backend.get_plan(plan_id)
            await _render_session_detail(
                callback,
                plan=plan,
                context=context,
                session_id=session_id,
                state=state,
            )
            await callback.answer("Marked as skipped")
            return

        if action == "view":
            plan = await backend.get_plan(plan_id)
            await _render_session_detail(
                callback,
                plan=plan,
                context=context,
                session_id=session_id,
                state=state,
            )
            await callback.answer()
            return

        await callback.answer()
    except BackendClientError as exc:
        await callback.answer(f"Failed: {exc}", show_alert=True)


@router.callback_query(F.data.startswith("nav:plan:"))
async def open_parent_plan(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        plan_id = int(str(callback.data).split(":")[2])
        await _render_plan_overview(callback, plan_id=plan_id, state=state)
        await callback.answer()
    except (ValueError, IndexError):
        await callback.answer()
    except BackendClientError as exc:
        await callback.answer(f"Failed: {exc}", show_alert=True)
