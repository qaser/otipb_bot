import re
import inspect
import logging
from aiogram import Bot

from config.bot_config import bot
from config.telegram_config import MY_TELEGRAM_ID, GROUP_ID
from utils.constants import DEPARTMENTS


# ---------- Ошибки ----------

async def report_error(e: Exception):
    frame = inspect.stack()[1]
    func_name = frame.function
    file_name = frame.filename
    line_number = frame.lineno
    error_text = f"Ошибка в {func_name} ({file_name}, строка {line_number}): {str(e)}"
    logging.error(error_text)
    try:
        await bot.send_message(MY_TELEGRAM_ID, text=f'❗️{error_text}')
    except Exception as inner_e:
        logging.error(f"Ошибка при отправке админу: {str(inner_e)}")


# ---------- Распознавание служб ----------
class DepartmentDetector:
    def __init__(self):
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        """Создает словарь паттернов с прямым соответствием DEPARTMENTS"""
        patterns = {}

        # --- АиМО ---
        patterns['АиМО КЦ-1'] = re.compile(r'аимо\s*к[цс][\s\-]*1', re.IGNORECASE)
        patterns['АиМО КЦ-2'] = re.compile(r'аимо\s*к[цс][\s\-]*2', re.IGNORECASE)
        patterns['АиМО КЦ-3'] = re.compile(r'аимо\s*к[цс][\s\-]*3', re.IGNORECASE)
        patterns['АиМО КЦ-4'] = re.compile(r'аимо\s*к[цс][\s\-]*4', re.IGNORECASE)
        patterns['АиМО КЦ-5'] = re.compile(r'аимо\s*к[цс][\s\-]*5', re.IGNORECASE)
        patterns['АиМО КЦ-6'] = re.compile(r'аимо\s*к[цс][\s\-]*6', re.IGNORECASE)
        patterns['АиМО КЦ-7,8'] = re.compile(r'аимо\s*к[цс][\s\-]*7\s*[,\.]?\s*8', re.IGNORECASE)
        patterns['АиМО КЦ-9,10'] = re.compile(r'аимо\s*к[цс][\s\-]*9\s*[,\.]?\s*10', re.IGNORECASE)
        patterns['АиМО ТМ'] = re.compile(r'аимо\s*тм', re.IGNORECASE)
        patterns['АиМО ВО'] = re.compile(r'аимо\s*во', re.IGNORECASE)

        # --- ГКС ---
        patterns['ГКС КЦ-1,4'] = re.compile(r'(гкс\s*)?к[цс][\s\-]*1\s*[,\.]?\s*4(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-2,3'] = re.compile(r'(гкс\s*)?к[цс][\s\-]*2\s*[,\.]?\s*3(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-5,6'] = re.compile(r'(гкс\s*)?к[цс][\s\-]*5\s*[,\.]?\s*6(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-7,8'] = re.compile(r'(гкс\s*)?к[цс][\s\-]*7\s*[,\.]?\s*8(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-9,10'] = re.compile(r'(гкс\s*)?к[цс][\s\-]*9\s*[,\.]?\s*10(?!\s*аимо)', re.IGNORECASE)

        # --- Прочие службы ---
        patterns['ЭВС Участок ТОиР ОЭ КС'] = re.compile(
            r'эвс.*участок.*тоир.*оэ.*к[сц]|участок.*тоир.*оэ.*к[сц]', re.IGNORECASE
        )
        patterns['Служба связи'] = re.compile(r'служб[аы]?\s*связи', re.IGNORECASE)
        patterns['ВПО'] = re.compile(r'впо', re.IGNORECASE)
        patterns['СЗК'] = re.compile(r'сзк', re.IGNORECASE)
        patterns['ЛЭС'] = re.compile(r'лэс', re.IGNORECASE)
        patterns['г. ХиР МТР'] = re.compile(r'(хи[и]?р|мтр)', re.IGNORECASE)

        return patterns

    def detect_department(self, text: str):
        """Определяет службу по тексту и возвращает точное имя из DEPARTMENTS"""
        if not text:
            return None
        text = text.strip()
        for department, pattern in self.patterns.items():
            if pattern.search(text):
                # проверяем, что найденное имя есть в DEPARTMENTS
                if department in DEPARTMENTS:
                    return department
                else:
                    # fallback — ищем ближайшее совпадение
                    for d in DEPARTMENTS:
                        if department.lower() in d.lower():
                            return d
        return None


# ---------- Управление службами ----------

class DepartmentManager:
    def __init__(self, buffer_collection):
        self.buffer = buffer_collection
        self.detector = DepartmentDetector()

    def generate_departments_list(self, reported_departments: set) -> str:
        lines = []
        for department in DEPARTMENTS:
            if department in reported_departments:
                lines.append(f"🟢 {department}")
            else:
                lines.append(f"⚪ {department}")
        return "\n".join(lines)

    async def update_level_message(self, bot: Bot, level: int):
        msg_data = self.buffer.find_one({'level': level})
        if not msg_data:
            return
        reported_departments = set(msg_data.get('reported_departments', []))
        title = "📋 Журнал дефектов основного и вспомогательного оборудования\n\n" if level == 1 else "📋 Журнал АПК\n\n"
        text = title + self.generate_departments_list(reported_departments)
        try:
            await bot.edit_message_text(chat_id=GROUP_ID, message_id=msg_data['msg_id'], text=text)
        except Exception as e:
            await report_error(e)

    async def mark_department_reported(self, bot: Bot, department: str, level: int):
        """Добавляет службу и обновляет сообщение"""
        msg_data = self.buffer.find_one({'level': level})
        if not msg_data:
            return
        self.buffer.update_one({'_id': msg_data['_id']}, {'$addToSet': {'reported_departments': department}})
        await self.update_level_message(bot, level)

    async def refresh_all(self, bot: Bot):
        """Обновляет все сообщения"""
        for lvl in [1, 2]:
            await self.update_level_message(bot, lvl)
