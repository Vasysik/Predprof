import sqlite3
import requests

# Функция для подключения к базе данных
def connect_to_database(database_name):
    conn = sqlite3.connect(database_name)
    return conn

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
            for i in windows_for_flat:
                for j in range(int(i)):
                    windows.append(f+j)
            windows.sort()
            f += len(windows_for_flat)

            for win in floor[1]:
                rooms_with_any_light.add(windows[int(win-1)])
                
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


def main(date):
    conn = connect_to_database('room_data.db')
    windows_with_light = find_windows_with_light(conn, date)

    for windows_on_each_floor in windows_with_light:
        for floor_number, floor_rooms in windows_on_each_floor:
            print("Этаж:", floor_number, "Окна:", floor_rooms) 

    flats_and_windows_info = get_flats_and_windows_info(conn, date)

    for room_id, room_info in flats_and_windows_info.items():
        windows_for_flat = room_info['windows_for_flat']

    rooms_with_any_light = find_rooms_with_any_light(windows_with_light, windows_for_flat)
    print("Комнаты, где хотя бы одно окно горит:", rooms_with_any_light)

main('14-02-23')