from aiogram import executor
import logging
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from config import dp
import asyncio
from aiogram.utils.executor import start_webhook
from func import bot, WEBHOOK_URL, WEBHOOK_PATH, check_users_periodically, send_notifications
from func import WEBAPP_HOST, WEBAPP_PORT
from aiogram import types
from database import create_db_pool, create_db
import handlers
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    await create_db_pool()
    loop1 = asyncio.get_event_loop()
    loop1.create_task(check_users_periodically())
    loop1.create_task(send_notifications())
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Главное меню"),
    ])
   # insert code here to run it after start


async def on_shutdown(dp):
    logging.warning('Shutting down..')

   # insert code here to run it before shutdown
   # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()

   # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning('Bye!')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    # loop = asyncio.get_event_loop()
    # loop.create_task(create_db())
    # start_webhook(
    #     dispatcher=dp,
    #     webhook_path=WEBHOOK_PATH,
    #     on_startup=on_startup,
    #     on_shutdown=on_shutdown,
    #     skip_updates=False,
    #     host=WEBAPP_HOST,
    #     port=WEBAPP_PORT,
    # )
