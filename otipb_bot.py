import asyncio
import logging

from aiogram import F

from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.bot_config import bot, dp
from config.telegram_config import MY_TELEGRAM_ID, GROUP_ID
from handlers import service
from utils.utils import report_error


MSG_TEXT = ('Прошу предоставить фотографии журналов и актов АПК в данную группу до 12:00. '
            'Для автоматического учёта отправленных сообщений прошу указывать службу (в виде контекста или отдельным сообщением).')


# @dp.message(F.content_type.in_({'text', 'video', 'photo', 'document'}))
# async def archive_messages(message: Message):
#     chat = message.chat.id
#     thread = message.message_thread_id
#     if message.text:
#         await bot.send_message(
#             chat_id=MY_TELEGRAM_ID,
#             text=f'{message.chat.id} {thread} принято',
#             parse_mode='HTML'
#         )


async def send_reminder():
    try:
        await bot.send_message(chat_id=GROUP_ID, text=MSG_TEXT)
    except Exception as e:
        await report_error(e)


# удаление сервисных сообщений
@dp.message(
        F.content_type.in_([
            'pinned_message',
            'left_chat_member',
            'forum_topic_created',
            'forum_topic_closed',
            'forum_topic_edited',
            'forum_topic_reopened',
            'new_chat_members'
        ])
    )
async def delete_service_pinned_message(message: Message):
    try:
        await message.delete()
    except:
        pass


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminder,
        'cron',
        day_of_week='mon',
        hour=8,
        minute=30,
        timezone='Asia/Yekaterinburg'
    )
    dp.include_routers(service.router)
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
