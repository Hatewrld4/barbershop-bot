import sqlite3

def init_db():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    
    # Таблиця для записів клієнтів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            service TEXT,
            time TEXT
        )
    ''')
    
    # Таблиця для вільних слотів часу (динамічна)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS working_hours (
            time_slot TEXT PRIMARY KEY
        )
    ''')
    
    # Заповнюємо початковий час за замовчуванням, якщо таблиця порожня
    cursor.execute("SELECT COUNT(*) FROM working_hours")
    if cursor.fetchone()[0] == 0:
        default_times = [("10:00",), ("12:00",), ("15:00",), ("17:00",)]
        cursor.executemany("INSERT INTO working_hours VALUES (?)", default_times)
        
    conn.commit()
    conn.close()

def add_appointment(user_id, username, service, time):
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO appointments (user_id, username, service, time) VALUES (?, ?, ?, ?)",
        (user_id, username, service, time)
    )
    conn.commit()
    conn.close()

def get_all_appointments():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, service, time FROM appointments")
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- НОВІ ФУНКЦІЇ ДЛЯ КЕРУВАННЯ ЧАСОМ ---

def get_working_hours():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()
    cursor.execute("SELECT time_slot FROM working_hours ORDER BY time_slot")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_working_hour(time_slot):
    try:
        conn = sqlite3.connect('barber.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO working_hours VALUES (?)", (time_slot,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False # такий час вже є

init_db()