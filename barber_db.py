import sqlite3

# Автоматичне створення таблиці, якщо її ще немає
def init_db():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            service TEXT,
            time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Функція для додавання нового запису клієнта
def add_appointment(user_id, username, service, time):
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO appointments (user_id, username, service, time) VALUES (?, ?, ?, ?)",
        (user_id, username, service, time)
    )
    conn.commit()
    conn.close()

# Функція для адміна — повертає всі записи з бази
def get_all_appointments():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, service, time FROM appointments")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Запускаємо перевірку бази при старті
init_db()