import subprocess
from config import bot
import asyncio
from pay_conf import pay_conf_wireguard


async def remove_wireguard_user(user_id):
    try:
        # Формируем команду для удаления пользователя
        command = f'pivpn -r vpn{str(user_id)}'

        # Запускаем процесс для выполнения команды
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Отправляем ввод "Y" для подтверждения удаления пользователя
        process.communicate(input=b'Y\n')

        if process.returncode == 0:
            # return
            # await bot.send_message(chat_id='1348491834',text=f"Пользователь {user_id} успешно удален из WireGuard.")
            try:
                await bot.send_message(chat_id=user_id,
                                       text='<b>😢 Время вашего VPN протокол Wireguard закончилось,\n'
                                            'но вы можете продолжить пользоваться сервисом VPN после оплаты</b>\n\n'
                                            'Продлевайте ваш VPN заранее, оставшиеся дни <b>НЕ СГОРЯТ</b>, '
                                            'они добавятся к новому тарифу')
                await pay_conf_wireguard(user_id)
                await asyncio.sleep(1)
            except Exception as e:
                await bot.send_message(chat_id='1348491834',text=f"Ошибка отправки сообщения: {e}")
                await asyncio.sleep(1)
        else:
            await bot.send_message(chat_id='1348491834',text=f"Ошибка при удалении пользователя.")

    except subprocess.CalledProcessError as e:
        await bot.send_message(chat_id='1348491834',text=f"Ошибка выполнения команды: {e}")
        return False
