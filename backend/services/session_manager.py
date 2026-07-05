"""
Session Manager — stores pipeline state per user session.

In production: swap `_sessions` dict with Redis.
For now: in-memory dict + optional JSON persistence to disk.

New in this version:
  • 'created_at_timestamp' field (Unix epoch float) for TTL-based cleanup
  • cleanup_old_sessions(max_age_seconds) — call periodically from a background task
"""

import asyncio
import logging
import os
import shutil
import time
import uuid
from typing import Any, Dict, Optional

from core.config import settings
from api.schemas.models import TaskStatus

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "id": session_id,
            "status": TaskStatus.PENDING,
            # ISO string for display / logging
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            # Unix timestamp used for TTL arithmetic
            "created_at_timestamp": time.monotonic(),
            "current_step": None,
            "progress_percent": 0,
            "agent1": None,
            "agent2": None,
            "agent3": None,
            "agent4": None,
            "agent5": None,
            "agent6": None,
            "error": None,
        }
        # Create per-session output directory on disk
        session_dir = os.path.join(settings.OUTPUTS_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        logger.debug(f"[SessionManager] New session: {session_id}")
        return session_id

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        """Remove a session from memory and delete its files from disk."""
        self._sessions.pop(session_id, None)

        for base_dir in (settings.OUTPUTS_DIR, settings.UPLOADS_DIR):
            session_dir = os.path.join(base_dir, session_id)
            if os.path.isdir(session_dir):
                try:
                    shutil.rmtree(session_dir)
                    logger.debug(
                        f"[SessionManager] Deleted files for session {session_id} "
                        f"at {session_dir}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[SessionManager] Could not delete {session_dir}: {e}"
                    )

    # ── State mutators ────────────────────────────────────────────────────────

    def set_status(
        self,
        session_id: str,
        status: TaskStatus,
        step: Optional[str] = None,
        progress: int = 0,
    ):
        session = self._sessions.get(session_id)
        if session:
            session["status"] = status
            session["current_step"] = step
            session["progress_percent"] = progress

    def set_agent_output(self, session_id: str, agent: int, data: Any):
        """Store the Pydantic model output (or plain dict) for a given agent."""
        session = self._sessions.get(session_id)
        if session:
            key = f"agent{agent}"
            session[key] = (
                data.model_dump() if hasattr(data, "model_dump") else data
            )

    def set_error(self, session_id: str, error: str):
        session = self._sessions.get(session_id)
        if session:
            session["status"] = TaskStatus.FAILED
            session["error"] = error
            logger.error(f"[SessionManager] Session {session_id} failed: {error}")

    # ── Path helpers ──────────────────────────────────────────────────────────

    def get_upload_path(self, session_id: str) -> str:
        path = os.path.join(settings.UPLOADS_DIR, session_id)
        os.makedirs(path, exist_ok=True)
        return path

    def get_output_path(self, session_id: str) -> str:
        path = os.path.join(settings.OUTPUTS_DIR, session_id)
        os.makedirs(path, exist_ok=True)
        return path

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def cleanup_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """
        Delete sessions (and their files) that are older than `max_age_seconds`.

        Uses the monotonic 'created_at_timestamp' stored at session creation.
        Returns the number of sessions removed.

        Call this from a FastAPI startup lifespan background task:

            asyncio.create_task(_periodic_cleanup())

        or from an APScheduler / cron job.
        """
        now = time.monotonic()
        expired = [
            sid
            for sid, data in list(self._sessions.items())
            if (now - data.get("created_at_timestamp", now)) > max_age_seconds
        ]

        for sid in expired:
            logger.info(f"[SessionManager] Cleaning up expired session: {sid}")
            self.delete(sid)

        if expired:
            logger.info(
                f"[SessionManager] Cleanup complete — removed {len(expired)} session(s)"
            )
        return len(expired)

    async def cleanup_old_sessions_async(self, max_age_seconds: int = 3600) -> int:
        """Async-safe version — acquires the internal lock before iterating."""
        async with self._lock:
            return self.cleanup_old_sessions(max_age_seconds)


# ── Singleton ─────────────────────────────────────────────────────────────────
session_manager = SessionManager()


# ── Background cleanup task (attach to FastAPI lifespan) ─────────────────────

async def periodic_cleanup_task(interval_seconds: int = 600, max_age_seconds: int = 3600):
    """
    Runs cleanup every `interval_seconds` (default: 10 min).
    Wire this up in your FastAPI app lifespan:

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            task = asyncio.create_task(
                periodic_cleanup_task(interval_seconds=600, max_age_seconds=3600)
            )
            yield
            task.cancel()
    """
    logger.info(
        f"[SessionManager] Periodic cleanup started "
        f"(every {interval_seconds}s, TTL={max_age_seconds}s)"
    )
    while True:
        await asyncio.sleep(interval_seconds)
        removed = await session_manager.cleanup_old_sessions_async(max_age_seconds)
        logger.debug(f"[SessionManager] Periodic cleanup removed {removed} session(s)")