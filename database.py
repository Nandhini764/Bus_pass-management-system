import sqlite3

def create_tables():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # Create bus_passes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_passes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            route TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Insert a default admin user for testing
    # Password is 'admin' (hashed)
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        admin_password_hash = "sha256$zG55u4Qf$36573c9f2258d55c765796067b848c081e7d2350a4b7325656112999e5250493" # 'admin'
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                       ('admin', admin_password_hash, 1))

    conn.commit()
    conn.close()
    print("Database tables created and default admin user added.")

if __name__ == '__main__':
    create_tables()