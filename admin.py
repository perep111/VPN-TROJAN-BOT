import psutil
import math
import time
from database import how_users_in_db
# import speedtest


# async def get_speed():
#     st = speedtest.Speedtest()
#     download_speed = st.download()
#     upload_speed = st.upload()
#
#     return download_speed, upload_speed


def readable_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f'{s} {size_name[i]}'


async def get_system_info():
    # Используем psutil для получения информации о системе
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_percent = psutil.cpu_percent(interval=1)

    # Замер начального времени и данных
    start_time = time.time()
    start_down_bandwidth = psutil.net_io_counters().bytes_recv
    start_up_bandwidth = psutil.net_io_counters().bytes_sent

    # Ждем некоторое время (например, 1 секунда)
    time.sleep(1)

    # Замер конечного времени и данных
    end_time = time.time()
    end_down_bandwidth = psutil.net_io_counters().bytes_recv
    end_up_bandwidth = psutil.net_io_counters().bytes_sent

    # Вычисляем скорость загрузки и отдачи
    down_speed = (end_down_bandwidth - start_down_bandwidth) / (end_time - start_time)
    up_speed = (end_up_bandwidth - start_up_bandwidth) / (end_time - start_time)

    total_memory = readable_size(psutil.virtual_memory().total)
    used_memory = readable_size(psutil.virtual_memory().used)
    free_memory = readable_size(psutil.virtual_memory().available)

    network = psutil.net_io_counters()
    down_bandwidth = network.bytes_recv
    up_bandwidth = network.bytes_sent
    total_bandwidth = readable_size(network.bytes_recv + network.bytes_sent)

    # download_speed, upload_speed = await get_speed()  #для спидтест
    users_in_wg = await how_users_in_db('users')
    users_in_tj = await how_users_in_db('trojan_users')
    total_users = users_in_tj + users_in_wg

    return """\
🎛 *CPU ядра*: `{cpu_cores}`
🖥 *CPU используется*: `{cpu_percent}%`
➖➖➖➖➖➖➖
📊 *Всего памяти*: `{total_memory}`
📈 *Занято памяти*: `{used_memory}`
📉 *Свободно памяти*: `{free_memory}`
➖➖➖➖➖➖➖
⬇️ *Загружено*: `{down_bandwidth}`
⬆️ *Отдано*: `{up_bandwidth}`
↕️ *Общий трафик*: `{total_bandwidth}`
➖➖➖➖➖➖➖
👥 *Пользователей trojan*: `{users_trojan}`
👥 *Пользователей wireguard*: `{users_wireguard}`
👥 *Всего пользователей*: `{total_users}`
➖➖➖➖➖➖➖
⏫ *Скорость отдачи*: `{up_speed}`
⏬ *Скорость загрузки*: `{down_speed}`
""".format(
        cpu_cores=cpu_cores,
        cpu_percent=cpu_percent,
        total_memory=total_memory,
        used_memory=used_memory,
        free_memory=free_memory,
        total_bandwidth=total_bandwidth,
        up_bandwidth=readable_size(up_bandwidth),
        down_bandwidth=readable_size(down_bandwidth),
        users_trojan=users_in_tj,
        users_wireguard=users_in_wg,
        total_users=total_users,
        up_speed=readable_size(up_speed),
        down_speed=readable_size(down_speed)
    )
