import logging
import aiomysql
import aiosqlite
from datetime import datetime, timedelta
from remove import remove_wireguard_user
from config import bot
from marzban import backend
from pay_conf import pay_conf_trojan
import asyncio

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваши настройки для подключения к MySQL
mysql_config = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "trojan",
    "password": "thisisthetrojandbpassword",
    "db": "trojan",
}


# Создайте соединение с базой данных
async def create_db_pool():
    global db_pool
    try:
        db_pool = await aiomysql.create_pool(
            host=mysql_config["host"],
            port=mysql_config["port"],
            user=mysql_config["user"],
            password=mysql_config["password"],
            db=mysql_config["db"],
            autocommit=True,  # Для автоматической фиксации изменений
            cursorclass=aiomysql.cursors.DictCursor,  # Для получения результатов как словарей
        )
        print("подлючение все четко")
        return db_pool
    except aiomysql.MySQLError as e:
        print(f"Ошибка при подключении к базе данных 1: {e}")
        return


async def fetch_data(query, args=None):
    global db_pool
    if db_pool is None:
        raise Exception("База данных не инициализирована. Вызовите init_db_pool.")

    try:

        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, args)
                result = await cursor.fetchall()
                # print(result)
        return result

    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")


async def create_db():
    print('создаю базу')
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    await cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            join_date DATE,
            is_vpn INTEGER,
            end_date DATE,
            test INTEGER,
            refer INTEGER
        )
    ''')
    await cursor.execute('''
        CREATE TABLE IF NOT EXISTS trojan_users (
            user_id INTEGER PRIMARY KEY,
            join_date DATE,
            is_vpn INTEGER,
            end_date DATE,
            test INTEGER,
            refer INTEGER,
            password TEXT
        )
    ''')

    await connection.commit()
    await connection.close()


async def write_to_db(user_id, table_name, refer, is_vpn=0, test=0, days=None):
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()
    join_date = datetime.now()
    join_date_str = join_date.strftime('%Y-%m-%d %H:%M:%S')
    if days:
        one_month_go = join_date + timedelta(days=days)
        one_month_go_str = one_month_go.strftime('%Y-%m-%d %H:%M:%S')

    else:
        one_month_go_str = None

    await cursor.execute(
        f'INSERT INTO {table_name} (user_id, join_date, is_vpn, refer, test, end_date) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, join_date_str, is_vpn, refer, test, one_month_go_str))

    await connection.commit()
    await connection.close()


async def is_vpn_false(user_id, table_name):
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    await cursor.execute(f'UPDATE {table_name} SET is_vpn = ? WHERE user_id = ?', (0, user_id))

    await connection.commit()
    await connection.close()


async def check_users_vpn_service():
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    # Получение текущей даты и вычисление даты месяц назад

    current_date = datetime.now()
    current_date_str = current_date.strftime('%Y-%m-%d %H:%M:%S')

    # Получение списка пользователей, присоединившихся ровно месяц назад

    await cursor.execute('SELECT user_id FROM users WHERE end_date IS NOT NULL AND end_date <= ? AND is_vpn = ?',
                         (current_date_str, True))

    users_to_delete_wireguard = await cursor.fetchall()

    # Удаление учетки каждого пользователя из wireguard
    for user_id in users_to_delete_wireguard:
        await remove_wireguard_user(user_id[0])
        await is_vpn_false(user_id[0], table_name='users')

    await cursor.execute('SELECT user_id FROM trojan_users WHERE end_date IS NOT NULL AND end_date <= ? AND is_vpn = ?',
                         (current_date_str, True))

    users_to_delete_trojan = await cursor.fetchall()

    # Удаление учетки каждого пользователя из trojan
    for user_id in users_to_delete_trojan:
        await remove_trojan_user(user_id[0])
        await is_vpn_false(user_id[0], table_name='trojan_users')

    await connection.commit()
    await connection.close()


async def is_user_in_db(table_name, user_id: int) -> bool:
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    await cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE user_id = ?', (user_id,))
    result = await cursor.fetchone()

    await connection.close()

    return result[0] > 0


async def how_users_in_db(table_name):
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    await cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE is_vpn = ?', (1,))
    result = await cursor.fetchone()

    await connection.close()

    return result[0]


async def how_users_in_db_unic():
    try:
        conn = await aiosqlite.connect('vpn-user.db')
        cursor = await conn.cursor()

        select_user_id = await cursor.execute('''
            SELECT user_id FROM users WHERE is_vpn = 1
            UNION
            SELECT user_id FROM trojan_users WHERE is_vpn = 1
        ''')
        select_order = await select_user_id.fetchall()

        users_dict = [i[0] for i in select_order]

        await conn.close()
        return len(users_dict)

    except Exception as e:
        print(e)


async def update_users_db(table_name, user_id, days, test=1):
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    now_date = datetime.now()
    now_date_str = now_date.strftime('%Y-%m-%d %H:%M:%S')
    one_month_go = now_date + timedelta(days=days)
    one_month_go_str = one_month_go.strftime('%Y-%m-%d %H:%M:%S')

    try:

        await cursor.execute(f'SELECT end_date FROM {table_name} WHERE user_id = ?', (user_id,))
        date_in_db = await cursor.fetchone()

        if date_in_db[0]:

            if date_in_db[0] <= now_date_str:

                await cursor.execute(f'UPDATE {table_name} SET end_date = ?, is_vpn = ?, test = ? WHERE user_id = ?',
                                     (one_month_go_str, 1, test, user_id))

            elif date_in_db[0] >= now_date_str:
                date_obj = datetime.strptime(date_in_db[0], '%Y-%m-%d %H:%M:%S')
                one_month_later = date_obj + timedelta(days=days)
                one_month_later_str = one_month_later.strftime('%Y-%m-%d %H:%M:%S')

                await cursor.execute(f'UPDATE {table_name} SET end_date = ?, is_vpn = ?, test = ? WHERE user_id = ?',
                                     (one_month_later_str, 1, test, user_id))

        else:

            await cursor.execute(
                f'UPDATE {table_name} SET end_date=?, is_vpn=?, test=? WHERE user_id=?',
                (one_month_go_str, 1, test, user_id)
            )

    except Exception as e:
        print(e)

    await connection.commit()
    await connection.close()


async def read_to_db_user_id():
    try:
        conn = await aiosqlite.connect('vpn-user.db')
        cursor = await conn.cursor()

        select_user_id = await cursor.execute('''
            SELECT user_id FROM users
            UNION
            SELECT user_id FROM trojan_users
        ''')
        select_order = await select_user_id.fetchall()

        users_dict = [i[0] for i in select_order]

        await conn.close()
        return users_dict

    except Exception as e:
        print(e)


async def read_to_db_end_date(user_id, table_name):
    try:
        conn = await aiosqlite.connect('vpn-user.db')
        cursor = await conn.cursor()

        await cursor.execute(f'SELECT end_date FROM {table_name} WHERE user_id = ?', (user_id,))
        end_date = await cursor.fetchone()

        await conn.close()
        return end_date

    except Exception as e:
        print(e)


async def is_user_in_wireguard(user_id: int) -> bool:
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    await cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ? AND is_vpn = ?',
                         (user_id, True))
    result = await cursor.fetchone()

    await connection.close()

    return result[0] > 0


async def is_user_in_trojan(user_id: int) -> bool:
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    await cursor.execute('SELECT COUNT(*) FROM trojan_users WHERE user_id = ? AND is_vpn = ?',
                         (user_id, True))
    result = await cursor.fetchone()

    await connection.close()

    return result[0] > 0


async def is_test(tale_name, user_id: int) -> bool:
    connection = await aiosqlite.connect('vpn-user.db')
    cursor = await connection.cursor()

    await cursor.execute(f'SELECT COUNT(*) FROM {tale_name} WHERE user_id = ? AND test = ?',
                         (user_id, True))
    result = await cursor.fetchone()

    await connection.close()

    return result[0] > 0


async def remove_trojan_user(user_id):
    user = f"{user_id}rac"

    data = await fetch_data("SELECT * FROM users WHERE username = '{}'".format(user, ))

    if data:
        await fetch_data("DELETE FROM users WHERE username = '{}'".format(user,))
        # await fetch_data("UPDATE users SET quota = 1, download = 0, upload = 0 WHERE username = '{}'".format(user,))

        
    a = backend.disable_user(user_id)
    if not a:
        logger.info(f'Не удалось disable: {user_id}')
        await bot.send_message(chat_id='1348491834', text=f'Не дисайбл юзер: {user_id}')


    try:
        await bot.send_message(chat_id=user_id,
                               text='<b>😢 Время вашего VPN закончилось,\n'
                                    'но вы можете продолжить пользоваться сервисом VPN после оплаты</b>\n\n'
                                    'Продлевайте ваш VPN заранее, оставшиеся дни <b>НЕ СГОРЯТ</b>, '
                                    'они добавятся к новому тарифу\n\n'
                                    '<b>Не хочешь платить?\n'
                                    'Приведи друга и получи 2 недели VPN бесплатно</b> '
                                    'Нажми кнопку Реферальная программа и отправь полученную ссылку другу')
        await pay_conf_trojan(user_id)

    except Exception as e:
        await bot.send_message(chat_id='1348491834', text=f"Ошибка отправки сообщения: юзеру {user_id}\n {e}")
        await asyncio.sleep(1)


async def count_refs(user_id: int):
    try:
        conn = await aiosqlite.connect('vpn-user.db')
        cursor = await conn.cursor()

        select_user_id = await cursor.execute('''
            SELECT refer FROM trojan_users WHERE refer=?
        ''', (user_id,))
        select_order = await select_user_id.fetchall()

        users_dict = [i[0] for i in select_order]

        await conn.close()
        return len(users_dict)

    except Exception as e:
        print(e)


async def check_notifications(tale_name):
    try:

        end_date_start = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
        end_date_end = (datetime.now() + timedelta(days=1, minutes=1)).strftime('%Y-%m-%d %H:%M')

        conn = await aiosqlite.connect('vpn-user.db')
        cursor = await conn.cursor()

        # Find users whose end_date is within the next 24 hours
        query = f'''
            SELECT user_id
            FROM {tale_name}
            WHERE end_date > ? AND end_date <= ?
        '''

        await cursor.execute(query, (end_date_start, end_date_end))
        users_to_notify = await cursor.fetchall()

        users_dict = [i[0] for i in users_to_notify]

        await conn.close()
        return users_dict

    except Exception as e:
        print(e)
