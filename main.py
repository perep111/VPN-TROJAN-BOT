import logging
import asyncio
from aiohttp import ClientSession
from aiogram import Bot
from aiohttp import web
from aiogram import types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from func import bot, WEBHOOK_URL, WEBHOOK_PATH, check_users_periodically, send_notifications
from func import WEBAPP_HOST, WEBAPP_PORT
from config import dp
from database import create_db
from yookassa_pay import yookassa_webhook_handler
import handlers  # Ваши обработчики

logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())

# Пути для вебхуков
YOO_WEBHOOK_PATH = "/yookassa/webhook"

# Убираем глобальное создание сессии
session = None  # Глобальная переменная для хранения сессии
db_pool = None  # Глобальный пул подключений

# Обработчики Telegram-бота
async def on_startup(dp):
    await create_db()  # Создание базы данных перед стартом
    global session
    session = ClientSession()  # Создаём сессию внутри асинхронной функции
    Bot.set_current(bot)
    await bot.set_webhook(WEBHOOK_URL)
    loop = asyncio.get_event_loop()
    loop.create_task(check_users_periodically())
    loop.create_task(send_notifications())
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Главное меню"),
    ])
    logging.info("Бот запущен и вебхук установлен.")

async def on_shutdown(dp):
    global session
    logging.warning("Завершаем работу...")
    if session:
        await session.close()
        logging.warning("Закрытие aiohttp.ClientSession завершено.")

    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("До свидания!")

# Основное приложение Aiohttp
async def init_app():
    # Создание приложения
    app = web.Application()

    # Маршруты
    app.router.add_post(WEBHOOK_PATH, bot_webhook_handler)  # Telegram бот
    app.router.add_post(YOO_WEBHOOK_PATH, yookassa_webhook_handler)  # YooKassa

    # Установим обработчики старта и завершения
    app.on_startup.append(on_startup_hook)
    app.on_shutdown.append(on_shutdown_hook)

    return app

async def bot_webhook_handler(request):
    """Обработчик вебхуков Telegram."""
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return web.Response()

async def on_startup_hook(app):
    """Вызывается при запуске Aiohttp."""
    await on_startup(dp)

async def on_shutdown_hook(app):
    """Вызывается при завершении работы Aiohttp."""
    await on_shutdown(dp)


if __name__ == "__main__":
    logging.info("Запуск приложения...")
    web.run_app(init_app(), host=WEBAPP_HOST, port=WEBAPP_PORT)
