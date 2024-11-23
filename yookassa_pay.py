import logging
from aiohttp import web
from config import bot
from ok_pay import saksefull_pay

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)



# Асинхронный обработчик вебхуков от Юкассы
async def yookassa_webhook_handler(request: web.Request):
    try:
        # Получаем JSON от Юкассы
        data = await request.json()

        # Логируем данные
        logging.info(f"Получен вебхук от Юкассы")

        # Обработка статуса оплаты
        event = data.get("event", "")
        if event == "payment.succeeded":
            # if payment_id and payment_id in PAYMENT_TRACKER:
            #     user_id = PAYMENT_TRACKER[payment_id]
            #     await bot.send_message(user_id, "Ваш платеж успешно завершен!")
            #     del PAYMENT_TRACKER[payment_id]

            metadata = data.get("object", {}).get("metadata", {})

            user_name = metadata.get("user_name")
            user_id = metadata.get("user_id")

            await bot.send_message(user_id, "Ваш платеж успешно завершен!")

            await saksefull_pay(user_id)

            # Здесь можно отправить сообщение администратору или обработать оплату
            await bot.send_message(
                chat_id="1348491834",
                text=f"Успешная оплата: {user_id}\n{user_name}",
            )
        return web.Response(status=200, text="OK")
    except Exception as e:
        logging.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(status=500, text="Internal Server Error")