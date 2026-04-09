import re

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

NEW_PLAN_BUTTON = "Create plan"
MY_PLANS_BUTTON = "My plans"
TODAY_BUTTON = "Today"
PROGRESS_BUTTON = "Progress"
MAIN_MENU_BUTTON = "Main menu"
BACK_TO_PLANS_BUTTON = "Back to plans"
VIEW_PLAN_BUTTON = "View plan"
COMPLETE_NEXT_BUTTON = "Complete next session"
UPLOAD_MATERIALS_BUTTON = "Add materials"
REGENERATE_PLAN_BUTTON = "Regenerate plan"
DELETE_PLAN_BUTTON = "Delete plan"
CANCEL_UPLOAD_BUTTON = "Cancel upload"
CONFIRM_DELETE_BUTTON = "Confirm delete"
CANCEL_DELETE_BUTTON = "Keep plan"


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
    if len(exam_name) > 28:
        exam_name = exam_name[:25].rstrip() + "..."
    return f"Plan {plan['id']} | {exam_name}"


def extract_plan_id(label: str | None) -> int | None:
    match = re.match(r"^Plan\s+(\d+)\b", (label or "").strip())
    if match is None:
        return None
    return int(match.group(1))


def session_action_keyboard(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Complete", callback_data=f"session:complete:{session_id}"),
                InlineKeyboardButton(text="Skip", callback_data=f"session:skip:{session_id}"),
            ]
        ]
    )
