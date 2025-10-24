import asyncio
import logging
from aiogram import F, Bot
from aiogram.filters.command import Command
from aiogram.types import Message, BotCommand, ReactionTypeEmoji
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.bot_config import bot, dp
from config.mongo_config import buffer
from config.telegram_config import MY_TELEGRAM_ID, GROUP_ID
from handlers import service
from utils.utils import report_error, DepartmentDetector, DepartmentManager
from utils.constants import MSG_TEXT, DEPARTMENTS


# Тексты сообщений
MSG_TEXT_1_LEVEL = "📋 Журнал дефектов основного и вспомогательного оборудования\n\n" + "\n".join(
    [f"⚪ {dept}" for dept in DEPARTMENTS]
)
MSG_TEXT_2_LEVEL = "📋 Журнал АПК\n\n" + "\n".join([f"⚪ {dept}" for dept in DEPARTMENTS])

# Менеджер служб
department_manager = DepartmentManager(buffer)


# ---------------------- ОБРАБОТКА СООБЩЕНИЙ ----------------------

@dp.message(F.content_type.in_({'photo', 'document'}))
async def handle_media_with_caption(message: Message, bot: Bot):
    """Обработка фото/документов с подписями"""
    text = message.caption or ""
    department = department_manager.detector.detect_department(text)
    if department and message.message_thread_id:
        level = get_level_by_thread_id(message.message_thread_id)
        if level:
            await department_manager.mark_department_reported(bot, department, level)
            await message.react([ReactionTypeEmoji(emoji='👍')])


@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message, bot: Bot):
    """Обработка обычных текстов"""
    text = message.text or ""
    department = department_manager.detector.detect_department(text)
    if department and message.message_thread_id:
        level = get_level_by_thread_id(message.message_thread_id)
        if level:
            await department_manager.mark_department_reported(bot, department, level)
            await message.react([ReactionTypeEmoji(emoji='👍')])


# ---------------------- СЛУЖЕБНЫЕ КОМАНДЫ ----------------------

@dp.message(Command("status"))
async def show_status(message: Message):
    """Показывает текущие отчёты по уровням"""
    reports = department_manager.buffer.find({'type': 'departments_list'})
    text = "📊 Статус отчётности:\n\n"
    for doc in reports:
        reported = doc.get('reported_departments', [])
        total = len(DEPARTMENTS)
        done = len(reported)
        missing = [d for d in DEPARTMENTS if d not in reported]
        level = doc.get("level")
        text += f"Уровень {level}: {done}/{total} служб\n"
        if missing:
            text += "❌ Не отчитались:\n" + "\n".join(missing[:5])
            if len(missing) > 5:
                text += "\n..."
        text += "\n\n"
    await message.answer(text.strip())


@dp.message(Command("reset"))
async def reset_reports(message: Message):
    """Сбрасывает отчёты"""
    department_manager.buffer.update_many({'type': 'departments_list'}, {'$set': {'reported_departments': []}})
    await message.answer("🔄 Все отчёты сброшены.")
    # Обновляем сообщения
    await department_manager.refresh_all(bot)


# ---------------------- НАПОМИНАНИЯ ----------------------

async def send_reminder():
    """Отправляет напоминание и два списка служб"""
    try:
        # Удаляем старые записи
        department_manager.buffer.delete_many({'type': 'departments_list'})

        # Основной текст
        await bot.send_message(chat_id=GROUP_ID, text=MSG_TEXT)

        # Первый уровень
        msg_1_lvl = await bot.send_message(chat_id=GROUP_ID, text=MSG_TEXT_1_LEVEL)
        department_manager.buffer.insert_one({
            'msg_id': msg_1_lvl.message_id,
            'level': 1,
            'type': 'departments_list',
            'reported_departments': []
        })

        # Второй уровень
        msg_2_lvl = await bot.send_message(chat_id=GROUP_ID, text=MSG_TEXT_2_LEVEL)
        department_manager.buffer.insert_one({
            'msg_id': msg_2_lvl.message_id,
            'level': 2,
            'type': 'departments_list',
            'reported_departments': []
        })
    except Exception as e:
        await report_error(e)


def get_level_by_thread_id(thread_id: int):
    """Определяет уровень по ID треда"""
    level_1_threads = [3, 373]
    level_2_threads = [2, 371]
    if thread_id in level_1_threads:
        return 1
    elif thread_id in level_2_threads:
        return 2
    return None


# ---------------------- УДАЛЕНИЕ СЛУЖЕБНЫХ СООБЩЕНИЙ ----------------------

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


# ---------------------- MAIN ----------------------

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminder,
        'cron',
        day_of_week='mon',
        hour=7,
        minute=55,
        timezone='Asia/Yekaterinburg'
    )
    scheduler.start()

    # # Регистрируем команды в Telegram
    # await bot.set_my_commands([
    #     BotCommand(command="status", description="Показать текущие отчёты"),
    #     BotCommand(command="reset", description="Сбросить отчёты"),
    # ])

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
