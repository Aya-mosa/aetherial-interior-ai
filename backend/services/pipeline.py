"""
Pipeline Orchestrator  (v2 — saves to history on completion/failure)
Runs all 6 agents in sequence, updates session state at each step.
"""

import asyncio, logging, os
from typing import Optional

from api.schemas.models import DesignRequest, TaskStatus
from services.session_manager import session_manager
from services.history_manager import history_manager
from agents import (
    agent1_preprocessing, agent2_spatial, agent3_vision,
    agent4_validator, agent5_prompt, agent6_renderer,
)

logger = logging.getLogger(__name__)

STEPS = [
    (10,  "Analysing room requirements…"),
    (25,  "Calculating optimal furniture placement…"),
    (40,  "Analysing room image with computer vision…"),
    (55,  "Validating spatial layout…"),
    (70,  "Engineering render prompts…"),
    (90,  "Rendering design variations…"),
]


def _resolve_canvas_path(canvas_image_path: Optional[str]) -> str:
    if not canvas_image_path:
        return ""
    try:
        from core.config import settings
        rel = canvas_image_path.lstrip("/")
        if rel.startswith("outputs/"):
            rel = rel[len("outputs/"):]
        full = os.path.join(settings.OUTPUTS_DIR, rel)
        if os.path.exists(full):
            return full
        logger.warning(f"[Pipeline] Canvas not found: {full}")
    except Exception as e:
        logger.warning(f"[Pipeline] Canvas resolve error: {e}")
    return ""


async def run_pipeline(
    session_id: str,
    request: DesignRequest,
    image_path: str,
    num_variations: int = 3,
):
    sm = session_manager
    sm.set_status(session_id, TaskStatus.PROCESSING, STEPS[0][1], STEPS[0][0])

    try:
        # Agent 1
        logger.info(f"[Pipeline] {session_id} — A1")
        a1_out, err = await agent1_preprocessing.run(session_id, request)
        if not a1_out:
            sm.set_error(session_id, f"Agent 1 failed: {err}")
            history_manager.fail(session_id)
            return
        sm.set_agent_output(session_id, 1, a1_out)
        sm.set_status(session_id, TaskStatus.PROCESSING, STEPS[1][1], STEPS[1][0])

        # Agent 2
        logger.info(f"[Pipeline] {session_id} — A2")
        a2_out, err = await agent2_spatial.run(session_id, a1_out)
        if not a2_out:
            sm.set_error(session_id, f"Agent 2 failed: {err}")
            history_manager.fail(session_id)
            return
        sm.set_agent_output(session_id, 2, a2_out)
        sm.set_status(session_id, TaskStatus.PROCESSING, STEPS[2][1], STEPS[2][0])

        # Agent 3 (non-fatal)
        logger.info(f"[Pipeline] {session_id} — A3")
        a3_out: Optional[object] = None
        if image_path:
            a3_out, err = await agent3_vision.run(session_id, image_path)
            if a3_out:
                sm.set_agent_output(session_id, 3, a3_out)
            else:
                logger.warning(f"[Pipeline] A3 skipped: {err}")
        sm.set_status(session_id, TaskStatus.PROCESSING, STEPS[3][1], STEPS[3][0])

        # Agent 4
        logger.info(f"[Pipeline] {session_id} — A4")
        a4_out, err = await agent4_validator.run(session_id, a2_out, a3_out)
        if not a4_out:
            sm.set_error(session_id, f"Agent 4 failed: {err}")
            history_manager.fail(session_id)
            return
        sm.set_agent_output(session_id, 4, a4_out)
        sm.set_status(session_id, TaskStatus.PROCESSING, STEPS[4][1], STEPS[4][0])

        # Agent 5
        logger.info(f"[Pipeline] {session_id} — A5")
        a5_out, err = await agent5_prompt.run(session_id, a1_out, a2_out, a3_out)
        if not a5_out:
            sm.set_error(session_id, f"Agent 5 failed: {err}")
            history_manager.fail(session_id)
            return
        sm.set_agent_output(session_id, 5, a5_out)
        sm.set_status(session_id, TaskStatus.PROCESSING, STEPS[5][1], STEPS[5][0])

        # Agent 6
        logger.info(f"[Pipeline] {session_id} — A6")
        canvas_path = _resolve_canvas_path(a4_out.canvas_image_path if a4_out else None)
        a6_out, err = await agent6_renderer.run(
            session_id=session_id,
            a5=a5_out,
            original_image_path=image_path,
            canvas_path=canvas_path,
            num_variations=num_variations,
        )
        if not a6_out:
            sm.set_error(session_id, f"Agent 6 failed: {err}")
            history_manager.fail(session_id)
            return

        sm.set_agent_output(session_id, 6, a6_out)
        sm.set_status(session_id, TaskStatus.DONE, "Design ready!", 100)
        logger.info(f"[Pipeline] {session_id} — COMPLETE ✓")

        # ── Save to history ───────────────────────────────────────────────────
        if a6_out.variations:
            first = a6_out.variations[0]
            history_manager.complete(
                session_id=session_id,
                thumbnail_url=first.thumbnail_url or first.image_url,
                image_url=first.image_url,
            )

    except Exception as e:
        err = f"Pipeline error: {e}"
        logger.exception(err)
        sm.set_error(session_id, err)
        history_manager.fail(session_id)