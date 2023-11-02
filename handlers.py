import hashlib
import logging
import asyncio
from aiogram.utils.exceptions import NetworkError, RetryAfter
from config import dp, bot
from func import main_menu, connect_vpn, generate_password, instrukt_kb, pay_conf, recept
from func import pre_pay_keyboard, delayed_task
from aiogram import types
from aiogram.types import Message, ContentType
from database import fetch_data


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


@dp.message_handler(commands=['start'])
async def process_start_command(msg: Message):
    await msg.answer(' @free_VIP_VPN_bot работает везде! Даже там, где VPN блокируют.'
                     ' Мы используем самый современный и защищенный протокол Trojan,'
                     ' который эффективно маскирует трафик под обычный, и с легкостью'
                     ' обходит любые системы глубокого анализа трафика.')
    await msg.answer_sticker(sticker='CAACAgIAAxkBAAEBgo9lL7p4rfT_TOJ25HtBsN-EtQ22YQACTQADWbv8JSiBoG3dG4L3MAQ')
    await msg.answer('Встречайте лучший в мире VPN!', reply_markup=main_menu)


@dp.message_handler(text='💸 Тарифы')
async def mess_replay(msg: Message):
    await msg.answer('Тариф пока один: 100р 50GB\n\n'
                     'неограниченное количество пользователей\n'
                     'Вы платите только за трафик', reply_markup=connect_vpn)


@dp.message_handler(text='🤯 Поддержка')
async def mess_replay(msg: Message):
    await msg.answer('если возникли проблемы с подключением или с подпиской,\n'
                     'напишите разработчикам @f_o_x_y_s,\n'
                     'так же последние новости публикуются на '
                     '<a href="https://24perep.ru/news/">этом сайте</a>')


@dp.message_handler(text='🔐 Мой VPN')
async def get_data(msg: Message):
    user = f"{msg.from_user.id}rac"
    data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user,))

    # Теперь вы можете обработать результат и отправить его в чат
    # Проверьте, что result не пустой
    if data:
        quota = data[0]['quota']
        download_value = data[0]['download']
        upload_value = data[0]['upload']
        a = round(((quota - (download_value + upload_value)) / 1073741824), 2)

        await msg.answer(f'🌟 Ваш тариф ☕️ Micro: 50 GB\n\n'
                         f'🚀 остаток трафика = {a}GB\n\n'
                         f'ℹ Вы можете установить и настроить VPN на неограниченное количество устройств,'
                         f' все они будут расходовать ваш трафик.\n\n'
                         f'Добавить еще трафик: ', reply_markup=instrukt_kb)

    else:
        await msg.answer('👉 Все тарифы работают на неограниченное количество устройств.'
                         ' Вы платите только за трафик\n\n'
                         '☕ 50 GB - должно хватить для 1 устройства с умеренной активностью в соц. сетях',
                         reply_markup=connect_vpn)


@dp.callback_query_handler(text="Extend_tariff")
async def extend_tariff(call: types.CallbackQuery):
    await call.answer()
    await bot.send_message(chat_id=call.from_user.id,
                           text='Тариф пока один: 100р 50GB\n\n'
                                'неограниченное количество пользователей\n'
                                'Вы платите только за трафик',
                           reply_markup=connect_vpn)


@dp.callback_query_handler(text="cancellation")
async def cancellation(call: types.CallbackQuery):
    await call.answer()


@dp.callback_query_handler(text="pay")
async def pay_message(call: types.CallbackQuery):
    await call.answer()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='☕ Micro: 50 GB / 1 месяц\n\n'
                                     'При оплате на МЕСЯЦ:\n'
                                     '👉 100 рублей\n'
                                     'ℹ 3.5 руб. в день\n\n'
                                     '⚠️В любой момент вы можете перейти на любой другой тариф '
                                     'без потери неизрасходованного трафика\n\n'
                                     'Сделайте выбор:',
                                reply_markup=pre_pay_keyboard)


@dp.callback_query_handler(lambda c: c.data == 'back')
async def push_cancel(call: types.CallbackQuery):
    await call.answer()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='Вы отказались, мне <b>очень жаль</b>')


@dp.callback_query_handler(text='pre_pay')
async def menu_message(call: types.CallbackQuery):
    await call.answer()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='👇🏻')

    await pay_conf(call.message.chat.id)


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    # await bot.send_message(chat_id=query.from_user.id, text='11')
    print('покупква')


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
    if message.successful_payment.invoice_payload == 'payment':
        await bot.send_message(message.from_user.id, 'Поздравляю с покупкой')
        name = message.from_user.username
        user_id = message.from_user.id
        user = f"{message.from_user.id}rac"
        quota = '53687091200'

        data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user, ))

        if not data:

            password_hash = generate_password(15)
            fullhash = hashlib.sha224(password_hash.encode('utf-8')).hexdigest()

            await fetch_data(
                "INSERT INTO users (username, password, quota) VALUES ('{}', '{}', '{}')".format(user,
                                                                                                 fullhash,
                                                                                                 quota))
            url = f"trojan://{password_hash}@24perep.ru:8888?security=tls&sni=24perep.ru&alpn=http%2F1.1%2Ch2%2Ch3&fp=chrome&type=tcp&headerType=none#{user}"

            await bot.send_message(chat_id=message.chat.id, text='ваша ссылка')
            await bot.send_message(chat_id=message.chat.id, text=url, reply_markup=main_menu)
            if name:
                await bot.send_message(chat_id='1348491834',text=f"новый юзер: @{name} добавлен {user}")
            else:
                await bot.send_message(chat_id='1348491834', text=f"новый {user}")

            asyncio.create_task(delayed_task(user_id))

        else:

            await fetch_data(
                "UPDATE users SET quota = quota + {} WHERE username = '{}'".format(quota, user))
            await bot.send_message(chat_id=message.chat.id,
                                   text='Вам добавлено еще 50GB нажмите Мой VPN, что бы узнать остаток своего трафика',
                                   reply_markup=main_menu)

            if name:
                await bot.send_message(chat_id='1348491834', text=f"имя: @{name} добавил 50GB {user}")
            else:
                await bot.send_message(chat_id='1348491834', text=f"добавил 50GB {user}")

