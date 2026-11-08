import sqlite3
import os
from typing import Optional

# Determine the root directory to place cache.db alongside main.py
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache.db")

def init_db() -> None:
    """Initializes the SQLite database, creating the ApiCache table and indexes if they don't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Create the ApiCache table based on the defined schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ApiCache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                commit_count INTEGER NOT NULL,
                fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create a composite index for O(1) cache lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_dates 
            ON ApiCache (username, start_date, end_date)
        """)
        conn.commit()

def get_cached_commits(username: str, start_date: str, end_date: str) -> Optional[int]:
    """
    Checks if a user's commit count for the exact date range was queried recently.
    Returns the commit_count if found, otherwise None.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT commit_count 
            FROM ApiCache 
            WHERE username = ? AND start_date = ? AND end_date = ?
        """, (username, start_date, end_date))
        
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

def save_to_cache(username: str, start_date: str, end_date: str, commit_count: int) -> None:
    """Inserts a successful API response into the cache database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ApiCache (username, start_date, end_date, commit_count)
            VALUES (?, ?, ?, ?)
        """, (username, start_date, end_date, commit_count))
        conn.commit()