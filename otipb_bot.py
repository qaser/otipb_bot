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
            'Для автоматического учёта отправленных сообщений прошу указывать службу '
            '(в виде контекста или отдельным сообщением).')

DEPARTMENTS = [
    'АиМО КЦ-1',
    'АиМО КЦ-2',
    'АиМО КЦ-3',
    'АиМО КЦ-4',
    'АиМО КЦ-5',
    'АиМО КЦ-6',
    'АиМО КЦ-7,8',
    'АиМО КЦ-9,10',
    'АиМО ТМ',
    'АиМО ВО',
    'ГКС КЦ-1,4',
    'ГКС КЦ-2,3',
    'ГКС КС-5,6',
    'ГКС КС-7,8',
    'ГКС КС-9,10',
    'ЭВС Участок ТОиР ОЭ КС',
    'Служба связи',
    'ВПО',
    'СЗК',
]


@dp.message(F.content_type.in_({'text', 'video', 'photo', 'document'}))
async def archive_messages(message: Message):
    chat = message.chat.id
    thread = message.message_thread_id
    if message.text:
        await bot.send_message(
            chat_id=MY_TELEGRAM_ID,
            text=f'{message.chat.id} {thread} принято',
            parse_mode='HTML'
        )


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
        day_of_week='sun',
        hour=17,
        minute=51,
        timezone='Asia/Yekaterinburg'
    )
    scheduler.start()
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
