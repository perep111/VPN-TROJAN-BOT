import asyncio
import os
import random
import string
import yookassa
from yookassa import Payment
import uuid
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
from database import read_to_db_user_id, check_users_vpn_service, is_user_in_db
from database import check_notifications
from marzban import backend
from dotenv import load_dotenv

load_dotenv()

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

yookassa.Configuration.secret_key = os.getenv('SECRET_KEY')
yookassa.Configuration.account_id = os.getenv('ACCOUNT_ID')


def generate_random_email():
    # Генерируем случайную строку для имени пользователя
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    # Доменное имя фиксированное
    domain = "mail.ru"
    # Собираем email
    return f"{username}@{domain}"


def recept():
    receipt = {
        "items": [
            {
                "description": "Покупка цифрового контента",
                "quantity": "1",
                "amount": {"value": "150.00", "currency": "RUB"},
                "vat_code": 1
            }
        ],
         "customer": {"email": generate_random_email()}
    }

    return receipt


def create_payment(user_id, user_name="Без имени"):
    id_key = str(uuid.uuid4())
    payment = Payment.create({
        "amount": {
            "value": "150.00",
            "currency": "RUB"
        },
        "receipt": recept(),
        "payment_method_data": {
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/free_VIP_VPN_bot"
        },
        "capture": True,
        "metadata": {
            "user_id": user_id,
            "user_name": user_name,
        },
        "description": "описание..."
    }, id_key)

    
    return payment.confirmation.confirmation_url

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


connect_vpn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🩸 Подключить VPN:',
                              callback_data="joy_trojan")],
        [InlineKeyboardButton(text='⏳ Пробный тариф:',
                              callback_data='trial_tariff')],
    ]
)


instrukt_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text='⚙ Установить и настроить VPN', callback_data="instrukt")],
        [InlineKeyboardButton(
            text='💸 Продлить тариф / сменить протокол', callback_data="extend_tariff")]
    ]
)

device_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Apple iPhone/iPad',
                              callback_data="Apple")],
        [InlineKeyboardButton(text='Android', callback_data="Android")]
    ]
)

def pay_inlane(chat_id, user_name=None):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Оплата:',
                                url=create_payment(chat_id, user_name=user_name))],
            [InlineKeyboardButton(text='Отмена оплаты', callback_data="back")]
        ]
    )
    return kb

async def delayed_task(chat_id):
    await asyncio.sleep(600)
    try:
        await bot.send_message(chat_id=chat_id,
                               text='если у вас возникли проблемы с подключением,\n'
                                    'напишите в поддержку @f_o_x_y_s'
                               )
    except Exception as e:
        logger.warning(f'Ошибка delayed_task : {e}')
        await bot.send_message(chat_id='1348491834', text=f'Ошибка delayed_task : {e}')


async def send_message_link(user, link):

    await bot.send_message(chat_id=user,
                           text=f'Ваша ссылка для подключения:\n\n'
                           f'{link}\n\n'
                           f'нажмите на нее или откройте в браузере,'
                           f'вы увидете информацию о своем тарифе и способах подключения\n\n'
                           f'или копируйте ее и вставьте в приложение')


async def send_message_mi(user, text, name=None):
    if name:
        await bot.send_message(chat_id='1348491834', text=f"{text}: @{name} {user}")
    else:
        await bot.send_message(chat_id='1348491834', text=f"{text} {user}")


async def send_conf(user_id):
    with open(f'/etc/wireguard/configs/vpn{str(user_id)}.conf', 'rb') as file:
        await bot.send_document(chat_id=user_id, document=file, caption="Ваш config", reply_markup=main_menu)


# Python
@dp.async_task
async def send_to_all_users(text, video_id=None, photo_id=None):
    users = await read_to_db_user_id()

    count_err = 0
    count_mess = 0

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
            count_mess += 1

        except Exception as e:
            logger.error(f'Ошибка отправки сообщения: {user_id} - {e}')
            count_err += 1
            continue

    await bot.send_message(chat_id='1348491834', text=f"Сообщений доставлено: {count_mess}\n\nОшибок отправки: {count_err}")


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
        try:

            for user in users_trojan:
                await bot.send_message(chat_id=user,
                                       text='❗️ЗАВТРА закончится ваш тариф\n\n'
                                            '🌟 Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ,'
                                            ' не сгорят!\n\n'
                                            '<b>Не хочешь платить?\n'
                                            'Приведи друга и получи 2 недели VPN бесплатно</b> '
                                            'Нажми кнопку Реферальная программа и отправь полученную ссылку другу',
                                       reply_markup=connect_vpn)

        except Exception as e:
            print(e)

        await asyncio.sleep(60)
