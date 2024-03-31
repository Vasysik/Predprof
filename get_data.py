import requests
import sqlite3
from datetime import datetime

# Функция для получения списка дат с сервера
def get_dates():
    url = "https://olimp.miet.ru/ppo_it_final/date"
    headers = {"X-Auth-Token": "ppo_10_17129"}  # Замените на свой логин
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        dates = response.json()["message"]
        return dates
    else:
        print("Failed to get dates:", response.status_code)
        return []

# Функция для получения данных по определенной дате с сервера
def get_data_by_date(date):
    day, month, year = date.split("-")
    url = f"https://olimp.miet.ru/ppo_it_final?day={day}&month={month}&year={year}"
    headers = {"X-Auth-Token": "ppo_10_17129"}  # Замените на свой логин
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()["message"]
        return data
    else:
        print(f"Failed to get data for {date}:", response.status_code)
        return None

# Функция для создания таблицы в базе данных
def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        DROP TABLE IF EXISTS room_data
    """)
    cursor.execute("""
        CREATE TABLE room_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            flats_count INTEGER,
            windows_for_flat TEXT,
            windows TEXT
        )
    """)
    conn.commit()

# Функция для сохранения данных в базу данных
def save_to_database(conn, data):
    cursor = conn.cursor()
    # Преобразуем временную метку в формат день-месяц-год
    date_str = datetime.fromtimestamp(data["date"]["data"]).strftime("%d-%m-%y")
    cursor.execute("""
        INSERT INTO room_data (date, flats_count, windows_for_flat, windows)
        VALUES (?, ?, ?, ?)
    """, (date_str, data["flats_count"]["data"], str(data["windows_for_flat"]["data"]), str(data["windows"]["data"])))
    conn.commit()

# Подключаемся к базе данных
conn = sqlite3.connect('room_data.db')
create_table(conn)

# Получаем список дат
dates = get_dates()
if dates:
    for date in dates:
        # Получаем данные для каждой даты
        data = get_data_by_date(date)
        if data:
            save_to_database(conn, data)
        else:
            print(f"No data available for {date}")
else:
    print("No dates available")

# Закрываем соединение с базой данных
conn.close()
