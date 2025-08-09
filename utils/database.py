import sqlite3
from pathlib import Path

# Path to the database file in the project's root directory
DB_FILE = Path(__file__).parent.parent / "user_activity.db"

def init_db():
    """Initializes the database and creates the 'users' table if it doesn't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                message_count INTEGER DEFAULT 0,
                vc_time_minutes INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def get_user_activity(user_id: int) -> tuple[int, int]:
    """
    Retrieves a user's activity stats from the database.
    Returns (message_count, vc_time_minutes).
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message_count, vc_time_minutes FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result if result else (0, 0)

def update_user_activity(user_id: int, messages: int = 0, vc_minutes: int = 0):
    """
    Updates a user's message count and/or voice channel time.
    Creates a new record if the user doesn't exist.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Create user record if it doesn't exist
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        
        # Update the stats
        cursor.execute("""
            UPDATE users
            SET message_count = message_count + ?,
                vc_time_minutes = vc_time_minutes + ?
            WHERE user_id = ?
        """, (messages, vc_minutes, user_id))
        conn.commit()