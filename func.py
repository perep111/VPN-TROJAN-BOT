from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
import subprocess
import os
import random
import string
from yoomoney import Quickpay

from aiogram import Bot, Dispatcher, types


async def set_default_commands(dip):
    await dip.bot.set_my_commands([
        types.BotCommand("start", "Главное меню"),
    ])


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


# async def add_user(user, gb):
#
#     # Определите абсолютный путь к trojan_manager.py
#     trojan_manager_path = "/root/trojan-manager/trojan_manager.py"
#     password = generate_password()
#     # Создайте список команд, которые вы хотите выполнить
#     commands = [
#         f"Adduser {user} {password}",
#         f"Setquota {user} {gb}"
#     ]
#     try:
#
#         # Запустите интерактивное приложение Trojan Manager и выполните команды
#         child = subprocess.Popen(["python3", trojan_manager_path, "int"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
#                                  stderr=subprocess.PIPE)
#         child.stdin.write(b'\n')  # Добавьте символ новой строки для ожидания ввода
#         child.stdin.flush()
#
#         for command in commands:
#             child.stdin.write(command.encode('utf-8') + b'\n')
#             child.stdin.flush()
#
#         child.stdin.close()
#         child.wait()
#
#     except subprocess.CalledProcessError as e:
#         await bot.send_message(chat_id="1348491834", text=f"конкретная Ошибка создания конф: {e}")
#         return False
#
#     return password
#
#
