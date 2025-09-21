import random
import inspect
import logging

from config.bot_config import bot
from config.telegram_config import MY_TELEGRAM_ID


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
