import sqlite3

DB_NAME = "newsletters.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS newsletters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_newsletter(goal, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO newsletters (goal, content) VALUES (?, ?)",
        (goal, content)
    )

    conn.commit()
    conn.close()

def get_all_newsletters():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, goal, created_at FROM newsletters ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows

def get_newsletter(newsletter_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM newsletters WHERE id=?", (newsletter_id,))
    row = cursor.fetchone()

    conn.close()
    return row[0] if row else "Not found"