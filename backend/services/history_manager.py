"""
History Manager — SQLite-based per-user design history.
Stores session metadata (style, room_type, thumbnail) keyed by user_id.
"""

import logging, os, sqlite3, time
from typing import Dict, List, Optional

logger   = logging.getLogger(__name__)
DB_PATH  = os.path.join("pipeline_data", "history.db")


class HistoryManager:
    def __init__(self):
        os.makedirs("pipeline_data", exist_ok=True)
        self._init_db()

    # ── internal ──────────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS designs (
                    session_id    TEXT PRIMARY KEY,
                    user_id       TEXT NOT NULL,
                    created_at    REAL NOT NULL,
                    style         TEXT,
                    room_type     TEXT,
                    thumbnail_url TEXT,
                    image_url     TEXT,
                    status        TEXT DEFAULT 'pending'
                )
            """)
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_created
                ON designs (user_id, created_at DESC)
            """)
        logger.info("[History] DB ready")

    # ── public API ────────────────────────────────────────────────────────────

    def create(
        self,
        session_id: str,
        user_id: str,
        style: str,
        room_type: str,
    ) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT OR IGNORE INTO designs
                   (session_id, user_id, created_at, style, room_type, status)
                   VALUES (?, ?, ?, ?, ?, 'pending')""",
                (session_id, user_id, time.time(), style, room_type),
            )

    def complete(
        self,
        session_id: str,
        thumbnail_url: str,
        image_url: str,
    ) -> None:
        with self._conn() as c:
            c.execute(
                """UPDATE designs
                   SET thumbnail_url=?, image_url=?, status='done'
                   WHERE session_id=?""",
                (thumbnail_url, image_url, session_id),
            )

    def fail(self, session_id: str) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE designs SET status='failed' WHERE session_id=?",
                (session_id,),
            )

    def get_user_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT * FROM designs
                   WHERE user_id=?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, session_id: str, user_id: str) -> bool:
        with self._conn() as c:
            res = c.execute(
                "DELETE FROM designs WHERE session_id=? AND user_id=?",
                (session_id, user_id),
            )
        return res.rowcount > 0

    def get_user_id_for_session(self, session_id: str) -> Optional[str]:
        with self._conn() as c:
            row = c.execute(
                "SELECT user_id FROM designs WHERE session_id=?",
                (session_id,),
            ).fetchone()
        return row["user_id"] if row else None


history_manager = HistoryManager()