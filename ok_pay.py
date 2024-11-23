import logging
from marzban import backend
from database import is_user_in_db, write_to_db, update_users_db
from config import bot
from func import main_menu, send_message_link


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)




async def saksefull_pay(user_id):
    data = backend.get_user(user_id)
    trojan_is = await is_user_in_db(table_name='trojan_users', user_id=user_id)

    if not data and not trojan_is:

        await write_to_db(table_name='trojan_users', user_id=user_id, refer=0, is_vpn=1, days=30, test=1)
        
        link = backend.create_user(user_id)

        if link is None:
            log.info(f'линк: для юзера {user_id} == None')
            await bot.send_message(user_id, 'возннникла ошибка с созданием профиля\n'
                                'обратитесь в поддержку @f_o_x_y_s')
            
            await bot.send_message(chat_id='1348491834', text=f'ошибка оплаченой ссылки для {user_id}')
        else:    
            await send_message_link(user_id, link['subscription_url'])  

            await bot.send_message(chat_id=user_id,
                                text='Вам доступно 30 дней VPN нажмите Мой VPN, '
                                        'что бы узнать срок действия тарифа\n\n'
                                        'Нажимай Как настроить VPN и получи подробную инструкцию по установке',
                                reply_markup=main_menu)

    elif data and trojan_is:

        backend.enable_user(user_id)


        await bot.send_message(chat_id=user_id,
                                text='Вам добавлено еще 30 дней нажмите Мой VPN, '
                                    'что бы узнать срок действия тарифа',
                                reply_markup=main_menu)
        
        await send_message_link(user_id, data['subscription_url'])

        await update_users_db(table_name='trojan_users', user_id=user_id, days=30)


    elif trojan_is and not data:

        link = backend.create_user(user_id)

        if link is None:
            log.info(f'линк: для юзера {user_id} == None')
            await bot.send_message(user_id, 'возннникла ошибка с созданием профиля\n'
                                'обратитесь в поддержку @f_o_x_y_s')
            await bot.send_message(chat_id='1348491834', text=f'ошибка оплаченой ссылки для {user_id}')
        else:    
            await send_message_link(user_id, link['subscription_url'])  


            await update_users_db(table_name='trojan_users', user_id=user_id, days=30)

            await bot.send_message(chat_id=user_id,
                                text='Вам доступно еще 30 дней,'
                                        'нажмите Мой VPN, что бы узнать срок действия тарифа\n\n'
                                        'Нажимай Как настроить VPN и получи подробную инструкцию по установке',
                                reply_markup=main_menu)
