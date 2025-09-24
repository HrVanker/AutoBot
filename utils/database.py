import sqlite3
from pathlib import Path
from typing import List
from datetime import datetime
from utils import schema

# Path to the database file in the project's root directory
DB_FILE = Path("/data/server_activity.db")

def init_db():
    """Initializes the database using the centralized schema."""
    schema.initialize_database()

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
    """
    Calculates a user's activity stats on-the-fly from the event tables.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # 1. Get total message count by counting rows
        cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = ?", (user_id,))
        message_count = cursor.fetchone()[0]
        
        # 2. Calculate total VC time by pairing join/leave events
        cursor.execute(
            "SELECT event_type, timestamp FROM vc_events WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,)
        )
        events = cursor.fetchall()
        
        total_seconds = 0
        join_time = None
        
        for event_type, timestamp_str in events:
            # Parse the ISO format timestamp string into a datetime object
            event_time = datetime.fromisoformat(timestamp_str)
            
            if event_type == 'join':
                # If we see a join, record the time
                join_time = event_time
            elif event_type == 'leave' and join_time:
                # If we see a leave and have a previous join time, calculate the duration
                duration = event_time - join_time
                total_seconds += duration.total_seconds()
                join_time = None # Reset for the next session
        
        vc_time_minutes = int(total_seconds // 60)
        
        return message_count, vc_time_minutes

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