import sqlite3
from pathlib import Path
from typing import List
from datetime import datetime

# Path to the database file in the project's root directory
DB_FILE = Path(__file__).parent.parent / "data" / "user_activity.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                message_count INTEGER DEFAULT 0,
                vc_time_minutes INTEGER DEFAULT 0
            )
        """)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER PRIMARY KEY,
                role_ids TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_history (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role_id INTEGER,
                action TEXT,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vc_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                event_type TEXT NOT NULL, -- "join" or "leave"
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
    CREATE TABLE IF NOT EXISTS reactions (
        reaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        message_id INTEGER NOT NULL,
        emoji TEXT NOT NULL,
        event_type TEXT NOT NULL, -- "add" or "remove"
        timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_state_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                event_type TEXT NOT NULL, -- "mute", "unmute", "deafen", etc.
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                event_type TEXT NOT NULL, -- "edit" or "delete"
                timestamp TEXT NOT NULL,
                original_content TEXT
            )
        ''')

def log_message(user_id: int, channel_id: int):
    """Logs a single message event to the database."""
    with sqlite3.connect(DB_FILE) as conn:
        timestamp = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO messages (user_id, channel_id, timestamp) VALUES (?, ?, ?)",
            (user_id, channel_id, timestamp)
        )

def log_vc_event(user_id: int, channel_id: int, event_type: str):
    """Logs a voice channel join or leave event."""
    with sqlite3.connect(DB_FILE) as conn:
        timestamp = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO vc_events (user_id, channel_id, event_type, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, channel_id, event_type, timestamp)
        )

def get_user_activity(user_id: int) -> tuple[int, int]:
    """Retrieves a user's activity stats from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message_count, vc_time_minutes FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result if result else (0, 0)

def update_user_activity(user_id: int, messages: int = 0, vc_minutes: int = 0):
    """Updates a user's message count and/or voice channel time."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        cursor.execute("""
            UPDATE users
            SET message_count = message_count + ?,
                vc_time_minutes = vc_time_minutes + ?
            WHERE user_id = ?
        """, (messages, vc_minutes, user_id))

# ▼▼▼ CORRECTED FUNCTIONS ▼▼▼

def update_user_roles(user_id: int, role_ids: List[str]):
    """Saves the current list of role IDs for a user."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        roles_str = ",".join(role_ids)
        cursor.execute("INSERT OR REPLACE INTO user_roles (user_id, role_ids) VALUES (?, ?)", (user_id, roles_str))

def get_user_roles(user_id: int) -> List[str]:
    """Retrieves the list of saved role IDs for a user."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role_ids FROM user_roles WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0].split(',')
        return []

def log_role_change(user_id: int, role_id: int, action: str, source: str):
    """Logs a single role change to the history table."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO role_history (user_id, role_id, action, source) VALUES (?, ?, ?, ?)",
            (user_id, role_id, action, source)
        )

def log_reaction(user_id: int, channel_id: int, message_id: int, emoji: str, event_type: str):
    """Logs a reaction add or remove event."""
    with sqlite3.connect(DB_FILE) as conn:
        timestamp = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO reactions (user_id, channel_id, message_id, emoji, event_type, timestamp) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, channel_id, message_id, str(emoji), event_type, timestamp)
        )

def log_voice_state_event(user_id: int, channel_id: int, event_type: str):
    """Logs a voice state change event like mute, deafen, etc."""
    with sqlite3.connect(DB_FILE) as conn:
        timestamp = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO voice_state_events (user_id, channel_id, event_type, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, channel_id, event_type, timestamp)
        )

def log_message_event(message_id: int, user_id: int, channel_id: int, event_type: str, content: str = None):
    """Logs a message edit or delete event."""
    with sqlite3.connect(DB_FILE) as conn:
        timestamp = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO message_events (message_id, user_id, channel_id, event_type, timestamp, original_content) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_id, user_id, channel_id, event_type, timestamp, content)
        )