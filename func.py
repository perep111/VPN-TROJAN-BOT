import asyncio
import subprocess
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
from database import fetch_data, read_to_db_user_id, check_users_vpn_service, write_password, is_user_in_db
from database import check_notifications
import hashlib
import random
import string


async def check_users_periodically():
    while True:
        await asyncio.sleep(60)
        await check_users_vpn_service()


main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
my_vpn_button = KeyboardButton(text='🔐 Мой VPN')
tarif_button = KeyboardButton(text='💸 Тарифы')
support_button = KeyboardButton(text='🤯 Поддержка')
instrukt_button = KeyboardButton(text='🎯 Как настроить VPN')
ref_button = KeyboardButton(text="💰 Реферальная программа")
main_menu.add(my_vpn_button, tarif_button, support_button)
main_menu.add(instrukt_button, ref_button)


pre_pay_keyboard_tro = InlineKeyboardMarkup(row_width=1)  # Можете указать другое значение row_width
connect_pay_button1 = InlineKeyboardButton(text='Оплата', callback_data='pre_pay_tro')
connect_pay_button2 = InlineKeyboardButton(text='Назад', callback_data='back')
pre_pay_keyboard_tro.add(connect_pay_button1,connect_pay_button2)

pre_pay_keyboard_wir = InlineKeyboardMarkup(row_width=1)  # Можете указать другое значение row_width
connect_pay_button3 = InlineKeyboardButton(text='Оплата', callback_data='pre_pay_wir')
pre_pay_keyboard_wir.add(connect_pay_button3,connect_pay_button2)


connect_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🩸 Подключить VPN Trojan:', callback_data="joy_trojan")],
        [InlineKeyboardButton(text='⏳ Пробный тариф Trojan:', callback_data='trial_tariff')],
        [InlineKeyboardButton(text='💧 Подключить протокол WireGuard', callback_data='joy_wireguard')]
    ]
)

extend_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='💵 Добавить еще месяц 110р', callback_data="pre_pay_tro")]
    ]
)

instrukt_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='⚙ Установить и настроить VPN', callback_data="instrukt")],
        [InlineKeyboardButton(text='💸 Продлить тариф / сменить протокол', callback_data="extend_tariff")]
    ]
)

device_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Apple iPhone/iPad', callback_data="Apple")],
        [InlineKeyboardButton(text='Android', callback_data="Android")]
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
                                    'посмотреть <a href="https://24perep.ru/">на нашем сайте</a>'
                               )
    except Exception as e:
        print(e)


async def send_quota(user_id, quota):
    user = f"{user_id}rac"

    password_hash = generate_password(15)
    fullhash = hashlib.sha224(password_hash.encode('utf-8')).hexdigest()

    await fetch_data(
        "INSERT INTO users (username, password, quota) VALUES ('{}', '{}', '{}')".format(user,
                                                                                         fullhash,
                                                                                         quota))
    url = f"trojan://{password_hash}@24perep.ru:8888?security=tls&sni=24perep.ru&alpn=http%2F1." \
          f"1%2Ch2%2Ch3&fp=firefox&type=tcp&headerType=none#{user}"
    await write_password(password_hash, user_id)

    await bot.send_message(chat_id=user_id,
                           text=f'ваша ссылка, просто нажмите на нее что бы скопировать:\n\n')
    await bot.send_message(chat_id=user_id, text=f'<code>{url}</code>', reply_markup=main_menu)

    asyncio.create_task(delayed_task(chat_id=user_id))


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
            await send_conf(user_id)
        else:
            await bot.send_message(chat_id='1348491834',text=f"Ошибка создания конф пользователя {user_id}")

    except subprocess.CalledProcessError as e:
        await bot.send_message(chat_id="1348491834", text=f"конкретная Ошибка создания конф: {e}")
        return False


async def send_conf(user_id):
    with open(f'/etc/wireguard/configs/vpn{str(user_id)}.conf', 'rb') as file:
        await bot.send_document(chat_id=user_id, document=file, caption="Ваш config", reply_markup=main_menu)


# Python
@dp.async_task
async def send_to_all_users(text, video_id=None, photo_id=None):
    users = await read_to_db_user_id()
    for user_id in users:
        try:
            if video_id:
                await bot.send_video(chat_id=user_id, video=video_id, caption=text, reply_markup=main_menu)
            elif photo_id:
                await bot.send_photo(chat_id=user_id, photo=photo_id, caption=text, reply_markup=main_menu)
            else:
                await bot.send_message(chat_id=user_id,
                                       text=text,
                                       reply_markup=main_menu)
            await asyncio.sleep(1)
        except Exception as e:
            await bot.send_message(chat_id='1348491834', text=f"Ошибка отправки сообщения: {user_id} - {e}")
            continue


async def send_video_from_file(chat_id, video, caption):
    # Открываем файл видео
    with open(video, 'rb') as video_file:
        await bot.send_video(chat_id=chat_id, video=video_file, caption=caption,
                             reply_markup=main_menu)


async def check_args(args, user_id: int):
    if args.isnumeric():
        if int(args) == user_id:
            args = '0'
            return args

        elif await is_user_in_db('trojan_users', args) or await is_user_in_db('users', args):
            return args
    else:
        args = '0'
        return args


async def send_notifications():
    while True:
        users_trojan = await check_notifications('trojan_users')
        users_wireguard = await check_notifications('users')
        try:

            for user in users_trojan:
                await bot.send_message(chat_id=user,
                                       text='❗️ЗАВТРА закончится ваш тариф протокола Trojan\n\n'
                                            '🌟 Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ,'
                                            ' не сгорят!\n\n'
                                            '<b>Не хочешь платить?\n'
                                            'Приведи друга и получи 2 недели VPN бесплатно</b> '
                                            'Нажми кнопку Реферальная программа и отправь полученную ссылку другу',
                                       reply_markup=connect_vpn)

            for user in users_wireguard:
                await bot.send_message(chat_id=user,
                                       text='❗️ЗАВТРА закончится ваш тариф протокола WireGuard\n\n'
                                            '🌟 Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ, не сгорят!\n\n'
                                            '🚀 Но лучше переходите но новый протокол Trojan, его невозможно '
                                            'заблокировать\n\n'
                                            '<b>Не хочешь платить?\n'
                                            'Приведи друга и получи 2 недели VPN бесплатно</b> '
                                            'Нажми кнопку Реферальная программа и отправь полученную ссылку другу',
                                       reply_markup=connect_vpn)
        except Exception as e:
            print(e)

        await asyncio.sleep(60)

