import hashlib
import uuid
import logging
import asyncio
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import NetworkError, RetryAfter
from aiogram.dispatcher.filters.state import StatesGroup, State
from config import dp, bot, client
from func import main_menu, connect_vpn, generate_password, pre_pay_keyboard, kb_func, instrukt_kb
from func import set_message_deletion_timer
from aiogram import types
from aiogram.types import Message
from database import fetch_data


admin = [1348491834]
delayed_message_flag = False


class UserState(StatesGroup):
    PROCESS_ORDER = State()


@dp.errors_handler()
async def error_handler(update, exception):
    if isinstance(exception, NetworkError):
        logging.error(f"NetworkError: {exception}")
        # Дополнительная обработка или уведомления об ошибке
        return True  # Отмечаем ошибку как обработанную

    elif isinstance(exception, RetryAfter):
        await asyncio.sleep(exception.timeout)
        return True  # Обработка завершена, можно продолжить выполнение


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
        # quota = data[0][3]
        # download_value = data[0][4]
        # upload_value = data[0][5]
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


@dp.callback_query_handler(lambda c: c.data == 'back', state='*')
async def push_cancel(call: types.CallbackQuery, state: FSMContext):
    await state.reset_state()
    await call.answer()
    # await call.message.answer('Вы отказались от подписки\n'
    #                           'Для дальнейшей работы с ботом необходима подписка\n'
    #                           'нажмите /menu', reply_markup=kb)
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='Вы отказались, мне <b>очень жаль</b>')


@dp.callback_query_handler(text='pre_pay')
async def menu_message(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    password = str(uuid.uuid4())
    async with state.proxy() as data:
        data['password'] = password

    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text='Жми кнопку "Оплатить" и после оплаты нажми\n ПРОВЕРКА ОПЛАТЫ',
                                reply_markup=kb_func(password))
    await UserState.PROCESS_ORDER.set()

    asyncio.create_task(set_message_deletion_timer(call.from_user.id, call.message.message_id, state))


@dp.callback_query_handler(text='verification', state=UserState.PROCESS_ORDER)
async def push_payment(call: types.CallbackQuery, state: FSMContext):
    user = f"{call.from_user.id}rac"
    name = call.from_user.username
    quota = '53687091200'
    async with state.proxy() as data:
        password = data['password']
    try:
        history = client.operation_history(label=password)

        if not history.operations:
            await bot.answer_callback_query(callback_query_id=call.id,
                                            text='Оплаты не было',
                                            show_alert=True)

        else:
            for i in history.operations:
                if i.status == 'success':
                    data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user, ))

                    if not data:

                        await bot.answer_callback_query(callback_query_id=call.id,
                                                        text='Спасибо за донат',
                                                        show_alert=True)
                        password_hash = generate_password(15)
                        fullhash = hashlib.sha224(password_hash.encode('utf-8')).hexdigest()

                        await fetch_data(
                            "INSERT INTO users (username, password, quota) VALUES ('{}', '{}', '{}')".format(user,
                                                                                                             fullhash,
                                                                                                             quota))
                        url = f"trojan://{password_hash}@24perep.ru:8888?security=tls&sni=24perep.ru&alpn=http%2F1.1%2Ch2%2Ch3&fp=chrome&type=tcp&headerType=none#{user}"

                        await bot.send_message(chat_id=call.from_user.id, text='ваша ссылка')
                        await bot.send_message(chat_id=call.from_user.id, text=url)
                        if name:
                            await bot.send_message(chat_id='1348491834',text=f"имя: @{name} добавлен {user}")
                        else:
                            await bot.send_message(chat_id='1348491834', text=f"добавлен {user}")
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                        await state.finish()

                    else:
                        await bot.answer_callback_query(callback_query_id=call.id,
                                                        text='Спасибо за донат',
                                                        show_alert=True)
                        await fetch_data(
                            "UPDATE users SET quota = quota + {} WHERE username = '{}'".format(quota, user))
                        await bot.send_message(chat_id=call.from_user.id, text='Вам добавлено еще 50GB')

                        if name:
                            await bot.send_message(chat_id='1348491834', text=f"имя: @{name} добавил 50GB {user}")
                        else:
                            await bot.send_message(chat_id='1348491834', text=f"добавил 50GB {user}")
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                        await state.finish()

    except Exception as e:
        await bot.send_message(chat_id='1348491834', text=f'ошибка оплаты для юзера {user}{str(e)}')
