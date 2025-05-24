import sqlite3

def init_db():
    conn = sqlite3.connect('wiperwala.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user', 'admin', 'cleaner'))
    );
    ''')

    # Create bookings table WITHOUT cleaner_id first if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        flat_type TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Pending', 'Paid', 'Completed'))
        -- cleaner_id will be added separately if missing
    );
    ''')

    # Check if cleaner_id column exists in bookings
    cursor.execute("PRAGMA table_info(bookings);")
    columns = [col[1] for col in cursor.fetchall()]
    if 'cleaner_id' not in columns:
        # Add cleaner_id column (NULLABLE)
        cursor.execute("ALTER TABLE bookings ADD COLUMN cleaner_id INTEGER;")

    # Add foreign keys (SQLite needs PRAGMA foreign_keys=ON in connection to enforce them)
    # But SQLite does not support adding foreign keys after table creation easily
    # For dev, just ensure cleaner_id is there. You can add FK constraints if recreating tables.

    # Insert default admin and cleaner users if not exists
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'adminpass', 'admin')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('cleaner1', 'cleanerpass', 'cleaner')")

    conn.commit()
    conn.close()
    print("Database initialized and updated.")

if __name__ == '__main__':
    init_db()