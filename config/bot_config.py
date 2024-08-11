from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config.telegram_config import TELEGRAM_TOKEN

storage = MemoryStorage()
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode='HTML')
)
dp = Dispatcher(storage=storage)
