from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import NEW_PLAN_BUTTON, new_plan_keyboard, plan_actions_keyboard
from bot.services.backend_client import BackendClient, BackendClientError
from bot.states import NewPlanStates, PlanStates
from bot.utils.formatters import format_plan_overview
from bot.utils.ui import cleanup_user_message, render_screen

router = Router()
backend = BackendClient()


def _parse_optional_answer(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if text.lower() in {"no", "none", "skip", "-", "нет", "не знаю"}:
        return None
    return text


def _parse_positive_int(value: str | None) -> int | None:
    try:
        parsed = int((value or '').strip())
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _parse_positive_float(value: str | None) -> float | None:
    try:
        parsed = float((value or '').strip().replace(',', '.'))
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _normalize_preferred_mode(value: str | None) -> str:
    text = (value or "").strip().lower()
    if text in {"practice", "tasks", "problems", "practice-heavy", "практика"}:
        return "practice"
    if text in {"theory", "concepts", "theory-heavy", "теория"}:
        return "theory"
    if text in {"balanced", "mix", "mixed", "сбалансированно", "баланс"}:
        return "balanced"
    return "balanced"


def _build_plan_brief(exam_name: str, weak_topics: str | None, preferred_mode: str) -> str:
    lines = [
        "Student context for study plan generation.",
        f"Exam: {exam_name}",
    ]
    if weak_topics:
        lines.append(f"Weak topics: {weak_topics}")
        lines.append(f"Priority topics: {weak_topics}")
    lines.append(f"Preferred mode: {preferred_mode}")
    if preferred_mode == "practice":
        lines.append("Need more practice and problem-solving sessions.")
    elif preferred_mode == "theory":
        lines.append("Need stronger theory explanations and concept review.")
    else:
        lines.append("Need a balanced mix of theory, revision, and practice.")
    return "\n".join(lines)


async def _start_new_plan(state: FSMContext, message: Message) -> None:
    await state.set_state(NewPlanStates.waiting_exam_name)
    await render_screen(
        message,
        state,
        "Send exam or course name.",
        reply_markup=new_plan_keyboard(),
        keyboard_key="new_plan",
        force_new=True,
    )


@router.callback_query(F.data == "menu:new_plan")
async def new_plan_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await _start_new_plan(state, callback.message)
    await callback.answer()


@router.message(Command("newplan"))
@router.message(F.text == NEW_PLAN_BUTTON)
async def new_plan_command(message: Message, state: FSMContext) -> None:
    await _start_new_plan(state, message)
    await cleanup_user_message(message)


@router.message(NewPlanStates.waiting_exam_name)
async def receive_exam_name(message: Message, state: FSMContext) -> None:
    exam_name = (message.text or '').strip()
    if not exam_name:
        await render_screen(
            message,
            state,
            "Exam name cannot be empty. Send it again.",
            reply_markup=new_plan_keyboard(),
            keyboard_key="new_plan",
        )
        await cleanup_user_message(message)
        return
    await state.update_data(exam_name=exam_name)
    await state.set_state(NewPlanStates.waiting_days_available)
    await render_screen(
        message,
        state,
        "How many days are left? Send a positive number.",
        reply_markup=new_plan_keyboard(),
        keyboard_key="new_plan",
    )
    await cleanup_user_message(message)


@router.message(NewPlanStates.waiting_days_available)
async def receive_days(message: Message, state: FSMContext) -> None:
    days = _parse_positive_int(message.text)
    if days is None:
        await render_screen(
            message,
            state,
            "Send a valid positive integer for days left.",
            reply_markup=new_plan_keyboard(),
            keyboard_key="new_plan",
        )
        await cleanup_user_message(message)
        return
    await state.update_data(days_available=days)
    await state.set_state(NewPlanStates.waiting_hours_per_day)
    await render_screen(
        message,
        state,
        "How many hours per day can you study?",
        reply_markup=new_plan_keyboard(),
        keyboard_key="new_plan",
    )
    await cleanup_user_message(message)


@router.message(NewPlanStates.waiting_hours_per_day)
async def receive_hours(message: Message, state: FSMContext) -> None:
    hours = _parse_positive_float(message.text)
    if hours is None:
        await render_screen(
            message,
            state,
            "Send a valid positive number for hours per day.",
            reply_markup=new_plan_keyboard(),
            keyboard_key="new_plan",
        )
        await cleanup_user_message(message)
        return
    await state.update_data(hours_per_day=hours)
    await state.set_state(NewPlanStates.waiting_weak_topics)
    await render_screen(
        message,
        state,
        "What topics feel weakest right now? Send them comma-separated, or send 'skip'.",
        reply_markup=new_plan_keyboard(),
        keyboard_key="new_plan",
    )
    await cleanup_user_message(message)


@router.message(NewPlanStates.waiting_weak_topics)
async def receive_weak_topics(message: Message, state: FSMContext) -> None:
    weak_topics = _parse_optional_answer(message.text)
    await state.update_data(weak_topics=weak_topics)
    await state.set_state(NewPlanStates.waiting_preferred_mode)
    await render_screen(
        message,
        state,
        "What should the plan emphasize: practice, theory, or balanced?",
        reply_markup=new_plan_keyboard(),
        keyboard_key="new_plan",
    )
    await cleanup_user_message(message)


@router.message(NewPlanStates.waiting_preferred_mode)
async def receive_preferred_mode(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    data = await state.get_data()
    preferred_mode = _normalize_preferred_mode(message.text)
    try:
        user = await backend.upsert_telegram_user(message.from_user)
        plan = await backend.create_study_plan(
            {
                "user_id": user["id"],
                "exam_name": data["exam_name"],
                "days_available": data["days_available"],
                "hours_per_day": data["hours_per_day"],
                "start_date": date.today().isoformat(),
                "generation_mode": "hybrid",
            }
        )
        await backend.upload_text_material(
            {
                "user_id": user["id"],
                "study_plan_id": plan["id"],
                "text": _build_plan_brief(
                    exam_name=data["exam_name"],
                    weak_topics=data.get("weak_topics"),
                    preferred_mode=preferred_mode,
                ),
                "original_filename": "student_brief.txt",
            }
        )
        await backend.generate_study_plan(plan["id"])
        full_plan = await backend.get_plan(plan["id"])
        progress = await backend.get_plan_progress(plan["id"])
        materials = await backend.get_plan_materials(plan["id"])
    except BackendClientError as exc:
        await render_screen(
            message,
            state,
            f"Failed to create plan: {exc}",
            reply_markup=new_plan_keyboard(),
            keyboard_key="new_plan",
        )
        await cleanup_user_message(message)
        return

    await state.set_state(PlanStates.plan_actions)
    await state.update_data(selected_plan_id=plan["id"])
    await render_screen(
        message,
        state,
        "Plan created.\n\n"
        + format_plan_overview(full_plan, progress=progress, materials=materials),
        reply_markup=plan_actions_keyboard(),
        keyboard_key="plan_actions",
        force_new=True,
    )
    await cleanup_user_message(message)
