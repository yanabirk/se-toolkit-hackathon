import re

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

NEW_PLAN_BUTTON = "📝 New plan"
MY_PLANS_BUTTON = "📚 My plans"
TODAY_BUTTON = "📅 Today"
PROGRESS_BUTTON = "📈 Progress"
MAIN_MENU_BUTTON = "🏠 Menu"
BACK_TO_PLANS_BUTTON = "⬅️ Plans"
VIEW_PLAN_BUTTON = "🗂 Sessions"
COMPLETE_NEXT_BUTTON = "✅ Complete next"
UPLOAD_MATERIALS_BUTTON = "📎 Add material"
REGENERATE_PLAN_BUTTON = "♻️ Regenerate"
DELETE_PLAN_BUTTON = "🗑 Delete plan"
CANCEL_UPLOAD_BUTTON = "✖️ Cancel upload"
CONFIRM_DELETE_BUTTON = "🗑 Yes, delete"
CANCEL_DELETE_BUTTON = "⬅️ Keep plan"


def session_status_icon(status: str) -> str:
    return {
        "completed": "✅",
        "skipped": "⏭",
        "pending": "◻️",
    }.get(status, "•")


def _shorten(text: str, limit: int = 28) -> str:
    value = " ".join(text.split()).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _reply_keyboard(
    rows: list[list[str]],
    *,
    placeholder: str | None = None,
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=label) for label in row]
            for row in rows
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=placeholder,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return _reply_keyboard(
        [
            [NEW_PLAN_BUTTON, MY_PLANS_BUTTON],
            [TODAY_BUTTON, PROGRESS_BUTTON],
        ],
        placeholder="Choose an action",
    )


def new_plan_keyboard() -> ReplyKeyboardMarkup:
    return _reply_keyboard(
        [[MAIN_MENU_BUTTON]],
        placeholder="Answer the setup questions",
    )


def plans_menu_keyboard(plans: list[dict]) -> ReplyKeyboardMarkup:
    rows = [[plan_button_text(plan)] for plan in plans]
    rows.append([MAIN_MENU_BUTTON])
    return _reply_keyboard(rows, placeholder="Choose a plan")


def plan_actions_keyboard() -> ReplyKeyboardMarkup:
    return _reply_keyboard(
        [
            [VIEW_PLAN_BUTTON, COMPLETE_NEXT_BUTTON],
            [UPLOAD_MATERIALS_BUTTON, REGENERATE_PLAN_BUTTON],
            [DELETE_PLAN_BUTTON],
            [BACK_TO_PLANS_BUTTON, MAIN_MENU_BUTTON],
        ],
        placeholder="Choose an action for this plan",
    )


def upload_material_keyboard() -> ReplyKeyboardMarkup:
    return _reply_keyboard(
        [
            [CANCEL_UPLOAD_BUTTON],
            [BACK_TO_PLANS_BUTTON, MAIN_MENU_BUTTON],
        ],
        placeholder="Send text, PDF, DOCX, or image",
    )


def delete_plan_keyboard() -> ReplyKeyboardMarkup:
    return _reply_keyboard(
        [
            [CONFIRM_DELETE_BUTTON, CANCEL_DELETE_BUTTON],
            [BACK_TO_PLANS_BUTTON, MAIN_MENU_BUTTON],
        ],
        placeholder="Confirm deletion",
    )


def plan_button_text(plan: dict) -> str:
    exam_name = str(plan.get("exam_name", "Plan")).strip()
    return f"📘 Plan {plan['id']} · {_shorten(exam_name, limit=24)}"


def extract_plan_id(label: str | None) -> int | None:
    match = re.match(r"^.*?Plan\s+(\d+)\b", (label or "").strip())
    if match is None:
        return None
    return int(match.group(1))


def _session_button_text(session: dict, *, show_day: bool) -> str:
    prefix = session_status_icon(str(session.get("status", "pending")))
    title = _shorten(str(session.get("title", "Session")), limit=26 if show_day else 30)
    if show_day:
        slot = f"D{session['day_number']}·{session['session_order']}"
    else:
        slot = f"{session['session_order']}."
    return f"{prefix} {slot} {title}"


def session_list_keyboard(
    plan_id: int,
    sessions: list[dict],
    *,
    context: str,
) -> InlineKeyboardMarkup:
    show_day = context == "plan"
    rows = [
        [
            InlineKeyboardButton(
                text=_session_button_text(session, show_day=show_day),
                callback_data=f"session:view:{context}:{plan_id}:{session['id']}",
            )
        ]
        for session in sessions
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back to plan",
                callback_data=f"nav:plan:{plan_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def session_detail_keyboard(
    *,
    context: str,
    plan_id: int,
    session_id: int,
    status: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    action_row: list[InlineKeyboardButton] = []
    if status != "completed":
        action_row.append(
            InlineKeyboardButton(
                text="✅ Mark done",
                callback_data=f"session:complete:{context}:{plan_id}:{session_id}",
            )
        )
    if status == "pending":
        action_row.append(
            InlineKeyboardButton(
                text="⏭ Skip",
                callback_data=f"session:skip:{context}:{plan_id}:{session_id}",
            )
        )
    if action_row:
        rows.append(action_row)
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back to sessions",
                callback_data=f"session:list:{context}:{plan_id}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back to plan",
                callback_data=f"nav:plan:{plan_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def session_action_keyboard(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Complete",
                    callback_data=f"session:complete:{session_id}",
                ),
                InlineKeyboardButton(
                    text="Skip",
                    callback_data=f"session:skip:{session_id}",
                ),
            ]
        ]
    )
