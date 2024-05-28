import json
from os import sep
import datetime
import sqlite3
from typing import Any

sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())


def get_db_connection():
    """
    Создает новое соединение с базой данных и возвращает его.
    """
    conn = sqlite3.connect(f"UsersDB{sep}users.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    """
    Функция создаёт базу данных, если она не была создана ранее
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            chat_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            register_date DATE,
            last_selected_start_station TEXT,
            count_trains INTEGER,
            favorite_trips TEXT,
            selected_trip_to_remove TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_all_users() -> list[Any]:
    """
    Функция возвращает список пользователей, хранящихся в базе данных
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_current_user(chat_id: int) -> dict:
    """
    Функция возвращает данные одного пользователя по его chat_id в виде словаря.
    :param chat_id: ID пользователя
    :return: Словарь с данными пользователя
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row is not None:
        return dict(row)
    else:
        return {}


def add_user(chat_id: int, username: str, first_name: str, last_name: str, register_date: datetime.date):
    """
    Функция добавляет нового пользователя в базу данных, при условии,
    что пользователя с таким chat_id нет в базе данных.
    :param chat_id: ID Чата в Телеграмм
    :param username: Имя аккаунта Телеграмм без "@"
    :param first_name: Имя пользователя
    :param last_name: Фамилия пользователя
    :param register_date: Дата регистрации
    """
    if not get_current_user(chat_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (chat_id, username, first_name, last_name, register_date, "
                       "last_selected_start_station, count_trains, favorite_trips, selected_trip_to_remove) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (chat_id, username, first_name, last_name, register_date, None, 3, None, None))
        conn.commit()
        conn.close()


def delete_user(chat_id):
    """
    Функция удаляет пользователя из базы данных по его user_id.
    :param chat_id: ID пользователя
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def update_user_data(chat_id: int, column_numbers: list, new_values: list):
    """
    Функция изменяет данные в требуемых столбцах на необходимые для конкретного пользователя.

    Столбцы имеют следующие номера
        0. **chat_id:** ID Чата в Телеграмм

        1. **username:** Имя аккаунта Телеграмм без "@"

        2. **first_name:** Имя пользователя

        3. **last_name:** Фамилия пользователя

        4. **register_date:** Дата регистрации

        5. **last_selected_start_station:** Выбранная пользователем станция начала поездки

        6. **count_trains:** Количество поездов, которые выводятся пользователю

        7. **selected_trip_to_remove** Выбранный маршрут из избранных для удаления

    :param chat_id: ID пользователя
    :param column_numbers: Массив с номерами столбцов, которые нужно изменить.
    :param new_values: Массив с новыми значениями для соответствующих столбцов
    """
    column_mapping = {
        0: "chat_id",
        1: "username",
        2: "first_name",
        3: "last_name",
        4: "register_date",
        5: "last_selected_start_station",
        6: "count_trains",
        7: "selected_trip_to_remove"
    }

    columns = [column_mapping[num] for num in column_numbers]

    set_clause = ", ".join([f"{column} = ?" for column in columns])

    values = tuple(new_values)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {set_clause} WHERE chat_id = ?", (*values, chat_id))
    conn.commit()
    conn.close()


def add_favorite_trip(chat_id, new_trip):
    """
    Функция добавляет новый избранный маршрут для пользователя
    :param chat_id: ID пользователя
    :param new_trip: Новый избранный маршрут
    """
    favorite_trips = get_favorite_trips(chat_id)
    favorite_trips.append(new_trip)
    trips_json = json.dumps(favorite_trips)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET favorite_trips = ? WHERE chat_id = ?", (trips_json, chat_id))
    conn.commit()
    conn.close()


def get_favorite_trips(chat_id):
    """
    Функция извлекает избранные маршруты пользователя
    :param chat_id: ID пользователя
    :return: Список избранных маршрутов
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT favorite_trips FROM Users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0]:
        return json.loads(result[0])
    return []


def remove_favorite_trip(chat_id, trip_to_remove):
    """
    Функция удаляет избранный маршрут из списка избранных маршрутов пользователя
    :param chat_id: ID пользователя
    :param trip_to_remove: Маршрут, который нужно удалить
    """
    favorite_trips = get_favorite_trips(chat_id)
    if trip_to_remove in favorite_trips:
        favorite_trips.remove(trip_to_remove)
        trips_json = json.dumps(favorite_trips)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET favorite_trips = ? WHERE chat_id = ?", (trips_json, chat_id))
        conn.commit()
        conn.close()
