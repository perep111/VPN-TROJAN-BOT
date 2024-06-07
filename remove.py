import subprocess
from config import bot
import asyncio

CHAT_ID = '1348491834'
USER_MESSAGE_1 = '<b>😢 Время вашего VPN протокол Wireguard закончилось,\n' \
                 'но вы можете продолжить пользоваться сервисом VPN после оплаты</b>\n\n' \
                 'Продлевайте ваш VPN заранее, оставшиеся дни <b>НЕ СГОРЯТ</b>, ' \
                 'они добавятся к новому тарифу\n\n' \
                 '<b>Не хочешь платить?\n' \
                 'Приведи друга и получи 2 недели VPN бесплатно</b> ' \
                 'Нажми кнопку Реферальная программа и отправь полученную ссылку другу'
USER_MESSAGE_2 = '<b>Внимание, ожидаются блокировки протокола Wireguard, ' \
                 'рекомендую перейти но новый протокол Trojan</b>\n\n' \
                 'Нажмите кнопку Тарифы и выберите Подключить VPN Trojan или ' \
                 'Подключить пробный тариф Trojan'


async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        await asyncio.sleep(1)
    except Exception as e:
        await bot.send_message(chat_id=CHAT_ID, text=f"Ошибка отправки сообщения: {e}")
        await asyncio.sleep(1)


async def remove_wireguard_user(user_id):
    try:
        command = f'pivpn -r vpn{str(user_id)}'
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate(input=b'Y\n')

        if process.returncode == 0:
            await send_message(user_id, USER_MESSAGE_1)
            await send_message(user_id, USER_MESSAGE_2)
        else:
            await send_message(CHAT_ID, "Ошибка при удалении пользователя.")
    except subprocess.CalledProcessError as e:
        await send_message(CHAT_ID, f"Ошибка выполнения команды: {e}")
        return False
