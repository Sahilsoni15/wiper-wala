import sqlite3

def init_db():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()

    # Users table (customers and cleaners)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL -- 'customer', 'cleaner', 'admin'
    )
    ''')

    # Bookings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        flat_type TEXT,
        date TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()