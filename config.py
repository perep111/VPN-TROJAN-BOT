import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from yoomoney import Client
import os
from dotenv import load_dotenv

load_dotenv()

# webhook settings
WEBHOOK_HOST = 'https://24perep.ru'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 88

API_TOKEN = os.getenv('API_TOKEN')
TOKEN_UKASSA_TEST = os.getenv('TOKEN_UKASSA_TEST')
TOKEN_UKASSA = os.getenv('TOKEN_UKASSA')


TOKEN_CLIENT = os.getenv('TOKEN_CLIENT')

client = Client(TOKEN_CLIENT)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)
