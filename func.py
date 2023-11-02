import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from config import *
import random
import string


def recept():
    receipt = {
        "items": [
            {
                "description": "Покупка цифрового контента",
                "quantity": "1",
                "amount": {"value": "100.00", "currency": "RUB"},
                "vat_code": 1
            }
        ]
        # "customer": {"email": "perep@24perep.ru"}
    }

    provider_data = {
        "receipt": receipt
    }
    return provider_data


main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
my_vpn_button = KeyboardButton(text='🔐 Мой VPN')
tarif_button = KeyboardButton(text='💸 Тарифы')
support_button = KeyboardButton(text='🤯 Поддержка')
main_menu.add(my_vpn_button, tarif_button, support_button)


pre_pay_keyboard = InlineKeyboardMarkup(row_width=1)  # Можете указать другое значение row_width
connect_pay_button1 = InlineKeyboardButton(text='Оплата', callback_data='pre_pay')
connect_pay_button2 = InlineKeyboardButton(text='Назад', callback_data='back')
pre_pay_keyboard.add(connect_pay_button1,connect_pay_button2)


connect_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Подключить VPN ☕Micro: 50 GB', callback_data="pay")],
    ]
)

instrukt_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='⚙ Установить и настроить VPN', callback_data="instrukt")],
        [InlineKeyboardButton(text='💸 Продлить тариф', callback_data="Extend_tariff")]
    ]
)


def generate_password(length=15):
    characters = string.ascii_letters + string.digits  # буквы и цифры
    password = ''.join(random.choice(characters) for i in range(length))
    return password


async def pay_conf(chat_id):
    await bot.send_invoice(chat_id=chat_id,
                           title='VPN',
                           description='Безграничные возможности, которые откроются со всеми '
                                       'запрещенными в РФ соцсетями',
                           payload='payment',
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
                                   amount=150_00
                               ),
                               LabeledPrice(
                                   label='Скидка',
                                   amount=-50_00
                               )])


async def delayed_task(user_id):
    await asyncio.sleep(10)
    try:
        await bot.send_message(chat_id=user_id, text='если у вас возникли проблемы с подключением,\n'
                                                     'напишите в поддержку @f_o_x_y_s')
    except Exception as e:
        print(e)
