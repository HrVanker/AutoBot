import sqlite3
from pathlib import Path
from typing import List

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
        # Stores the last known roles for a user. This is what we'll use for re-assignment.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER PRIMARY KEY,
                role_ids TEXT
            )
        ''')
        # Stores a complete history of every role change.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_history (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role_id INTEGER,
                action TEXT, -- 'added' or 'removed'
                source TEXT, -- 'System (Auto)', 'Moderator (@username)', 'User (Reaction Role)', etc.
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
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

def update_user_roles(user_id: int, role_ids: List[str]):
    """Saves the current list of role IDs for a user."""
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    # Join the list of IDs into a single comma-separated string
    roles_str = ",".join(role_ids)
    c.execute("INSERT OR REPLACE INTO user_roles (user_id, role_ids) VALUES (?, ?)", (user_id, roles_str))
    conn.commit()
    conn.close()

def get_user_roles(user_id: int) -> List[str]:
    """Retrieves the list of saved role IDs for a user."""
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT role_ids FROM user_roles WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        # Split the string back into a list of IDs
        return result[0].split(',')
    return []

def log_role_change(user_id: int, role_id: int, action: str, source: str):
    """Logs a single role change to the history table."""
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO role_history (user_id, role_id, action, source) VALUES (?, ?, ?, ?)",
        (user_id, role_id, action, source)
    )
    conn.commit()
    conn.close()