"""
History router  — GET /api/history/{user_id}
                — DELETE /api/history/{user_id}/{session_id}
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.history_manager import history_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class HistoryEntry(BaseModel):
    session_id:    str
    user_id:       str
    created_at:    float
    style:         str | None = None
    room_type:     str | None = None
    thumbnail_url: str | None = None
    image_url:     str | None = None
    status:        str        = "pending"


@router.get("/{user_id}", response_model=List[HistoryEntry])
async def get_history(user_id: str, limit: int = 20):
    if not user_id or len(user_id) > 64:
        raise HTTPException(status_code=422, detail="Invalid user_id")
    entries = history_manager.get_user_history(user_id, limit=min(limit, 50))
    return entries


@router.delete("/{user_id}/{session_id}")
async def delete_history_entry(user_id: str, session_id: str):
    deleted = history_manager.delete(session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"ok": True}