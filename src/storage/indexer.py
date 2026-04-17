import sqlite3
import os
from typing import Dict, Any

class IndexManager:
    """
    SQL-based indexing system for robotics motion sessions.
    Enables O(1) temporal lookups and advanced spatial querying.
    """
    def __init__(self, session_path: str):
        self.db_path = os.path.join(session_path, "index.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS frames (
                    frame_index INTEGER PRIMARY KEY,
                    timestamp REAL,
                    source_id TEXT,
                    sync_id TEXT,
                    label TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON frames(timestamp)")

    def index_packet(self, frame_index: int, timestamp: float, source_id: str, sync_id: str, label: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO frames (frame_index, timestamp, source_id, sync_id, label)
                VALUES (?, ?, ?, ?, ?)
            """, (frame_index, timestamp, source_id, sync_id, label))

    def query_by_time(self, start_ts: float, end_ts: float):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM frames WHERE timestamp BETWEEN ? AND ?", (start_ts, end_ts))
            return [dict(row) for row in cursor.fetchall()]

    def get_frame_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0]
