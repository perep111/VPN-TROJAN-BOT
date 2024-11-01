from functools import wraps
import logging
import asyncio
from aiogram.utils.exceptions import NetworkError, RetryAfter
from aiogram.utils.deep_linking import get_start_link
from config import dp, bot
from pay_conf import pay_conf_wireguard, pay_conf_trojan
from func import main_menu, connect_vpn, instrukt_kb, extend_vpn,send_message_link
from func import pre_pay_keyboard_tro, pre_pay_keyboard_wir, delayed_task, send_message_mi
from func import send_to_all_users, send_video_from_file, check_args, device_kb
from aiogram import types
from aiogram.types import ContentType
from database import is_test, count_refs, is_user_in_trojan
from database import fetch_data, update_users_db, read_to_db_end_date, is_user_in_db, write_to_db, is_user_in_wireguard
from admin import get_system_info
from aiogram.types import ParseMode
from marzban import backend

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

admin = [1348491834]


def admin_only(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        if message.from_user.id in admin:
            return await func(message, *args, **kwargs)
        else:
            try:
                # Проверяем наличие имени у пользователя
                user_name = message.from_user.username or "Имя отсутствует"

                # Формируем текст сообщения для пересылки
                forward_text = (
                    f"Сообщение от пользователя @{user_name} ID: {message.from_user.id}\n\n"
                    f"{message.text if message.text else 'Не текстовое сообщение'}"
                )

                # Пересылаем сообщение в ваш чат
                if message.text:
                    await bot.send_message(chat_id=1348491834, text=forward_text)
                else:
                    # Если сообщение не текстовое, пересылаем его как есть
                    await bot.send_message(chat_id=1348491834, text=forward_text)
                    await message.forward(chat_id=1348491834)

            except Exception as e:
                await message.reply(f"Ошибка при пересылке сообщения: {str(e)}")

    return wrapper


@dp.errors_handler()
async def error_handler(update, exception):
    if isinstance(exception, NetworkError):
        logging.error(f"NetworkError: {exception}")
        # Дополнительная обработка или уведомления об ошибке
        return True  # Отмечаем ошибку как обработанную

    elif isinstance(exception, RetryAfter):
        await asyncio.sleep(exception.timeout)
        return True  # Обработка завершена, можно продолжить выполнение

    else:
        logging.error(f'хз че за ошибка...{exception}')
        return True


@dp.message_handler(commands=['info'])
@admin_only
async def send_info(message: types.Message):
    system_info = await get_system_info()
    await message.answer(system_info, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['mess'])
@admin_only
async def send_mess_user(message: types.Message):
    args = message.get_args()

    try:
        # Разделяем аргументы на ID пользователя и текст сообщения
        user_id, text_message = args.split(' ', 1)

        # Пробуем преобразовать ID пользователя в число
        user_id = int(user_id)

        # Отправляем сообщение пользователю
        await bot.send_message(chat_id=user_id, text=text_message)
        await message.reply(f"Сообщение отправлено пользователю с ID {user_id}.")
    except ValueError:
        await message.reply("Пожалуйста, укажите корректный ID пользователя и текст сообщения.")
    except Exception as e:
        await message.reply(f"Ошибка: {str(e)}")


@dp.message_handler(commands=['read'])
@admin_only
async def all_users(message: types.Message):
    text = message.get_args()
    await send_to_all_users(text)


# @dp.message_handler(content_types=types.ContentType.VIDEO)
# async def handle_video(message: types.Message):
#     video_id = message.video.file_id  # Получаем идентификатор видео
#     await bot.send_message(1348491834, f"ID вашего видео: {video_id}")


@dp.message_handler(content_types=types.ContentType.VIDEO)
@admin_only
async def handle_video(message: types.Message):

    # Обработка видео
    video = message.video  # Получаем видео из сообщения
    video_id = message.video.file_id  # Получаем идентификатор видео из сообщения
    caption = message.caption  # Получаем подпись к видео
    await send_to_all_users(caption, video_id=video_id)



# Python
@dp.message_handler(content_types=types.ContentType.PHOTO)
@admin_only
async def handle_photo(message: types.Message):
    # Обработка фото
    # Получаем фото из сообщения (последний элемент - наибольшее разрешение)
    photo = message.photo[-1]
    photo_id = photo.file_id  # Получаем идентификатор файла фото
    caption = message.caption  # Получаем подпись к фото
    await send_to_all_users(caption, photo_id=photo_id)


@dp.message_handler(commands=['start'])
async def process_start_command(msg: types.Message):
    user_id = msg.from_user.id

    referal_args = msg.get_args()  # /start 123123
    check_referal_args = await check_args(referal_args, msg.from_user.id)

    user_is_tj = await is_user_in_db('trojan_users', user_id)

    if not user_is_tj:

        await write_to_db(user_id=user_id, table_name='trojan_users', refer=check_referal_args)

        try:
            if check_referal_args and check_referal_args != '0':
                old_user_is_tj = await is_user_in_trojan(user_id=check_referal_args)

                if old_user_is_tj:
                    
                    await update_users_db(table_name='trojan_users', user_id=check_referal_args, days=15)
                    await bot.send_message(chat_id=check_referal_args,
                                           text='по вашей ссылке зарегистрировались\n\n'
                                                'Вам добавлено 15 дней\n\n'
                                                'нажмите Мой VPN, что бы узнать срок действия тарифа\n\n'
                                                'Нажимай Как настроить VPN и получи подробную инструкцию по установке')
                else:
                    # await send_quota(check_referal_args, quota=26843545600)

                    if not backend.get_user(check_referal_args):
                        link = backend.create_user(check_referal_args)
                        await send_message_link(check_referal_args, link['subscription_url'])

                    else:
                        backend.enable_user(check_referal_args)

                    if not await is_user_in_db(table_name='trojan_users', user_id=check_referal_args):
                        await write_to_db(table_name='trojan_users', user_id=check_referal_args, refer=None, is_vpn=1,
                                          days=15)
                    else:
                        await update_users_db(table_name='trojan_users', user_id=check_referal_args, days=15)

                    await bot.send_message(chat_id=check_referal_args,
                                           text='по вашей ссылке зарегистрировались\n\n'
                                                'Вам добавлено 15\n\n'
                                                'нажмите Мой VPN, что бы узнать срок действия тарифа\n\n'
                                                'Нажимай Как настроить VPN и получи подробную инструкцию по установке')

            await bot.send_message(chat_id=user_id, text='Вы воспользовались реферальной ссылкой')

        except Exception as a:
            log.error(f"Ошибка при обработке нажатия start: {a}")

    if user_id:
        await bot.send_message(chat_id=msg.chat.id,
                               text=' @free_VIP_VPN_bot работает везде! \n'
                                    ' Даже там, где VPN блокируют.\n\n'
                                    ' Мы используем самый современный и защищенный протокол WLESS,'
                                    ' который эффективно маскирует трафик под обычный и с легкостью'
                                    ' обходит любые системы глубокого анализа трафика.')
        await bot.send_message(chat_id=msg.chat.id,
                               text=' 🍀 у него есть пробный период, можно попробовать все его преимущества'
                                    ' совершенно бесплатно,\n\n'
                                    'Нажмите  <b>Мой VPN</b> или <b>Тарифы</b> в меню внизу экрана и выберите для себя '
                                    ' подходящий тариф 🦞')
        await bot.send_message(chat_id=msg.chat.id,
                               text='<b>Не хочешь платить?\n'
                                    'Приведи друга и получи 2 недели VPN бесплатно</b> '
                                    'Нажми кнопку Реферальная программа и отправь полученную ссылку другу')
        await msg.answer_sticker(sticker='CAACAgIAAxkBAAEBgo9lL7p4rfT_TOJ25HtBsN-EtQ22YQACTQADWbv8JSiBoG3dG4L3MAQ')
        await bot.send_message(chat_id=msg.chat.id,
                               text='Встречайте лучший в мире VPN!', reply_markup=main_menu)

    else:
        await bot.send_message(chat_id=msg.chat.id,
                               text='Вам не получится пользоваться нашим сервисом\n'
                                    'т.к в вашем телеграм профиле нет user id')


@dp.message_handler(text='💰 Реферальная программа')
async def referal(mess: types.Message):
    ref_link = await get_start_link(payload=mess.from_user.id)
    count = await count_refs(mess.from_user.id)
    await mess.answer(f'У тебя  рефералов: {count}\n'
                      f'Твоя реферальная ссылка\n'
                      f'Просто нажми на нее что бы скопировать\n\n'
                      f'<code>{ref_link}</code>\n\n',
                      reply_markup=main_menu)


@dp.message_handler(text='💸 Тарифы')
async def mess_replay(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id,
                           text='☕ Тариф 30 дней VPN: 150р\n\n'
                                '🍄 Пробный тариф \n'
                                '(доступно один раз для каждого пользователя)\n\n',
                           reply_markup=connect_vpn)


@dp.message_handler(text='🤯 Поддержка')
async def mess_replay(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id,
                           text='если возникли проблемы с подключением или с подпиской,\n'
                                'напишите разработчикам @f_o_x_y_s,\n'
                                'так же последние новости публикуются на '
                                '<a href="https://24perep.ru/">этом сайте</a>')


@dp.message_handler(text='🎯 Как настроить VPN')
async def mess_replay(msg: types.Message):
    if await is_user_in_trojan(user_id=msg.from_user.id):
        await bot.send_message(chat_id=msg.chat.id,
                               text='Это инструкция для подключения VPN\n\n'
                                    'Выберите, на какое устройство вы хотели бы установить VPN:',
                               reply_markup=device_kb)
    else:
        await bot.send_message(chat_id=msg.chat.id,
                               text='У вас нет активной подписки\n\n'
                                    'Нажмите Тарифы и выберите тариф',
                               reply_markup=main_menu)


@dp.callback_query_handler(text="Android")
async def send_instruct_an(call: types.CallbackQuery):
    await call.answer()
    await bot.send_message(chat_id=call.from_user.id,
                           text='Инструкция для v2rayNG (Android)\n\n'
                                '1️⃣ Cкопировать ключ ⬆\n'
                                ' ссылка выше"\n'
                                '2️⃣ Cкачать приложение '
                                '<a href="https://play.google.com/store/apps/details?id=com.v2ray.ang">'
                                ' v2rayNG </a>\n'
                                '3️⃣ Cмотреть видео как добавить ключ',
                           reply_markup=main_menu,
                           disable_web_page_preview=True)
    await bot.send_video(call.message.chat.id, 
                         video="BAACAgIAAxkBAAIvH2bA3pSSY1cwFUMtbHq_nKIalsFGAAI-WQAC_EwJSq5j62W85yGJNQQ", 
                         caption='Вот инструкция по настройке VPN')
    


@dp.callback_query_handler(text="Apple")
async def send_instruct_ap(call: types.CallbackQuery):
    await call.answer()
    await bot.send_message(chat_id=call.from_user.id,
                           text='Инструкция для Streisand (Apple)\n\n'
                                '1️⃣ Cкопировать ключ ⬆ \n'
                                'ссылка выше"\n'
                                '2️⃣ Cкачать приложение '
                                '<a href="https://apps.apple.com/ru/app/streisand/id6450534064">'
                                ' Streisand </a>\n'
                                '3️⃣ Cмотреть видео как добавить ключ',
                           reply_markup=main_menu,
                           disable_web_page_preview=True)
    await bot.send_video(call.message.chat.id, 
                         video="BAACAgIAAxkBAAIukmbAhl8a4BUUlxQb5DyHUIUPOEGrAAJxVAAC_EwJSgcI0cStgyJmNQQ", 
                         caption='Вот инструкция по настройке VPN')
    


@dp.message_handler(text='🔐 Мой VPN')
async def get_data(msg: types.Message):

    wireguard_is = await is_user_in_wireguard(user_id=msg.from_user.id)
    trojan_is = await is_user_in_trojan(user_id=msg.from_user.id)

    # Теперь вы можете обработать результат и отправить его в чат
    # Проверьте, что result не пустой
    if trojan_is and wireguard_is:

        date_to_tro = await read_to_db_end_date(user_id=msg.from_user.id, table_name='trojan_users')
        date_to_wire = await read_to_db_end_date(user_id=msg.from_user.id, table_name='users')
        if date_to_wire is None or len(date_to_wire) < 0:
            date_to_wire = ['Ты какой то читер',]
        if date_to_tro is None or len(date_to_tro) < 0:
            date_to_tro = ['Ты какой то читер конкретный',]

        await bot.send_message(chat_id=msg.chat.id,
                               text=f'🌟 Ваш тариф:\n'
                                    f'🟢 активен до: {date_to_tro[0]}\n\n'
                                    f'📲 так же у вас подключен WireGuard \n'
                                    f'🟢 активен до {date_to_wire[0]}\n\n'
                                    f'⚠️Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ, не сгорят\n'
                                    f'Продлить тариф: ',
                               reply_markup=instrukt_kb)

    elif trojan_is:

        date_do = await read_to_db_end_date(user_id=msg.from_user.id, table_name='trojan_users')
        if date_do is None or len(date_do) < 0:
            date_do = ['Ты какой то читерhhh',]

        await bot.send_message(chat_id=msg.chat.id,
                               text=f'🌟 Ваш тариф:\n'
                                    f'🟢 активен до: {date_do[0]}\n\n'
                                    f'⚠️Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ, не сгорят\n'
                                    f'Продлить тариф: ',
                               reply_markup=instrukt_kb)

    elif wireguard_is:
        date_to_wire = await read_to_db_end_date(user_id=msg.from_user.id, table_name='users')
        if date_to_wire is None or len(date_to_wire) < 0:
            date_to_wire = ['Ты какой то читер',]

        await bot.send_message(chat_id=msg.chat.id,
                               text=f'У вас активен WireGuard до {date_to_wire[0]}\n\n'
                                    f'Переходите на новый тариф, который не боится блокировок.\n\n'
                                    f'⚠️Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ, не сгорят\n'
                                    f'Продлить тариф: ',
                               reply_markup=instrukt_kb)

    else:

        await bot.send_message(chat_id=msg.chat.id,
                               text='У вас нет активных подписок\n\n'
                                    'Выберите протокол и пользуйтесь VPN без остановки'
                                    '👉 Наш VPN работает везде! Даже там, где VPN блокируют. '
                                    'Мы используем самый современный и защищенный протокол VLESS\n\n'
                                    '⏳ Подключите пробный тариф и оцените качество нового протокола\n\n'
                                    'красная 🩸 или синяя 💧??',
                               reply_markup=connect_vpn)


@dp.callback_query_handler(text='trial_tariff')
async def trial_tariff(call: types.CallbackQuery):
    await call.answer()
    data_test = await is_test(user_id=call.from_user.id, tale_name='trojan_users')
    data_trojan = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(f"{call.from_user.id}rac", ))
    data_VLESS = backend.get_user(call.from_user.id)

    if not data_test and not data_trojan and not data_VLESS:
        if await is_user_in_db(table_name='trojan_users', user_id=call.from_user.id):
            await update_users_db(table_name='trojan_users', user_id=call.from_user.id, days=3, test=1)

        else:
            await write_to_db(user_id=call.from_user.id, is_vpn=1, table_name='trojan_users', refer=0, days=3, test=1)

        link = backend.create_user(call.from_user.id)

        if link is None:
            log.info(f'линк: для юзера {call.message.chat.id} == None')
            await bot.send_message(call.message.chat.id, 'возннникла ошибка с созданием профиля\n'
                                   'обратитесь в поддержку @f_o_x_y_s')
            await bot.send_message(chat_id='1348491834', text=f'ошибка тестовой ссылки для {call.message.chat.id}')

        else:    
            await send_message_link(call.message.chat.id, link['subscription_url'])  

            await bot.send_message(chat_id=call.message.chat.id,
                                text='Вам доступно 3 дня VPN'
                                        ' нажмите Мой VPN, что бы узнать срок действия тарифа\n\n'
                                        'Нажимай Как настроить VPN и получи подробную инструкцию по установке',
                                reply_markup=main_menu)
            await send_message_mi(user=call.from_user.id, text='подключил Пробный VPN', name=call.from_user.username)

    else:

        await bot.send_message(chat_id=call.from_user.id,
                               text='🥹 К сожалению пробный тариф доступен только новым пользователям',
                               reply_markup=main_menu)


@dp.callback_query_handler(text="extend_tariff")
async def extend_tariff(call: types.CallbackQuery):
    await call.answer()
    user = f"{call.from_user.id}rac"
    data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user, ))
    data_VLESS = backend.get_user(call.from_user.id)
    wireguard_is = await is_user_in_wireguard(user_id=call.from_user.id)

    if data or data_VLESS and wireguard_is:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='🎲 Отлично что вы пробуете новый протокол, '
                                    'Можете добавить еще месяц протокола 🥇WLESS\n\n'
                                    'или оставайтесь с WireGuard\n'
                                    'Но я предупреждал о возможных блокировках🙄',
                               reply_markup=connect_vpn)

    elif data:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='☕ Добавить еще месяц: 150р\n',
                               reply_markup=extend_vpn)

    else:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='<b>Внимание, протокол Wireguard больше нельзя купить,'
                                    'рекомендую перейти но новый протокол VLESS</b>')
        await bot.send_message(chat_id=call.message.chat.id,
                               text='🦞 Переходите на новый протокол WLESS, '
                                    'пробуйте тестовый период бесплатно\n\n',
                               reply_markup=connect_vpn)



@dp.callback_query_handler(text="instrukt")
async def cancellation(call: types.CallbackQuery):
    await call.answer()
    if await is_user_in_trojan(call.from_user.id):
        await bot.send_message(chat_id=call.message.chat.id,
                               text='Это инструкция для подключения VPN\n\n'
                                    'Выберите, на какое устройство вы хотели бы установить VPN:',
                               reply_markup=device_kb)
    else:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='У вас нет активной подписки\n\n'
                                    'Нажмите Тарифы и выберите VPN или Пробный тариф',
                               reply_markup=main_menu)


@dp.callback_query_handler(text="joy_trojan")
async def pay_message(call: types.CallbackQuery):
    await call.answer()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='☕ VPN / 1 месяц\n\n'
                                     'При оплате на МЕСЯЦ:\n'
                                     '👉 150 рублей\n'
                                     'ℹ 5 руб. в день\n\n'
                                     '⚠️В любой момент вы можете перейти на любой другой тариф\n\n'
                                     'Сделайте выбор:',
                                reply_markup=pre_pay_keyboard_tro)


@dp.callback_query_handler(lambda c: c.data == 'back')
async def push_cancel(call: types.CallbackQuery):
    await call.answer()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='Вы отказались, мне <b>очень жаль</b>')


@dp.callback_query_handler(lambda c: c.data.startswith('pre_pay_'))
async def menu_message(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    if data == "pre_pay_tro":

        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text='👇🏻')
        await pay_conf_trojan(call.message.chat.id)

    elif data == "pre_pay_wir":

        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text='👇🏻')
        await pay_conf_wireguard(call.message.chat.id)


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(query: types.PreCheckoutQuery):
    # a = query.total_amount
    # await bot.send_message(chat_id=query.from_user.id, text=f'{a}')
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):

    name = message.from_user.username
    user_id = message.from_user.id
    pay_id = message.successful_payment.provider_payment_charge_id


    if message.successful_payment.invoice_payload == 'payment_trojan':
        # pay_id = message.successful_payment.provider_payment_charge_id
        await bot.send_message(message.from_user.id, 'Поздравляю с покупкой')
        # name = message.from_user.username

        data = backend.get_user(message.from_user.id)
        trojan_is = await is_user_in_db(table_name='trojan_users', user_id=message.from_user.id)

        if not data and not trojan_is:

            await bot.send_message(chat_id=message.chat.id,
                                   text=f'Платежный идентификатор\n'f'{pay_id}',
                                   reply_markup=main_menu)

            await write_to_db(table_name='trojan_users', user_id=user_id, refer=0, is_vpn=1, days=30, test=1)
            
            link = backend.create_user(user_id)

            if link is None:
                log.info(f'линк: для юзера {message.from_user.id} == None')
                await bot.send_message(message.from_user.id, 'возннникла ошибка с созданием профиля\n'
                                    'обратитесь в поддержку @f_o_x_y_s')
                
                await bot.send_message(chat_id='1348491834', text=f'ошибка оплаченой ссылки для {message.from_user.id}')
            else:    
                await send_message_link(message.from_user.id, link['subscription_url'])  

                await bot.send_message(chat_id=message.chat.id,
                                    text='Вам доступно 30 дней VPN нажмите Мой VPN, '
                                            'что бы узнать срок действия тарифа\n\n'
                                            'Нажимай Как настроить VPN и получи подробную инструкцию по установке',
                                    reply_markup=main_menu)
                await send_message_mi(user=user_id, text='Купил Trojan', name=name)

        elif data and trojan_is:

            backend.enable_user(user_id)


            await bot.send_message(chat_id=message.chat.id,
                                   text='Вам добавлено еще 30 дней нажмите Мой VPN, '
                                        'что бы узнать срок действия тарифа',
                                   reply_markup=main_menu)

            await bot.send_message(chat_id=message.chat.id,
                                   text=f'Платежный идентификатор\n'f'{pay_id}',
                                   reply_markup=main_menu)
            
            await send_message_link(message.from_user.id, data['subscription_url'])

            await update_users_db(table_name='trojan_users', user_id=user_id, days=30)
            await send_message_mi(user=user_id, text='Добавил 30 дней VLESS', name=name)

        elif trojan_is and not data:

            link = backend.create_user(user_id)

            if link is None:
                log.info(f'линк: для юзера {message.from_user.id} == None')
                await bot.send_message(message.from_user.id, 'возннникла ошибка с созданием профиля\n'
                                    'обратитесь в поддержку @f_o_x_y_s')
                await bot.send_message(chat_id='1348491834', text=f'ошибка оплаченой ссылки для {message.from_user.id}')
            else:    
                await send_message_link(message.from_user.id, link['subscription_url'])  


                await update_users_db(table_name='trojan_users', user_id=user_id, days=30)
                await bot.send_message(chat_id=message.chat.id,
                                    text=f'Платежный идентификатор\n'f'{pay_id}',
                                    reply_markup=main_menu)
                await bot.send_message(chat_id=message.chat.id,
                                    text='Вам доступно еще 30 дней,'
                                            'нажмите Мой VPN, что бы узнать срок действия тарифа\n\n'
                                            'Нажимай Как настроить VPN и получи подробную инструкцию по установке',
                                    reply_markup=main_menu)
                await send_message_mi(user=user_id, text='Добавил 30 дней VLESS', name=name)

    elif message.successful_payment.invoice_payload == 'payment_wireguard':

        try:

            await update_users_db(table_name='users', user_id=user_id, days=30)
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'Платежный идентификатор\n'
                                        f'{pay_id}')
            await send_message_mi(user=user_id, text='оплатил WireGuard', name=name)

            asyncio.create_task(delayed_task(user_id))

        except Exception as e:
            await bot.send_message(chat_id='1348491834', text=f'ошибка оплаты для юзера {user_id}{str(e)}')
