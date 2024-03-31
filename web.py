from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Функция для подключения к базе данных
def connect_to_database():
    conn = sqlite3.connect('room_data.db')
    return conn

# Функция для получения уникальных дат из таблицы room_data
def get_available_dates():
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT date
        FROM room_data
    """)
    dates = cursor.fetchall()
    conn.close()
    return [date[0] for date in dates]

# Функция для получения данных о комнатах и окнах по заданной дате
def get_room_data_by_date(date):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT windows
        FROM room_data
        WHERE date = ?
    """, (date,))
    room_data_str = cursor.fetchone()
    conn.close()
    return eval(room_data_str[0]) if room_data_str else None

# Функция для получения ответов на задачу по заданным датам
def get_task_answers(date):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data
        FROM json_text
        WHERE date = ?
    """, (date,))
    answers = cursor.fetchone()
    conn.close()
    return answers if answers else None

# Основной маршрут для отображения интерфейса
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_date = request.form['selected_date']
        room_data = get_room_data_by_date(selected_date)
        task_answers = get_task_answers(selected_date)
        return render_template('index.html', room_data=room_data, task_answers=task_answers, available_dates=get_available_dates(), selected_date=selected_date)
    return render_template('index.html', available_dates=get_available_dates())

if __name__ == '__main__':
    app.run(debug=True)
