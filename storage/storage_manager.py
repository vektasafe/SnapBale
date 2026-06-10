# SnapBale — Storage Manager
# Version: 1.0
# Author: James Kabingu

import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from config import SESSION_BASE_PATH, DATABASE_PATH, TEMP_PATH

logger = logging.getLogger(__name__)


class StorageManager:

    def __init__(self):
        self.session_base = Path(SESSION_BASE_PATH)
        self.db_path = DATABASE_PATH
        self.temp_path = Path(TEMP_PATH)

    def initialize_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                item_count INTEGER DEFAULT 0,
                storage_bytes INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                item_number INTEGER NOT NULL,
                captured_at TEXT NOT NULL,
                front_original TEXT,
                back_original TEXT,
                front_edited TEXT,
                back_edited TEXT,
                quality_front TEXT DEFAULT 'pending',
                quality_back TEXT DEFAULT 'pending',
                flagged INTEGER DEFAULT 0,
                flag_reason TEXT,
                processing_time_ms INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized")

    def create_session(self):
        session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        session_path = self.session_base / session_id
        originals_path = session_path / "Originals"
        edited_path = session_path / "Edited"

        originals_path.mkdir(parents=True, exist_ok=True)
        edited_path.mkdir(parents=True, exist_ok=True)

        conn = self._connect()
        conn.execute("""
            INSERT INTO sessions (session_id, started_at, status)
            VALUES (?, ?, 'active')
        """, (session_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        logger.info(f"Session created: {session_id}")
        return session_id, session_path

    def get_item_paths(self, session_id, item_number):
        session_path = self.session_base / session_id
        prefix = f"item_{item_number:03d}"
        return {
            "front_original": str(session_path / "Originals" / f"{prefix}_front_raw.jpg"),
            "back_original":  str(session_path / "Originals" / f"{prefix}_back_raw.jpg"),
            "front_edited":   str(session_path / "Edited" / f"{prefix}_front.jpg"),
            "back_edited":    str(session_path / "Edited" / f"{prefix}_back.jpg"),
            "preview":        str(self.temp_path / f"{session_id}_{prefix}_preview.jpg")
        }

    def save_item_record(self, session_id, item_number, paths,
                         quality_front, quality_back,
                         flagged, flag_reason, processing_time_ms):
        conn = self._connect()
        conn.execute("""
            INSERT INTO items (
                session_id, item_number, captured_at,
                front_original, back_original,
                front_edited, back_edited,
                quality_front, quality_back,
                flagged, flag_reason, processing_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            item_number,
            datetime.now().isoformat(),
            paths["front_original"],
            paths["back_original"],
            paths["front_edited"],
            paths["back_edited"],
            quality_front,
            quality_back,
            1 if flagged else 0,
            flag_reason,
            processing_time_ms
        ))
        conn.execute("""
            UPDATE sessions
            SET item_count = item_count + 1
            WHERE session_id = ?
        """, (session_id,))
        conn.commit()
        conn.close()

    def complete_session(self, session_id):
        conn = self._connect()
        conn.execute("""
            UPDATE sessions
            SET status = 'complete', completed_at = ?
            WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))
        conn.commit()
        conn.close()
        logger.info(f"Session completed: {session_id}")

    def get_session_summary(self, session_id):
        conn = self._connect()
        session = conn.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,)).fetchone()
        items = conn.execute("""
            SELECT * FROM items WHERE session_id = ?
            ORDER BY item_number ASC
        """, (session_id,)).fetchall()
        conn.close()
        return session, items

    def get_flagged_items(self, session_id):
        conn = self._connect()
        items = conn.execute("""
            SELECT * FROM items
            WHERE session_id = ? AND flagged = 1
            ORDER BY item_number ASC
        """, (session_id,)).fetchall()
        conn.close()
        return items

    def get_storage_free(self):
        import shutil
        total, used, free = shutil.disk_usage(SESSION_BASE_PATH)
        return free, total

    def check_incomplete_sessions(self):
        conn = self._connect()
        incomplete = conn.execute("""
            SELECT * FROM sessions WHERE status = 'active'
        """).fetchall()
        conn.close()
        return incomplete

    def mark_session_incomplete(self, session_id):
        conn = self._connect()
        conn.execute("""
            UPDATE sessions SET status = 'incomplete'
            WHERE session_id = ?
        """, (session_id,))
        conn.commit()
        conn.close()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
