import sqlite3

# Connect to DB
conn = sqlite3.connect('bookings.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# View users table
cursor.execute("SELECT * FROM users;")
for row in cursor.fetchall():
    print(row)

conn.close()