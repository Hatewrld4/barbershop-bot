import sqlite3

conn = sqlite3.connect("barbershop.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    service TEXT,
    time TEXT
)
""")
conn.commit()

def add_appointment(user_id, username, service, time):
    cursor.execute("INSERT INTO appointments (user_id, username, service, time) VALUES (?, ?, ?, ?)", 
                   (user_id, username, service, time))
    conn.commit()