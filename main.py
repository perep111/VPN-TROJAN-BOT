# from aiogram import executor
import logging
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from config import dp
import asyncio
from aiogram.utils.executor import start_webhook
from func import bot, WEBHOOK_URL, WEBHOOK_PATH
from func import WEBAPP_HOST, WEBAPP_PORT
from aiogram import types
from database import create_db_pool
import handlers
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    await create_db_pool()
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
    loop = asyncio.get_event_loop()
    # loop.create_task(check_users_periodically())
    # loop.create_task(create_db())
    # executor.start_polling(dp,
    #                        # on_startup=set_default_commands,
    #                        skip_updates=False)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
