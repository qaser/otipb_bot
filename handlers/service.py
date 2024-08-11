from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove
from utils.constants import INITIAL_TEXT
from aiogram.fsm.context import FSMContext
from config.telegram_config import MY_TELEGRAM_ID, CHIEF_ENGINEER_ID
from config.bot_config import bot
from config.mongo_config import reports
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import datetime as dt


router = Router()

START_TEXT = (
    'Это бот для анонимного информирования руководства филиала '
    'о нарушениях, связанных с охраной труда и промышленной безопасностью.\n'
    'Для ввода сообщения нажмите /report'
)
THX_TEXT = (
    'Информация отправлена.\nСпасибо за обращение, '
    'вместе мы сделаем нашу работу безопаснее!\n'
    'Для ввода новой информации нажмите\n/report'
)
ABORT_TEXT = (
    'Информация не отправлена.\n'
    'Если необходимо отправить новую информацию '
    '- нажмите /report'
)


class Report(StatesGroup):
    waiting_report = State()
    waiting_confirm = State()


@router.message(Command('reset'))
async def reset_handler(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
    await message.answer(
        'Текущее состояние бота сброшено',
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command('report'))
async def report(message: Message, state: FSMContext):
    await message.delete()
    await message.answer('Введите проблемный вопрос, информацию о нарушении '
                         'или потенциально опасном событии')
    await state.set_state(Report.waiting_report)


@router.message(Report.waiting_report)
async def report_confirm(message: Message, state: FSMContext):
    await state.update_data(report=message.text)
    kb = ReplyKeyboardBuilder()
    kb.button(text='Нет')
    kb.button(text='Да')
    kb.adjust(2)
    await message.answer(
        text='Информация получена. Отправить?',
        reply_markup=kb.as_markup(resize_keyboard=True)
    )
    await state.set_state(Report.waiting_confirm)


@router.message(Report.waiting_confirm)
async def report_save(message: Message, state: FSMContext):
    if message.text.lower() not in ['нет', 'да']:
        await message.answer('Пожалуйста, отправьте "Да" или "Нет"')
        return
    if message.text.lower() == 'да':
        user_id = message.from_user.id
        data = await state.get_data()
        report_text = data['report']
        reports.insert_one(
            {
                'user_id': user_id,
                'datetime': dt.datetime.now(),
                'text': report_text,
            }
        )
        await state.clear()
        for target_id in [MY_TELEGRAM_ID, CHIEF_ENGINEER_ID]:
            try:
                await bot.send_message(
                    chat_id=target_id,
                    text=(
                        'Получена информация о нарушении или потенциально '
                        f'опасном событии:\n\n <b>{report_text}</b>'
                    ),
                )
            except:
                print(target_id)
        await message.answer(THX_TEXT, reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(ABORT_TEXT, reply_markup=ReplyKeyboardRemove())
        await state.clear()


@router.message(Command('start'))
async def start_handler(message: Message):
    await message.answer(START_TEXT)


@router.message(Command('help'))
async def help_handler(message: Message):
    await message.answer(INITIAL_TEXT)


@router.message(Command('log'))
async def send_logs(message: Message):
    user_id = message.from_user.id
    if user_id == int(MY_TELEGRAM_ID):
        document = FSInputFile(path=r'logs_bot.log')
        await message.answer_document(document=document)
    await message.delete()
