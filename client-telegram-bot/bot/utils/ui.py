from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup

SCREEN_MESSAGE_ID_KEY = "screen_message_id"
SCREEN_KEYBOARD_KEY = "screen_keyboard_key"


async def render_screen(
    message: Message,
    state: FSMContext,
    text: str,
    *,
    reply_markup: ReplyKeyboardMarkup | None = None,
    keyboard_key: str | None = None,
    force_new: bool = False,
) -> Message:
    data = await state.get_data()
    previous_message_id = data.get(SCREEN_MESSAGE_ID_KEY)
    previous_keyboard_key = data.get(SCREEN_KEYBOARD_KEY)

    if (
        not force_new
        and previous_message_id is not None
        and previous_keyboard_key == keyboard_key
    ):
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=int(previous_message_id),
                text=text,
            )
            await state.update_data(
                **{
                    SCREEN_MESSAGE_ID_KEY: int(previous_message_id),
                    SCREEN_KEYBOARD_KEY: keyboard_key,
                }
            )
            return message
        except TelegramBadRequest:
            pass

    sent = await message.answer(text, reply_markup=reply_markup)

    if previous_message_id is not None and int(previous_message_id) != sent.message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=int(previous_message_id),
            )
        except TelegramBadRequest:
            pass

    await state.update_data(
        **{
            SCREEN_MESSAGE_ID_KEY: sent.message_id,
            SCREEN_KEYBOARD_KEY: keyboard_key,
        }
    )
    return sent


async def cleanup_user_message(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def clear_state_preserving_screen(state: FSMContext) -> None:
    data = await state.get_data()
    screen_message_id = data.get(SCREEN_MESSAGE_ID_KEY)
    screen_keyboard_key = data.get(SCREEN_KEYBOARD_KEY)
    await state.clear()
    if screen_message_id is not None:
        await state.update_data(
            **{
                SCREEN_MESSAGE_ID_KEY: screen_message_id,
                SCREEN_KEYBOARD_KEY: screen_keyboard_key,
            }
        )
