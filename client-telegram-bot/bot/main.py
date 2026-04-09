import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.handlers import callbacks, my_plans, new_plan, progress, start, today


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher(storage=MemoryStorage())

    dispatcher.include_router(start.router)
    dispatcher.include_router(new_plan.router)
    dispatcher.include_router(my_plans.router)
    dispatcher.include_router(today.router)
    dispatcher.include_router(progress.router)
    dispatcher.include_router(callbacks.router)

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
