import asyncio
import aiomysql


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
    try:
        pool = await aiomysql.create_pool(
            host=mysql_config["host"],
            port=mysql_config["port"],
            user=mysql_config["user"],
            password=mysql_config["password"],
            db=mysql_config["db"],
            autocommit=True,  # Для автоматической фиксации изменений
            cursorclass=aiomysql.cursors.DictCursor,  # Для получения результатов как словарей
            loop=asyncio.get_event_loop()
        )
        return pool
    except aiomysql.MySQLError as e:
        print(f"Ошибка при подключении к базе данных 1: {e}")
        return


db_pool = asyncio.get_event_loop().run_until_complete(create_db_pool())


async def fetch_data(query, args=None):
    try:
        async with db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, args)
                result = await cursor.fetchall()
        return result

    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
