from config import bot, TOKEN_UKASSA
from aiogram.types import LabeledPrice


def recept():
    receipt = {
        "items": [
            {
                "description": "Покупка цифрового контента",
                "quantity": "1",
                "amount": {"value": "150.00", "currency": "RUB"},
                "vat_code": 1
            }
        ]
        # "customer": {"email": "perep@24perep.ru"}
    }

    provider_data = {
        "receipt": receipt
    }
    return provider_data


async def pay_conf_wireguard(chat_id):
    await bot.send_invoice(chat_id=chat_id,
                           title='VPN WIREGUARD PROTOKOL',
                           description='Безграничные возможности, которые откроются со всеми '
                                       'запрещенными в РФ соцсетями',
                           payload='payment_wireguard',
                           provider_token=TOKEN_UKASSA,
                           currency='RUB',
                           start_parameter='vpn_bot',
                           need_email=True,
                           send_email_to_provider=True,
                           photo_url='https://d1xsi6mgo67kia.cloudfront.net/uploads/2022/03/VPN.jpg',
                           provider_data=recept(),
                           prices=[
                               LabeledPrice(
                                   label='Месячная подписка VPN',
                                   amount=160_00
                               ),
                               LabeledPrice(
                                   label='Скидка',
                                   amount=-10_00
                               )])


async def pay_conf_trojan(chat_id):
    await bot.send_invoice(chat_id=chat_id,
                           title='VPN PROTOKOL',
                           description='Безграничные возможности, которые откроются со всеми '
                                       'запрещенными в РФ соцсетями',
                           payload='payment_trojan',
                           provider_token=TOKEN_UKASSA,
                           currency='RUB',
                           start_parameter='vpn_bot',
                           need_email=True,
                           send_email_to_provider=True,
                           photo_url='https://d1xsi6mgo67kia.cloudfront.net/uploads/2022/03/VPN.jpg',
                           provider_data=recept(),
                           prices=[
                               LabeledPrice(
                                   label='Месячная подписка VPN',
                                   amount=160_00
                               ),
                               LabeledPrice(
                                   label='Скидка',
                                   amount=-10_00
                               )])
