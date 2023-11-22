import logging
import asyncio
from aiogram.utils.exceptions import NetworkError, RetryAfter
from aiogram.utils.deep_linking import get_start_link
from config import dp, bot
from pay_conf import pay_conf_wireguard, pay_conf_trojan
from func import main_menu, connect_vpn, instrukt_kb, extend_vpn
from func import pre_pay_keyboard_tro, pre_pay_keyboard_wir, delayed_task, send_quota, send_message_mi, send_conf
from func import add_wireguard_user, send_to_all_users, send_video_from_file, check_args
from aiogram import types
from aiogram.types import ContentType
from database import is_test, count_refs
from database import fetch_data, update_users_db, read_to_db_end_date, is_user_in_db, write_to_db, is_user_in_wireguard
from admin import get_system_info
from aiogram.types import ParseMode

admin = [1348491834]


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
        print(f'хз че за ошибка...{exception}')
        return True


@dp.message_handler(commands=['info'])
async def send_info(message: types.Message):
    if message.from_user.id in admin:
        system_info = await get_system_info()
        await message.answer(system_info, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer('соси')


# @dp.message_handler(commands=['st'])
# async def process_start_command(msg: types.Message):
#     url = '<code>trojan://sq2nmm93McA7BSa@24perep.ru:' \
#           '8888?security=tls&sni=24perep.ru&alpn=http%2F1.' \
#           '1%2Ch2%2Ch3&fp=firefox&type=tcp&headerType=none#1348491834rac</code>'
#     await bot.send_photo(chat_id=msg.chat.id,
#                          photo=f'https://api.qrserver.com/v1/create-qr-code/?size=800x800&data={url}',
#                          caption=f'ваша ссылка, просто нажмите на нее что бы скопировать:\n\n'
#                                  '⚠️Это ваша личная ссылка, не давайте ее никому, если не хотите поделиться'
#                                  ' своим трафиком.\n\n'
#                                  'Для подключения <b>на другом устройстве можете использовать этот QR-код на '
#                                  'следующем шаге</b>. Ваша ссылка и QR-код подходят для подключения неограниченного '
#                                  'количества устройств. Каждое подключенное устройство будет расходовать ваш трафик.')
#     await bot.send_message(chat_id=msg.chat.id, text=url)


@dp.message_handler(commands=['read'])
async def all_users(message: types.Message):
    if message.from_user.id in admin:
        text = message.get_args()
        await send_to_all_users(text)
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")


@dp.message_handler(commands=['start'])
async def process_start_command(msg: types.Message):
    user_id = msg.from_user.id

    referal_args = msg.get_args()  # /start 123123
    check_referal_args = await check_args(referal_args, msg.from_user.id)

    user_is_wg = await is_user_in_db('users', user_id)
    user_is_tj = await is_user_in_db('trojan_users', user_id)

    if not user_is_wg and not user_is_tj:
        await write_to_db(user_id=user_id, table_name='users', refer=check_referal_args)
        await write_to_db(user_id=user_id, table_name='trojan_users', refer=check_referal_args)
        try:
            if check_referal_args and check_referal_args != '0':
                old_user_is_wg = await is_user_in_wireguard(user_id=check_referal_args)
                old_user_is_tj = await fetch_data(
                    "SELECT * FROM users WHERE username = '{}'".format(f"{check_referal_args}rac",))

                if old_user_is_wg and not old_user_is_tj:
                    await update_users_db(table_name='users', user_id=check_referal_args, days=15)
                    await bot.send_message(chat_id=check_referal_args,
                                           text='по вашей ссылке зарегистрировались\n\n'
                                                'Вам добавлено 15 дней')
                elif old_user_is_tj:
                    await fetch_data(
                        "UPDATE users SET quota = quota + {} WHERE username = '{}'".format('26843545600',
                                                                                           f"{check_referal_args}rac"))
                    await update_users_db(table_name='trojan_users', user_id=check_referal_args, days=15)
                    await bot.send_message(chat_id=check_referal_args,
                                           text='по вашей ссылке зарегистрировались\n\n'
                                                'Вам добавлено 15 дней и 25GB протокола trojan')
                elif not old_user_is_tj and not old_user_is_wg:

                    await send_quota(check_referal_args, quota=26843545600)
                    if not await is_user_in_db(table_name='trojan_users', user_id=check_referal_args):
                        await write_to_db(table_name='trojan_users', user_id=check_referal_args, refer=None, is_vpn=1,
                                          days=15)
                    else:
                        await update_users_db(table_name='trojan_users', user_id=check_referal_args, days=15)
                    await bot.send_message(chat_id=check_referal_args,
                                           text='по вашей ссылке зарегистрировались\n\n'
                                                'Вам добавлено 15 дней и 25GB')

            await bot.send_message(chat_id=user_id, text='Вы воспользовались реферальной ссылкой')

        except Exception as a:
            print(a)
    #
    # elif not user_is_tj and user_is_wg:
    #     await write_to_db(user_id=user_id, table_name='trojan_users', refer=check_referal_args)
    #     bot.send_message(chat_id=check_referal_args,
    #                      text='по вашей ссылке зарегестрировались')
    #
    # elif not user_is_wg and user_is_tj:
    #     await write_to_db(user_id=user_id, table_name='users', refer=check_referal_args)
    #     bot.send_message(chat_id=check_referal_args,
    #                      text='по вашей ссылке зарегестрировались')

    if user_id:
        await bot.send_message(chat_id=msg.chat.id,
                               text=' @free_VIP_VPN_bot работает везде! \n'
                                    ' Даже там, где VPN блокируют.\n\n'
                                    ' Мы используем самый современный и защищенный протокол Trojan,'
                                    ' который эффективно маскирует трафик под обычный и с легкостью'
                                    ' обходит любые системы глубокого анализа трафика.')
        await bot.send_message(chat_id=msg.chat.id,
                               text=' 🍀 у него есть пробный период, можно попробовать все его преимущества'
                                    ' совершенно бесплатно,'
                                    ' но установка и настройка немного сложнее чем у Wireguard\n\n'
                                    ' 🍁 Протокол WireGuard еще поддерживается и доступен для установки,'
                                    ' но я настоятельно рекомендую перейти на новый протокол trojan\n\n'
                                    'Нажмите  <b>Мой VPN</b> или <b>Тарифы</b> в меню внизу экрана и выберите для себя '
                                    ' подходящий протокол 🦞')
        await msg.answer_sticker(sticker='CAACAgIAAxkBAAEBgo9lL7p4rfT_TOJ25HtBsN-EtQ22YQACTQADWbv8JSiBoG3dG4L3MAQ')
        await bot.send_message(chat_id=msg.chat.id,
                               text='Встречайте лучший в мире VPN!', reply_markup=main_menu)

    else:
        await bot.send_message(chat_id=msg.chat.id,
                               text='Вам не получится пользоваться нашим сервисом\n'
                                    'т.к в вашем телеграм профиле нет user id')


@dp.message_handler(commands=['ref'])
async def refferal(mess: types.Message):
    ref_link = await get_start_link(payload=mess.from_user.id)
    count = await count_refs(mess.from_user.id)
    await mess.answer(f'У тебя  рефералов: {count}\n'
                      f'Твоя реферальная ссылка\n'
                      f'<code>{ref_link}</code>')


@dp.message_handler(text='💸 Тарифы')
async def mess_replay(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id,
                           text='☕ Тариф протокола trojan: 100р 50GB\n'
                                'неограниченное количество пользователей. '
                                'Вы платите только за трафик\n\n'
                                '🍄 Пробный тариф протокола trojan\n'
                                '(доступно 2GB, один раз для каждого пользователя)\n\n'
                                '🤟 Тариф протокола WireGuard: 100р\n\n'
                                'безлимитный трафик, одно устройство\n'
                                '(могут быть блокировки со стороны вашего провайдера)',
                           reply_markup=connect_vpn)


@dp.message_handler(text='🤯 Поддержка')
async def mess_replay(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id,
                           text='если возникли проблемы с подключением или с подпиской,\n'
                                'напишите разработчикам @f_o_x_y_s,\n'
                                'так же последние новости публикуются на '
                                '<a href="https://24perep.ru/news/">этом сайте</a>')


@dp.message_handler(text='🔐 Мой VPN')
async def get_data(msg: types.Message):
    user = f"{msg.from_user.id}rac"
    data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user,))
    wireguard_is = await is_user_in_wireguard(user_id=msg.from_user.id)

    # Теперь вы можете обработать результат и отправить его в чат
    # Проверьте, что result не пустой
    if data and wireguard_is:
        quota = data[0]['quota']
        download_value = data[0]['download']
        upload_value = data[0]['upload']
        a = round(((quota - (download_value + upload_value)) / 1073741824), 2)
        date_to_tro = await read_to_db_end_date(user_id=msg.from_user.id, table_name='trojan_users')
        date_to_wire = await read_to_db_end_date(user_id=msg.from_user.id, table_name='users')
        if date_to_wire is None or len(date_to_wire) < 0:
            date_to_wire = ['Ты какой то читер',]
        if date_to_tro is None or len(date_to_tro) < 0:
            date_to_tro = ['Ты какой то читер конкретныцй',]

        await bot.send_message(chat_id=msg.chat.id,
                               text=f'🌟 Ваш тариф ☕️ Micro: 50 GB\n'
                                    f'🚀 остаток трафика = {a}GB\n'
                                    f'🟢 активен до: {date_to_tro[0]}\n\n'
                                    f'📲 так же у вас подключен WireGuard \n'
                                    f'🟢 активен до {date_to_wire[0]}\n\n'
                                    f'ℹ Вы можете установить и настроить VPN на неограниченное количество устройств,'
                                    f' все они будут расходовать ваш трафик.\n\n'
                                    f'⚠️Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ, не сгорят\n'
                                    f'Добавить еще трафик: ',
                               reply_markup=instrukt_kb)

    elif data:
        quota = data[0]['quota']
        download_value = data[0]['download']
        upload_value = data[0]['upload']
        a = round(((quota - (download_value + upload_value)) / 1073741824), 2)
        date_do = await read_to_db_end_date(user_id=msg.from_user.id, table_name='trojan_users')
        if date_do is None or len(date_do) < 0:
            date_do = ['Ты какой то читерhhh',]

        await bot.send_message(chat_id=msg.chat.id,
                               text=f'🌟 Ваш тариф ☕ Micro: 50 GB\n'
                                    f'🚀 остаток трафика = {a}GB\n'
                                    f'🟢 активен до: {date_do[0]}\n\n'
                                    f'ℹ Вы можете установить и настроить VPN на неограниченное количество устройств,'
                                    f' все они будут расходовать ваш трафик.\n\n'
                                    f'⚠️Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ, не сгорят'
                                    f'Добавить еще трафик: ',
                               reply_markup=instrukt_kb)

    elif wireguard_is:
        date_to_wire = await read_to_db_end_date(user_id=msg.from_user.id, table_name='users')
        if date_to_wire is None or len(date_to_wire) < 0:
            date_to_wire = ['Ты какой то читер',]

        await bot.send_message(chat_id=msg.chat.id,
                               text=f'У вас активен WireGuard до {date_to_wire[0]}\n\n'
                                    f'Переходите на новый протокол trojan, который не боится блокировок.\n\n'
                                    f'⚠️Продлевайте тариф заранее, оставшиеся дни ДОБАВЯТСЯ, не сгорят\n'
                                    f'Добавить еще трафик: ',
                               reply_markup=instrukt_kb)

    else:

        await bot.send_message(chat_id=msg.chat.id,
                               text='👉 Тарифы протокола trojan рассчитаны на неограниченное количество устройств.'
                                    ' Вы платите только за трафик\n\n'
                                    '☕ 50 GB протокола trojan - должно хватить для 1 устройства с '
                                    'умеренной активностью в соц.'
                                    ' сетях\n\n'
                                    '⏳ Подключите пробный тариф и оцените качество нового протокола\n\n'
                                    '🤟 Или воспользуйтесь протоколом WireGuard\n'
                                    ' безлимитный трафик, но только на одно устройство\n\n'
                                    '💰 Первые 10 дней бесплатно\n'
                                    ' """Возможны блокировки со стороны вашего провайдера"""\n\n'
                                    'Выбор за тобой: \n'
                                    'красная 🩸 или синяя 💧??',
                               reply_markup=connect_vpn)


@dp.callback_query_handler(text='trial_tariff')
async def trial_tariff(call: types.CallbackQuery):
    await call.answer()
    data_test = await is_test(user_id=call.from_user.id, tale_name='trojan_users')
    data_trojan = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(f"{call.from_user.id}rac", ))

    if not data_test and not data_trojan:
        if await is_user_in_db(table_name='trojan_users', user_id=call.from_user.id):
            await update_users_db(table_name='trojan_users', user_id=call.from_user.id, days=7, test=1)

        else:
            await write_to_db(user_id=call.from_user.id, table_name='trojan_users', refer=0, days=7, test=1)

        await send_quota(user_id=call.from_user.id, quota='2147483648')

        await bot.send_message(chat_id=call.message.chat.id,
                               text='Вам доступно 2GB нажмите Мой VPN, что бы узнать остаток своего трафика',
                               reply_markup=main_menu)

    else:

        await bot.send_message(chat_id=call.from_user.id,
                               text='🥹 К сожалению пробный тариф доступен только новым пользователям протокола trojan',
                               reply_markup=main_menu)


@dp.callback_query_handler(text="extend_tariff")
async def extend_tariff(call: types.CallbackQuery):
    await call.answer()
    user = f"{call.from_user.id}rac"
    data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user, ))
    wireguard_is = await is_user_in_wireguard(user_id=call.from_user.id)

    if data and wireguard_is:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='🎲 Отлично что вы пробуете новый протокол, '
                                    'Можете добавить еще месяц и 50GB протокола 🥇trojan\n\n'
                                    'или оставайтесь с WireGuard\n'
                                    'Но я предупреждал о возможных блокировках🙄',
                               reply_markup=connect_vpn)

    elif data:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='☕ Добавить еще месяц и 50GB: 100р\n'
                                    'неограниченное количество пользователей. '
                                    'Вы платите только за трафик',
                               reply_markup=extend_vpn)

    else:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='🦞 Переходите на новый протокол trojan, '
                                    'пробуйте тестовый период бесплатно\n\n'
                                    'или продлите свой WireGuard',
                               reply_markup=connect_vpn)


@dp.callback_query_handler(text="joy_wireguard")
async def add_wireguard(call: types.CallbackQuery):
    await call.answer()
    a = await is_test(tale_name='users', user_id=call.from_user.id)
    if a:
        await bot.send_message(chat_id=call.message.chat.id,
                               text='💈 Вы выбрали протокол Wireguard\n'
                                    'При оплате на МЕСЯЦ: 100р\n\n'
                                    'Один пользователь, безлимитный трафик.\n'
                                    '⚠️В любой момент вы можете перейти на любой другой тариф\n\n'
                                    'Сделайте выбор:',
                               reply_markup=pre_pay_keyboard_wir)
    else:
        await add_wireguard_user(user_id=call.from_user.id)
        await send_message_mi(user=call.from_user.id, text='подключил пробный WireGuard', name=call.from_user.username)
        await send_conf(user_id=call.from_user.id)
        await update_users_db(table_name='users', user_id=call.from_user.id, days=10, test=1)
        await bot.send_message(chat_id=call.message.chat.id,
                               text="Вам активирован пробный период: 10 дней",
                               reply_markup=main_menu)
        await send_video_from_file(chat_id=call.message.chat.id)


@dp.callback_query_handler(text="cancellation")
async def cancellation(call: types.CallbackQuery):
    await call.answer()


@dp.callback_query_handler(text="joy_trojan")
async def pay_message(call: types.CallbackQuery):
    await call.answer()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='☕ Micro: 50 GB / 1 месяц\n\n'
                                     'При оплате на МЕСЯЦ:\n'
                                     '👉 100 рублей\n'
                                     'ℹ 3.5 руб. в день\n\n'
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
        user = f"{user_id}rac"
        quota = '53687091200'

        data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user, ))
        trojan_is = await is_user_in_db(table_name='trojan_users', user_id=message.from_user.id)

        if not data and not trojan_is:
            print('no data')

            await send_quota(message.from_user.id, quota=quota, pay_id=pay_id)
            await write_to_db(table_name='trojan_users', user_id=user_id, refer=0, is_vpn=1, days=30)

        elif data and trojan_is:

            await fetch_data(
                "UPDATE users SET quota = quota + {} WHERE username = '{}'".format(quota, user))
            await bot.send_message(chat_id=message.chat.id,
                                   text='Вам добавлено еще 50GB и 30 дней нажмите Мой VPN, '
                                        'что бы узнать остаток своего трафика',
                                   reply_markup=main_menu)

            await bot.send_message(chat_id=message.chat.id,
                                   text=f'Платежный идентификатор\n'
                                        f'{pay_id}',
                                   reply_markup=main_menu)

            await send_message_mi(user=user, text='добавил 50GB', name=name)
            await update_users_db(table_name='trojan_users', user_id=user_id, days=30)

        elif trojan_is and not data:
            await send_quota(message.from_user.id, quota=quota, pay_id=pay_id)
            await update_users_db(table_name='trojan_users', user_id=user_id, days=30)

    elif message.successful_payment.invoice_payload == 'payment_wireguard':

        try:

            await add_wireguard_user(user_id)
            await send_conf(user_id)
            await update_users_db(table_name='users', user_id=user_id, days=30)
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'Платежный идентификатор\n'
                                        f'{pay_id}')
            await send_message_mi(user=user_id, text='подключил WireGuard', name=name)

            asyncio.create_task(delayed_task(user_id))

        except Exception as e:
            await bot.send_message(chat_id='1348491834', text=f'ошибка оплаты для юзера {user_id}{str(e)}')
