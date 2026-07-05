"""
Canvas router — real-time spatial validation when user moves furniture.
Fix: accepts both flat {x,z,width,depth} AND nested {position:{x,z}, size:{width,depth}} formats.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from pydantic import BaseModel

from api.schemas.models import (
    CanvasValidationResponse,
    Agent2Output, FurniturePosition,
)
from services.session_manager import session_manager
from agents import agent4_validator

logger = logging.getLogger(__name__)
router = APIRouter()


class CanvasUpdateRequest(BaseModel):
    session_id: str
    furniture_positions: List[Dict[str, Any]]


def _parse_item(item: dict, session_id: str) -> FurniturePosition:
    """
    Parse furniture item from frontend — handles both formats:
    - Flat:   {id, x, z, width, depth, label?, color?}
    - Nested: {id, position:{x,z}, size:{width,depth}, label?, color?}
    """
    item_id = str(item.get("id", "unknown"))

    # Try nested format first (frontend sends this)
    pos  = item.get("position") or {}
    size = item.get("size") or {}

    if isinstance(pos, dict) and ("x" in pos or "z" in pos):
        x = float(pos.get("x", 0))
        z = float(pos.get("z", 0))
    else:
        x = float(item.get("x", 0))
        z = float(item.get("z", 0))

    if isinstance(size, dict) and ("width" in size or "depth" in size):
        w = float(size.get("width", 50))
        d = float(size.get("depth", 50))
    else:
        w = float(item.get("width", 50))
        d = float(item.get("depth", 50))

    return FurniturePosition(
        id=item_id,
        label=str(item.get("label", item_id)),
        position={"x": x, "z": z},
        size={"width": max(w, 1), "depth": max(d, 1)},
        color=item.get("color"),
    )


@router.post("/update", response_model=CanvasValidationResponse)
async def update_canvas(body: CanvasUpdateRequest):
    """
    Called when user drags/resizes furniture on the canvas.
    Re-runs Agent 4 validation and returns any issues.
    """
    session = session_manager.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_a2 = session.get("agent2")
    if not current_a2:
        raise HTTPException(status_code=400, detail="No layout found. Run full pipeline first.")

    try:
        updated_furniture = [
            _parse_item(item, body.session_id)
            for item in body.furniture_positions
        ]

        room_dims = (
            current_a2.get("room_dimensions")
            if isinstance(current_a2, dict)
            else getattr(current_a2, "room_dimensions", {})
        )

        updated_a2 = Agent2Output(
            session_id=body.session_id,
            room_dimensions=room_dims,
            furniture=updated_furniture,
        )
    except Exception as e:
        logger.error(f"[canvas/update] parse error: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid positions: {e}")

    # Re-run validator
    a4_out, _ = await agent4_validator.run(body.session_id, updated_a2)

    # Persist updated layout
    session_manager.set_agent_output(body.session_id, 2, updated_a2)
    session_manager.set_agent_output(body.session_id, 4, a4_out)

    logger.info(f"[canvas/update] {body.session_id} — {len(updated_furniture)} items, valid={a4_out.is_valid}")

    return CanvasValidationResponse(
        session_id=body.session_id,
        is_valid=a4_out.is_valid,
        issues=a4_out.issues,
        updated_layout=updated_a2,
    )
