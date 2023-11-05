import asyncio
import subprocess
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
from database import fetch_data, read_to_db_user_id, check_users_vpn_service
import hashlib
import random
import string


async def check_users_periodically():
    while True:
        await asyncio.sleep(10)
        await check_users_vpn_service()


main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
my_vpn_button = KeyboardButton(text='🔐 Мой VPN')
tarif_button = KeyboardButton(text='💸 Тарифы')
support_button = KeyboardButton(text='🤯 Поддержка')
main_menu.add(my_vpn_button, tarif_button, support_button)


pre_pay_keyboard_tro = InlineKeyboardMarkup(row_width=1)  # Можете указать другое значение row_width
connect_pay_button1 = InlineKeyboardButton(text='Оплата', callback_data='pre_pay_tro')
connect_pay_button2 = InlineKeyboardButton(text='Назад', callback_data='back')
pre_pay_keyboard_tro.add(connect_pay_button1,connect_pay_button2)

pre_pay_keyboard_wir = InlineKeyboardMarkup(row_width=1)  # Можете указать другое значение row_width
connect_pay_button3 = InlineKeyboardButton(text='Оплата', callback_data='pre_pay_wir')
pre_pay_keyboard_wir.add(connect_pay_button3,connect_pay_button2)


connect_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='💵 Подключить VPN ☕Micro: 50 GB', callback_data="joy_trojan")],
        [InlineKeyboardButton(text='⏳ Подключить пробный тариф: 2 GB', callback_data='trial_tariff')],
        [InlineKeyboardButton(text='💰 Подключить протокол WireGuard', callback_data='joy_wireguard')]
    ]
)

extend_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='💵 Добавить еще месяц и 50GB: 100р', callback_data="pre_pay_tro")]
    ]
)

instrukt_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='⚙ Установить и настроить VPN', callback_data="instrukt")],
        [InlineKeyboardButton(text='💸 Продлить тариф / сменить протокол', callback_data="extend_tariff")]
    ]
)


def generate_password(length=15):
    characters = string.ascii_letters + string.digits  # буквы и цифры
    password = ''.join(random.choice(characters) for i in range(length))
    return password


async def delayed_task(chat_id):
    await asyncio.sleep(600)
    try:
        await bot.send_message(chat_id=chat_id,
                               text='если у вас возникли проблемы с подключением,\n'
                                    'напишите в поддержку @f_o_x_y_s\n\n'
                                    'Так же все актуальные новости можно \n'
                                    'посмотреть <a href="https://24perep.ru/news/">на нашем сайте</a>'
                               )
    except Exception as e:
        print(e)


async def send_quota(msg: types.Message, quota, pay_id=None):
    user = f"{msg.chat.id}rac"
    password_hash = generate_password(15)
    fullhash = hashlib.sha224(password_hash.encode('utf-8')).hexdigest()

    await fetch_data(
        "INSERT INTO users (username, password, quota) VALUES ('{}', '{}', '{}')".format(user,
                                                                                         fullhash,
                                                                                         quota))
    url = f"trojan://{password_hash}@24perep.ru:8888?security=tls&sni=24perep.ru&alpn=http%2F1.1%2Ch2%2Ch3&fp=firefox&type=tcp&headerType=none#{user}"

    if pay_id:
        await bot.send_message(chat_id=msg.chat.id, text=f'Платежный идентификатор\n'
                                                         f'{pay_id}')
    await bot.send_message(chat_id=msg.chat.id, text='ваша ссылка, просто кликните на нее что бы скопировать')
    await bot.send_message(chat_id=msg.chat.id, text=f'<code>{url}</code>', reply_markup=main_menu)

    asyncio.create_task(delayed_task(chat_id=msg.chat.id))


async def send_message_mi(user, text, name=None):
    if name:
        await bot.send_message(chat_id='1348491834', text=f"{text}: @{name} {user}")
    else:
        await bot.send_message(chat_id='1348491834', text=f"{text} {user}")


async def add_wireguard_user(user_id):
    try:
        # Формируем команду для добавления пользователя без указания имени
        command = 'pivpn add'

        # Запускаем процесс для выполнения команды
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Отправляем ввод нового имени пользователя в терминал
        process.communicate(input=f'vpn{user_id}\n'.encode())

        if process.returncode == 0:
            await bot.send_message(chat_id='1348491834',text="успешно добавлен")
        else:
            await bot.send_message(chat_id='1348491834',text=f"Ошибка создания конф пользователя {user_id}")

    except subprocess.CalledProcessError as e:
        await bot.send_message(chat_id="1348491834", text=f"конкретная Ошибка создания конф: {e}")
        return False


async def send_conf(user_id):
    with open(f'/home/vpn/configs/vpn{str(user_id)}.conf', 'rb') as file:
        await bot.send_document(chat_id=user_id, document=file, caption="Ваш config", reply_markup=main_menu)


async def send_to_all_users(text):
    users = await read_to_db_user_id()
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            await asyncio.sleep(6)
        except Exception as e:
            print(f'{e}-{user_id}')
            await asyncio.sleep(6)


async def send_video_from_file(chat_id):
    # Открываем файл видео
    with open('video/instr.mp4', 'rb') as video_file:
        await bot.send_video(chat_id=chat_id, video=video_file, caption='Вот инструкция по настройке VPN WireGuard',
                             reply_markup=main_menu)
