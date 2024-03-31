import sqlite3
import requests
import json
import natsort
from collections import defaultdict
from collections import Counter


# Функция для подключения к базе данных
def connect_to_database(database_name):
    conn = sqlite3.connect(database_name)
    return conn

def get_unique_dates(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT date
        FROM room_data
    """)
    unique_dates = [row[0] for row in cursor.fetchall()]
    return unique_dates

# Функция для поиска номеров комнат, в которых горит свет
def find_windows_with_light(conn, date):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, windows
        FROM room_data
        WHERE date = ?
    """, (date,))
    window_with_light = []
    for row in cursor.fetchall():
        window_id, windows_data = row
        windows = eval(windows_data)  # Преобразование строки с данными об окнах в словарь
        window_on_each_floor = []
        for floor, lights in windows.items():
            floor_number = int(floor.split("_")[1])
            floor_lights = [index + 1 for index, light in enumerate(lights) if light]
            window_on_each_floor.append([floor_number, floor_lights])
        window_with_light.append(window_on_each_floor)
    return window_with_light

def find_rooms_with_any_light(windows_with_light, windows_for_flat):
    rooms_with_any_light = set()
    for windows_on_each_floor in windows_with_light:
        f = 1
        for floor in windows_on_each_floor:
            
            windows = []
            for num in range(len(windows_for_flat)):
                windows.extend([num] * windows_for_flat[num])

            count = defaultdict(int)
            result = []
            label_count = f

            for item in windows:
                if item not in count:
                    count[item] = label_count
                    label_count += 1
                result.append(count[item])

            f += len(windows_for_flat)

            for win in floor[1]:
                rooms_with_any_light.add(result[int(win-1)])
                
    return rooms_with_any_light

def get_flats_and_windows_info(conn, date):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, flats_count, windows_for_flat
        FROM room_data
        WHERE date = ?
    """, (date,))
    flats_and_windows_info = {}
    for row in cursor.fetchall():
        room_id, flats_count, windows_for_flat = row
        flats_and_windows_info[room_id] = {'flats_count': flats_count, 'windows_for_flat': eval(windows_for_flat)}
    return flats_and_windows_info 

def send_post_request(data):
    url = f"https://olimp.miet.ru/ppo_it_final"
    headers = {"X-Auth-Token": "ppo_10_17129"}  # Замените на свой логин
    response = requests.post(url, json=data, headers=headers)
    return response

def build_json_for_check(rooms_with_any_light, date):
    data = {
        "data": {
            "count": len(rooms_with_any_light),
            "rooms": natsort.natsorted(list(rooms_with_any_light))
        },
        "date": date  # Замените на нужную вам дату
    }
    return data

def sort_windows_with_light(windows_with_light):
    sorted_windows_with_light = []
    for floor_windows in windows_with_light:
        sorted_floor_windows = sorted(floor_windows, key=lambda x: x[0])
        sorted_windows_with_light.append(sorted_floor_windows)
    sorted_windows_with_light.sort(key=lambda x: x[0][0])
    return sorted_windows_with_light

def main(date):
    conn = connect_to_database('room_data.db')
    windows_with_light = find_windows_with_light(conn, date)
    windows_with_light = sort_windows_with_light(windows_with_light)
    
    # for windows_on_each_floor in windows_with_light:
    #     for floor_number, floor_rooms in windows_on_each_floor:
    #         print("Этаж:", floor_number, "Окна:", floor_rooms) 

    flats_and_windows_info = get_flats_and_windows_info(conn, date)

    for room_id, room_info in flats_and_windows_info.items():
        windows_for_flat = room_info['windows_for_flat']

    rooms_with_any_light = find_rooms_with_any_light(windows_with_light, windows_for_flat)
    
    json_data = build_json_for_check(rooms_with_any_light, date)
    # print(json_data)
    response = send_post_request(json_data)
    if response.status_code == 200:
        print("Ответ сервера:", response.json()["message"])
    else:
        print("Произошла ошибка при отправке запроса:", response.status_code)
    return(json_data)

def save_json_data_to_table(conn, json_data):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS json_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            date TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO json_text (data, date)
        VALUES (?, ?)
    """, (json.dumps(json_data), json_data['date']))  # Вставляем данные и дату в таблицу
    conn.commit()

conn = connect_to_database('room_data.db')
unique_dates = get_unique_dates(conn)


# json_data = main('14-03-23')
# save_json_data_to_table(conn, json_data)

for date in unique_dates:
    json_data = main(date)
    save_json_data_to_table(conn, json_data)

