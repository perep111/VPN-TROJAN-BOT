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
