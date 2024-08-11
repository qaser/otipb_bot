import asyncio
import logging

# from aiogram.filters.command import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.types import MessageReactionUpdated

from config.bot_config import bot, dp
from handlers import service



async def main():
    dp.include_routers(
        service.router,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        filename='logs_bot.log',
        level=logging.INFO,
        filemode='a',
        format='%(asctime)s - %(message)s',
        datefmt='%d.%m.%y %H:%M:%S',
        encoding='utf-8',
    )
    asyncio.run(main())
