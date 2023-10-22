from aiogram import executor
import logging
from config import dp
import asyncio
from func import set_default_commands
import handlers
logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # loop.create_task(check_users_periodically())
    # loop.create_task(create_db())
    executor.start_polling(dp,
                           on_startup=set_default_commands,
                           skip_updates=False)
