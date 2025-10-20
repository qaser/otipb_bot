import asyncio
import logging

from aiogram import F, Bot, Router

from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReactionTypeEmoji
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.bot_config import bot, dp
from config.mongo_config import buffer
from config.telegram_config import MY_TELEGRAM_ID, GROUP_ID
from handlers import service
from utils.utils import report_error, DepartmentDetector, DepartmentManager
from utils.constants import MSG_TEXT, DEPARTMENTS


MSG_TEXT_1_LEVEL = "📋 Журнал дефектов основного и вспомогательного оборудования\n\n" + "\n".join([f"⚪ {dept}" for dept in DEPARTMENTS])
MSG_TEXT_2_LEVEL = "📋 Журнал АПК\n\n" + "\n".join([f"⚪ {dept}" for dept in DEPARTMENTS])

# Создаем детектор
detector = DepartmentDetector()
department_manager = DepartmentManager(buffer)


@dp.message(F.content_type.in_({'photo', 'document'}))
async def handle_media_with_caption(message: Message, bot: Bot):
    """Обрабатывает сообщения с фото/документами и подписью"""
    text = message.caption or ""
    department = department_manager.detector.detect_department(text)
    if department and message.message_thread_id:
        # Определяем уровень по ID треда
        thread_id = message.message_thread_id
        level = get_level_by_thread_id(thread_id)  # Нужно реализовать эту функцию
        if level in [1, 2]:
            # Обновляем список служб
            await department_manager.mark_department_reported(bot, department, level)
            await message.react([ReactionTypeEmoji(emoji='👍')])
            # print(f"Обнаружена служба: {department} в треде уровня {level}")


@dp.message(F.text)
async def handle_text_message(message: Message, bot: Bot):
    """Обрабатывает текстовые сообщения (отдельные сообщения со службами)"""
    text = message.text or ""
    department = department_manager.detector.detect_department(text)
    if department and message.message_thread_id:
        # Определяем уровень по ID треда
        thread_id = message.message_thread_id
        level = get_level_by_thread_id(thread_id)  # Нужно реализовать эту функцию
        if level in [1, 2]:
            # Обновляем список служб
            await department_manager.mark_department_reported(bot, department, level)
            await message.react([ReactionTypeEmoji(emoji='👍')])
            # print(f"Обнаружена служба: {department} в текстовом сообщении уровня {level}")


async def send_reminder():
    """Отправляет напоминание и два сообщения со списками служб"""
    try:
        # Основное сообщение
        await bot.send_message(chat_id=GROUP_ID, text=MSG_TEXT)
    except Exception as e:
        await report_error(e)

    try:
        # Сообщение для первого уровня
        msg_1_lvl = await bot.send_message(chat_id=GROUP_ID, text=MSG_TEXT_1_LEVEL)
        department_manager.buffer.insert_one({
            'msg_id': msg_1_lvl.message_id,
            'level': 1,
            'type': 'departments_list'
        })
    except Exception as e:
        await report_error(e)

    try:
        # Сообщение для второго уровня
        msg_2_lvl = await bot.send_message(chat_id=GROUP_ID, text=MSG_TEXT_2_LEVEL)
        department_manager.buffer.insert_one({
            'msg_id': msg_2_lvl.message_id,
            'level': 2,
            'type': 'departments_list'
        })
    except Exception as e:
        await report_error(e)


def get_level_by_thread_id(thread_id: int):
    """
    Определяет уровень по ID треда.
    Нужно реализовать логику сопоставления ID тредов с уровнями.
    """
    # Пример реализации - замените на вашу логику
    level_1_threads = [3, 373]  # ID тредов первого уровня
    level_2_threads = [2, 371]  # ID тредов второго уровня

    if thread_id in level_1_threads:
        return 1
    elif thread_id in level_2_threads:
        return 2
    else:
        return None


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
        minute=40,
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
