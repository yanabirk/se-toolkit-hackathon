from pathlib import Path
from tempfile import gettempdir

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    BACK_TO_PLANS_BUTTON,
    CANCEL_DELETE_BUTTON,
    CANCEL_UPLOAD_BUTTON,
    COMPLETE_NEXT_BUTTON,
    CONFIRM_DELETE_BUTTON,
    DELETE_PLAN_BUTTON,
    MAIN_MENU_BUTTON,
    MY_PLANS_BUTTON,
    REGENERATE_PLAN_BUTTON,
    UPLOAD_MATERIALS_BUTTON,
    VIEW_PLAN_BUTTON,
    delete_plan_keyboard,
    extract_plan_id,
    main_menu_keyboard,
    plan_actions_keyboard,
    plans_menu_keyboard,
    session_list_keyboard,
    upload_material_keyboard,
)
from bot.services.backend_client import BackendClient, BackendClientError
from bot.states import PlanStates
from bot.utils.file_utils import detect_file_name, download_telegram_file
from bot.utils.formatters import (
    format_plan_overview,
    format_plans_list,
    format_session_browser,
)
from bot.utils.ui import cleanup_user_message, clear_state_preserving_screen, render_screen

router = Router()
backend = BackendClient()


async def _load_current_user(tg_user: object | None) -> dict | None:
    if tg_user is None:
        return None
    return await backend.upsert_telegram_user(tg_user)


async def _show_plan_selector(
    message: Message,
    state: FSMContext,
    tg_user: object | None,
) -> None:
    try:
        user = await _load_current_user(tg_user)
        if user is None:
            return
        plans = await backend.get_user_plans(user["id"])
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to load plans: {exc}",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        return

    await clear_state_preserving_screen(state)
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

    await state.set_state(PlanStates.waiting_plan_selection)
    await render_screen(
        message,
        state,
        format_plans_list(plans),
        reply_markup=plans_menu_keyboard(plans),
        keyboard_key="plans",
        force_new=True,
    )


async def _open_plan(
    message: Message,
    state: FSMContext,
    plan_id: int,
    *,
    notice: str | None = None,
) -> None:
    try:
        plan = await backend.get_plan(plan_id)
        progress = await backend.get_plan_progress(plan_id)
        materials = await backend.get_plan_materials(plan_id)
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to open plan: {exc}",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        return

    await state.set_state(PlanStates.plan_actions)
    await state.update_data(selected_plan_id=plan_id)
    text = format_plan_overview(plan, progress=progress, materials=materials)
    if notice:
        text = f"{notice}\n\n{text}"
    await render_screen(
        message,
        state,
        text,
        reply_markup=plan_actions_keyboard(),
        keyboard_key="plan_actions",
    )


async def _show_plan_sessions(
    message: Message,
    state: FSMContext,
    plan_id: int,
) -> None:
    try:
        plan = await backend.get_plan(plan_id)
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Couldn't load sessions: {exc}",
            reply_markup=plan_actions_keyboard(),
            keyboard_key="plan_actions",
        )
        return

    sessions = list(plan.get("sessions", []))
    await state.set_state(PlanStates.plan_actions)
    await state.update_data(selected_plan_id=plan_id)
    await render_screen(
        message,
        state,
        format_session_browser(plan, sessions, context="plan"),
        reply_markup=(
            session_list_keyboard(plan_id, sessions, context="plan")
            if sessions
            else None
        ),
        keyboard_key=f"plan_sessions:{plan_id}",
        force_new=True,
    )


def _find_next_pending_session(plan: dict) -> dict | None:
    for session in plan.get("sessions", []):
        if session.get("status") == "pending":
            return session
    return None


async def _selected_plan_id(state: FSMContext) -> int | None:
    data = await state.get_data()
    value = data.get("selected_plan_id")
    if isinstance(value, int):
        return value
    return None


@router.callback_query(F.data == "menu:my_plans")
async def my_plans_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await _show_plan_selector(callback.message, state, callback.from_user)
    await callback.answer()


@router.message(Command("myplans"))
@router.message(F.text == MY_PLANS_BUTTON)
async def my_plans_command(message: Message, state: FSMContext) -> None:
    await _show_plan_selector(message, state, message.from_user)
    await cleanup_user_message(message)


@router.message(PlanStates.waiting_plan_selection, F.text == MAIN_MENU_BUTTON)
@router.message(PlanStates.plan_actions, F.text == MAIN_MENU_BUTTON)
@router.message(PlanStates.waiting_material_upload, F.text == MAIN_MENU_BUTTON)
@router.message(PlanStates.waiting_delete_confirmation, F.text == MAIN_MENU_BUTTON)
async def back_to_main_menu(message: Message, state: FSMContext) -> None:
    await clear_state_preserving_screen(state)
    await render_screen(
        message,
        state,
        "Main menu.",
        reply_markup=main_menu_keyboard(),
        keyboard_key="main",
        force_new=True,
    )
    await cleanup_user_message(message)


@router.message(PlanStates.waiting_plan_selection)
async def choose_plan(message: Message, state: FSMContext) -> None:
    plan_id = extract_plan_id(message.text)
    if plan_id is None:
        await render_screen(
            message,
            state,
            "Choose a plan using the keyboard below.",
            keyboard_key="plans",
        )
        await cleanup_user_message(message)
        return
    await _open_plan(message, state, plan_id)
    await cleanup_user_message(message)


@router.message(PlanStates.plan_actions, F.text == BACK_TO_PLANS_BUTTON)
@router.message(PlanStates.waiting_material_upload, F.text == BACK_TO_PLANS_BUTTON)
@router.message(PlanStates.waiting_delete_confirmation, F.text == BACK_TO_PLANS_BUTTON)
async def back_to_plan_list(message: Message, state: FSMContext) -> None:
    await _show_plan_selector(message, state, message.from_user)
    await cleanup_user_message(message)


@router.message(PlanStates.plan_actions, F.text == VIEW_PLAN_BUTTON)
async def view_plan(message: Message, state: FSMContext) -> None:
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await render_screen(
            message,
            state,
            "Open a plan first.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    await _show_plan_sessions(message, state, plan_id)
    await cleanup_user_message(message)


@router.message(PlanStates.plan_actions, F.text == COMPLETE_NEXT_BUTTON)
async def complete_next_session(message: Message, state: FSMContext) -> None:
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await render_screen(
            message,
            state,
            "Open a plan first.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    try:
        plan = await backend.get_plan(plan_id)
        next_session = _find_next_pending_session(plan)
        if next_session is None:
            await render_screen(
                message,
                state,
                "All sessions are already completed or skipped.",
                reply_markup=plan_actions_keyboard(),
                keyboard_key="plan_actions",
            )
            await cleanup_user_message(message)
            return
        await backend.complete_session(int(next_session["id"]))
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to update progress: {exc}",
            reply_markup=plan_actions_keyboard(),
            keyboard_key="plan_actions",
        )
        await cleanup_user_message(message)
        return
    await _open_plan(message, state, plan_id, notice="Next session marked as completed.")
    await cleanup_user_message(message)


@router.message(PlanStates.plan_actions, F.text == REGENERATE_PLAN_BUTTON)
async def regenerate_plan(message: Message, state: FSMContext) -> None:
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await render_screen(
            message,
            state,
            "Open a plan first.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    try:
        await backend.regenerate_study_plan(plan_id)
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to regenerate plan: {exc}",
            reply_markup=plan_actions_keyboard(),
            keyboard_key="plan_actions",
        )
        await cleanup_user_message(message)
        return
    await _open_plan(
        message,
        state,
        plan_id,
        notice="Plan regenerated. Completed sessions were kept where possible.",
    )
    await cleanup_user_message(message)


@router.message(PlanStates.plan_actions, F.text == UPLOAD_MATERIALS_BUTTON)
async def start_material_upload(message: Message, state: FSMContext) -> None:
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await render_screen(
            message,
            state,
            "Open a plan first.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    await state.set_state(PlanStates.waiting_material_upload)
    await state.update_data(selected_plan_id=plan_id)
    await render_screen(
        message,
        state,
        "Send plain text, a PDF, a DOCX, or an image for this plan.",
        reply_markup=upload_material_keyboard(),
        keyboard_key="upload",
        force_new=True,
    )
    await cleanup_user_message(message)


@router.message(PlanStates.waiting_material_upload, F.text == CANCEL_UPLOAD_BUTTON)
async def cancel_material_upload(message: Message, state: FSMContext) -> None:
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await clear_state_preserving_screen(state)
        await render_screen(
            message,
            state,
            "Upload cancelled.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    await state.set_state(PlanStates.plan_actions)
    await render_screen(
        message,
        state,
        "Upload cancelled.",
        reply_markup=plan_actions_keyboard(),
        keyboard_key="plan_actions",
        force_new=True,
    )
    await cleanup_user_message(message)


@router.message(PlanStates.waiting_material_upload)
async def upload_material_to_selected_plan(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await clear_state_preserving_screen(state)
        await render_screen(
            message,
            state,
            "Open a plan first.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return

    temp_path: Path | None = None
    try:
        user = await _load_current_user(message.from_user)
        if user is None:
            return
        if message.text:
            await backend.upload_text_material(
                {
                    "user_id": user["id"],
                    "study_plan_id": plan_id,
                    "text": message.text,
                }
            )
        elif message.document or message.photo:
            temp_path = Path(gettempdir()) / detect_file_name(message)
            await download_telegram_file(message, temp_path)
            await backend.upload_file_material(user["id"], plan_id, temp_path, temp_path.name)
        else:
            await render_screen(
                message,
                state,
                "Send text, PDF, DOCX, or image.",
                reply_markup=upload_material_keyboard(),
                keyboard_key="upload",
            )
            await cleanup_user_message(message)
            return
        await backend.regenerate_study_plan(plan_id)
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to upload material: {exc}",
            reply_markup=upload_material_keyboard(),
            keyboard_key="upload",
        )
        await cleanup_user_message(message)
        return
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)

    await _open_plan(message, state, plan_id, notice="Material added and plan regenerated.")
    await cleanup_user_message(message)


@router.message(PlanStates.plan_actions, F.text == DELETE_PLAN_BUTTON)
async def ask_delete_confirmation(message: Message, state: FSMContext) -> None:
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await render_screen(
            message,
            state,
            "Open a plan first.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    await state.set_state(PlanStates.waiting_delete_confirmation)
    await state.update_data(selected_plan_id=plan_id)
    await render_screen(
        message,
        state,
        "Delete this plan? This will also remove its sessions and materials.",
        reply_markup=delete_plan_keyboard(),
        keyboard_key="delete_confirm",
        force_new=True,
    )
    await cleanup_user_message(message)


@router.message(PlanStates.waiting_delete_confirmation, F.text == CANCEL_DELETE_BUTTON)
async def cancel_delete(message: Message, state: FSMContext) -> None:
    await state.set_state(PlanStates.plan_actions)
    await render_screen(
        message,
        state,
        "Plan was kept.",
        reply_markup=plan_actions_keyboard(),
        keyboard_key="plan_actions",
        force_new=True,
    )
    await cleanup_user_message(message)


@router.message(PlanStates.waiting_delete_confirmation, F.text == CONFIRM_DELETE_BUTTON)
async def confirm_delete(message: Message, state: FSMContext) -> None:
    plan_id = await _selected_plan_id(state)
    if plan_id is None:
        await clear_state_preserving_screen(state)
        await render_screen(
            message,
            state,
            "Open a plan first.",
            reply_markup=main_menu_keyboard(),
            keyboard_key="main",
            force_new=True,
        )
        await cleanup_user_message(message)
        return
    try:
        await backend.delete_study_plan(plan_id)
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to delete plan: {exc}",
            reply_markup=delete_plan_keyboard(),
            keyboard_key="delete_confirm",
        )
        await cleanup_user_message(message)
        return
    await clear_state_preserving_screen(state)
    await render_screen(
        message,
        state,
        "Plan deleted.",
        reply_markup=main_menu_keyboard(),
        keyboard_key="main",
        force_new=True,
    )
    await cleanup_user_message(message)
