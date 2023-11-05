
import aiomysql
import aiosqlite
from datetime import datetime, timedelta
from remove import remove_wireguard_user


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
    connection = await aiosqlite.connect('vpn-user-test.db')
    cursor = await connection.cursor()

    await cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            join_date DATE,
            is_vpn INTEGER,
            end_date DATE
        )
    ''')
    await cursor.execute('''
        CREATE TABLE IF NOT EXISTS trojan_users (
            user_id INTEGER PRIMARY KEY,
            join_date DATE,
            is_vpn INTEGER,
            end_date DATE
        )
    ''')

    await connection.commit()
    await connection.close()


async def write_to_db(user_id, table_name, day):
    connection = await aiosqlite.connect('vpn-user-test.db')
    cursor = await connection.cursor()
    join_date = datetime.now()
    join_date_str = join_date.strftime('%Y-%m-%d %H:%M:%S')
    one_month_go = join_date + timedelta(days=day)
    one_month_go_str = one_month_go.strftime('%Y-%m-%d %H:%M:%S')

    await cursor.execute(f'INSERT INTO {table_name} (user_id, join_date, is_vpn, end_date) VALUES (?, ?, ?, ?)',
                         (user_id, join_date_str, 1, one_month_go_str))

    await connection.commit()
    await connection.close()


async def is_vpn_false(user_id, table_name):
    connection = await aiosqlite.connect('vpn-user-test.db')
    cursor = await connection.cursor()

    await cursor.execute(f'UPDATE {table_name} SET is_vpn = ? WHERE user_id = ?', (0, user_id))

    await connection.commit()
    await connection.close()


async def check_users_vpn_service():
    connection = await aiosqlite.connect('vpn-user-test.db')
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
        # await remove_trojan_user(user_id[0])                                           сделать удаление из базы троян
        await is_vpn_false(user_id[0], table_name='trojan_users')

    await connection.commit()
    await connection.close()


async def is_user_in_db(table_name, user_id: int) -> bool:
    connection = await aiosqlite.connect('vpn-user-test.db')
    cursor = await connection.cursor()

    await cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE user_id = ?', (user_id,))
    result = await cursor.fetchone()

    await connection.close()

    return result[0] > 0


async def update_users_db(table_name, user_id):
    connection = await aiosqlite.connect('vpn-user-test.db')
    cursor = await connection.cursor()

    now_date = datetime.now()
    now_date_str = now_date.strftime('%Y-%m-%d %H:%M:%S')
    one_month_go = now_date + timedelta(days=30)
    one_month_go_str = one_month_go.strftime('%Y-%m-%d %H:%M:%S')

    try:
        print('1')

        await cursor.execute(f'SELECT end_date FROM {table_name} WHERE user_id = ?', (user_id,))
        date_in_db = await cursor.fetchone()

        if date_in_db[0]:
            print(date_in_db[0])
            print(now_date_str)

            if date_in_db[0] <= now_date_str:

                print('3')
                await cursor.execute(f'UPDATE {table_name} SET end_date = ?, is_vpn = ? WHERE user_id = ?',
                                     (one_month_go_str, 1, user_id))

            elif date_in_db[0] >= now_date_str:
                date_obj = datetime.strptime(date_in_db[0], '%Y-%m-%d %H:%M:%S')
                one_month_later = date_obj + timedelta(days=30)
                one_month_later_str = one_month_later.strftime('%Y-%m-%d %H:%M:%S')

                await cursor.execute(f'UPDATE {table_name} SET end_date = ?, is_vpn = ? WHERE user_id = ?',
                                     (one_month_later_str, 1, user_id))

        else:
            await cursor.execute(
                f'INSERT OR REPLACE INTO {table_name} (end_date, is_vpn, WHERE user_id) VALUES (?, ?, ?,)',
                (one_month_go_str, 1, user_id)
            )

    except Exception as e:
        print(e)

    await connection.commit()
    await connection.close()


async def read_to_db_user_id():
    try:
        conn = await aiosqlite.connect('vpn-user-test.db')
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
        conn = await aiosqlite.connect('vpn-user-test.db')
        cursor = await conn.cursor()

        await cursor.execute(f'SELECT end_date FROM {table_name} WHERE user_id = ?', (user_id,))
        end_date = await cursor.fetchone()

        await conn.close()
        return end_date

    except Exception as e:
        print(e)


async def is_user_in_wireguard(user_id: int) -> bool:
    connection = await aiosqlite.connect('vpn-user-test.db')
    cursor = await connection.cursor()

    await cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ? AND is_vpn = ?',
                         (user_id, True))
    result = await cursor.fetchone()

    await connection.close()

    return result[0] > 0
