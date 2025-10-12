import random
import inspect
import logging
import re

from aiogram import Bot

from config.bot_config import bot
from config.telegram_config import MY_TELEGRAM_ID, GROUP_ID
from utils.constants import DEPARTMENTS


def random_list_elem(list):
    list_len = len(list) - 1
    rand_num = random.randint(0, list_len)
    return rand_num


def word_conjugate(number):
    args = ['заявка', 'заявки', 'заявок']
    int_num = int(number)
    last_digit = int_num % 10
    last_two_digit = int_num % 100  # для проверки 11...14
    if last_digit == 1 and last_two_digit != 11:
        return f'{args[0]}'  # заявка
    if 1 < last_digit < 5 and last_two_digit not in range(11, 15):
        return f'{args[1]}'  # заявки
    return f'{args[2]}'  # заявок


async def report_error(e: Exception):
    """Уведомляет администратора и логирует ошибку"""
    # Получаем стек вызовов
    frame = inspect.stack()[1]
    func_name = frame.function
    file_name = frame.filename
    line_number = frame.lineno
    # Текст ошибки
    error_text = f"Ошибка в {func_name} ({file_name}, строка {line_number}): {str(e)}"
    # Логируем ошибку в файл
    logging.error(error_text)
    # Пытаемся отправить сообщение админу
    try:
        await bot.send_message(MY_TELEGRAM_ID, text=f'❗️{error_text}')
    except Exception as inner_e:
        logging.error(f"Ошибка при отправке уведомления администратору: {str(inner_e)}")


class DepartmentDetector:
    def __init__(self):
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        patterns = {}
        # Паттерны для АиМО служб
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

        # Паттерны для ГКС служб - ВСЕГДА возвращаем с "КЦ" для соответствия DEPARTMENTS
        patterns['ГКС КЦ-1,4'] = re.compile(r'гкс\s*к[цс][\s\-]*1\s*[,\.]?\s*4', re.IGNORECASE)
        patterns['ГКС КЦ-2,3'] = re.compile(r'гкс\s*к[цс][\s\-]*2\s*[,\.]?\s*3', re.IGNORECASE)
        patterns['ГКС КЦ-5,6'] = re.compile(r'гкс\s*к[цс][\s\-]*5\s*[,\.]?\s*6', re.IGNORECASE)
        patterns['ГКС КЦ-7,8'] = re.compile(r'гкс\s*к[цс][\s\-]*7\s*[,\.]?\s*8', re.IGNORECASE)
        patterns['ГКС КЦ-9,10'] = re.compile(r'гкс\s*к[цс][\s\-]*9\s*[,\.]?\s*10', re.IGNORECASE)

        # Паттерны для ГКС служб (без явного указания ГКС) - тоже возвращаем с "КЦ"
        patterns['ГКС КЦ-1,4_auto'] = re.compile(r'к[цс][\s\-]*1\s*[,\.]?\s*4(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-2,3_auto'] = re.compile(r'к[цс][\s\-]*2\s*[,\.]?\s*3(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-5,6_auto'] = re.compile(r'к[цс][\s\-]*5\s*[,\.]?\s*6(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-7,8_auto'] = re.compile(r'к[цс][\s\-]*7\s*[,\.]?\s*8(?!\s*аимо)', re.IGNORECASE)
        patterns['ГКС КЦ-9,10_auto'] = re.compile(r'к[цс][\s\-]*9\s*[,\.]?\s*10(?!\s*аимо)', re.IGNORECASE)

        # Остальные службы
        patterns['ЭВС Участок ТОиР ОЭ КС'] = re.compile(
            r'эвс.*участок.*тоир.*оэ.*к[сц]|участок.*тоир.*оэ.*к[сц]', re.IGNORECASE
        )
        patterns['Служба связи'] = re.compile(r'служб[аы]?\s*связи', re.IGNORECASE)
        patterns['ВПО'] = re.compile(r'впо', re.IGNORECASE)
        patterns['СЗК'] = re.compile(r'сзк', re.IGNORECASE)
        return patterns

    def detect_department(self, text: str):
        """Определяет службу в тексте сообщения"""
        if not text:
            return None
        text = text.strip()
        # Сначала проверяем явные указания служб
        for department, pattern in self.patterns.items():
            if '_auto' not in department and pattern.search(text):
                return department
        # Затем проверяем автоматическое определение ГКС (если не нашли АиМО)
        for department, pattern in self.patterns.items():
            if '_auto' in department and pattern.search(text):
                return department.replace('_auto', '')
        return None


class DepartmentManager:
    def __init__(self, buffer_collection):
        self.buffer = buffer_collection
        self.detector = DepartmentDetector()
        # Состояния служб по уровням - инициализируем как множества
        self.level_1_reports = set()
        self.level_2_reports = set()

    def generate_departments_list(self, reported_departments: set) -> str:
        """Генерирует текст со списком служб"""
        lines = []
        for department in DEPARTMENTS:
            if department in reported_departments:
                lines.append(f"🟢 {department}")
            else:
                lines.append(f"⚪ {department}")
        return "\n".join(lines)

    async def update_level_message(self, bot: Bot, level: int, thread_id: int = None):
        """Обновляет сообщение с списком служб для указанного уровня"""
        # Находим сообщение в БД
        msg_data = self.buffer.find_one({'level': level})
        if not msg_data:
            return
        reported_departments = self.level_1_reports if level == 1 else self.level_2_reports
        title = "📋 Первый уровень АПК\n\n" if level == 1 else "📋 Второй уровень АПК\n\n"
        text = title + self.generate_departments_list(reported_departments)
        try:
            await bot.edit_message_text(
                chat_id=GROUP_ID,
                message_id=msg_data['msg_id'],
                text=text,
            )
        except Exception as e:
            await report_error(e)
            # print(f"Ошибка при обновлении сообщения уровня {level}: {e}")

    async def mark_department_reported(self, bot: Bot, department: str, level: int, thread_id: int = None):
        """Отмечает службу как отчитавшуюся и обновляет сообщение"""
        if level == 1:
            self.level_1_reports.add(department)
        else:
            self.level_2_reports.add(department)
        await self.update_level_message(bot, level, thread_id)
        # Для отладки - выводим текущее состояние
        # print(f"Уровень {level} - отчитавшиеся службы: {self.level_1_reports if level == 1 else self.level_2_reports}")

    async def reset_reports(self, level: int = None):
        """Сбрасывает отчеты для указанного уровня или всех уровней"""
        if level is None:
            self.level_1_reports.clear()
            self.level_2_reports.clear()
        elif level == 1:
            self.level_1_reports.clear()
        elif level == 2:
            self.level_2_reports.clear()
