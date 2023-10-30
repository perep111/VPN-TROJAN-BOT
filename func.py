from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
import asyncio
import random
import string
from yoomoney import Quickpay
from aiogram.dispatcher import FSMContext

from aiogram import types


# async def set_default_commands(dip):
#     await dip.bot.set_my_commands([
#         types.BotCommand("start", "Главное меню"),
#     ])


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


def pay(comment):
    quickpay = Quickpay(
                receiver="4100118220335308",
                quickpay_form="shop",
                targets="Sponsor this project",
                paymentType="AC",
                successURL='https://t.me/free_VIP_VPN_bot',
                sum=2,
                label=comment
                )

    return quickpay


def kb_func(password):
    keyboard = InlineKeyboardMarkup()
    btn_payment = InlineKeyboardButton('Оплатить', callback_data='payment', url=pay(comment=password).redirected_url)
    btn_cancel = InlineKeyboardButton('Отмена', callback_data='back')
    verification = InlineKeyboardButton('ПРОВЕРКА_ОПЛАТЫ', callback_data='verification')
    keyboard.add(btn_payment, btn_cancel)
    keyboard.row(verification)
    return keyboard


def generate_password(length=15):
    characters = string.ascii_letters + string.digits  # буквы и цифры
    password = ''.join(random.choice(characters) for i in range(length))
    return password


async def set_message_deletion_timer(chay_id, mes_id, state: FSMContext):
    await asyncio.sleep(600)  # Подождать 30 минут (1800 секунд)

    # Получить состояние пользователя
    user_state = await state.get_state()

    if user_state == "UserState:PROCESS_ORDER":
        try:
            # Если пользователь все еще находится в состоянии "PROCESS_ORDER", удалите сообщение
            await bot.edit_message_text(chat_id=chay_id,
                                        message_id=mes_id,
                                        text='Ссылка на оплату устарела',
                                        reply_markup=connect_vpn)
            await state.finish()  # Завершите состояние
        except Exception as e:
            print(e)

