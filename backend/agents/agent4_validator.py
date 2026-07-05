"""
Agent 4: Spatial Validator + Floor Plan Generator
- Validates layout (overlaps, out-of-bounds)
- Generates dark-themed floor plan PNG matching the UI aesthetic
"""
import logging, os
from typing import List, Optional, Tuple

import cv2
import numpy as np

from core.config import settings
from api.schemas.models import Agent2Output, Agent3Output, Agent4Output, ValidationIssue

logger = logging.getLogger(__name__)
CANVAS_SCALE = 2   # px per cm


def _check_overlaps(furniture) -> List[ValidationIssue]:
    issues = []
    for i in range(len(furniture)):
        for j in range(i + 1, len(furniture)):
            a, b = furniture[i], furniture[j]
            ax1, az1 = a.position["x"], a.position["z"]
            ax2, az2 = ax1 + a.size["width"], az1 + a.size["depth"]
            bx1, bz1 = b.position["x"], b.position["z"]
            bx2, bz2 = bx1 + b.size["width"], bz1 + b.size["depth"]
            if ax1 < bx2 and ax2 > bx1 and az1 < bz2 and az2 > bz1:
                issues.append(ValidationIssue(
                    item_id=a.id, issue_type="overlap",
                    description=f"'{a.label}' overlaps with '{b.label}'",
                    suggested_fix=f"Move '{b.label}' at least {int(a.size['width'])}cm away",
                ))
    return issues


def _check_bounds(furniture, room_w: float, room_l: float) -> List[ValidationIssue]:
    issues = []
    for item in furniture:
        x2 = item.position["x"] + item.size["width"]
        z2 = item.position["z"] + item.size["depth"]
        if x2 > room_w or z2 > room_l or item.position["x"] < 0 or item.position["z"] < 0:
            issues.append(ValidationIssue(
                item_id=item.id, issue_type="out_of_bounds",
                description=f"'{item.label}' extends outside the room boundary",
                suggested_fix=f"Reposition '{item.label}' within {room_w}×{room_l}cm",
            ))
    return issues


def _hex_to_bgr(hex_color: str) -> tuple:
    """Convert #RRGGBB (from agent2 palette) → OpenCV BGR."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (100, 100, 100)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)


def _generate_canvas(a2: Agent2Output, output_path: str) -> bool:
    try:
        rd   = a2.room_dimensions
        w_cm = max(float(rd.get("width",  400)), 100)
        l_cm = max(float(rd.get("length", 500)), 100)
        w_px = int(w_cm * CANVAS_SCALE)
        l_px = int(l_cm * CANVAS_SCALE)

        # ── Dark UI-matching palette (BGR) ────────────────────────────────────
        BG       = (28,  26,  24)    # obsidian
        BORDER   = (76,  168, 201)   # gold-accent
        GRID     = (50,  48,  45)    # subtle grid
        TEXT_COL = (200, 200, 200)   # light marble
        LABEL_BG = (45,  43,  40)    # label backdrop

        canvas = np.full((l_px, w_px, 3), BG, dtype=np.uint8)

        # Grid (50-cm steps)
        step = int(50 * CANVAS_SCALE)
        for gx in range(0, w_px, step):
            cv2.line(canvas, (gx, 0), (gx, l_px), GRID, 1)
        for gy in range(0, l_px, step):
            cv2.line(canvas, (0, gy), (w_px, gy), GRID, 1)

        # Room border (double-line)
        cv2.rectangle(canvas, (0, 0), (w_px-1, l_px-1), BORDER, 3)
        cv2.rectangle(canvas, (4, 4), (w_px-5, l_px-5), (60, 55, 50), 1)

        # Dimension label
        cv2.putText(canvas, f"{int(w_cm)}x{int(l_cm)} cm",
                    (8, l_px-8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.35, (100, 90, 80), 1, cv2.LINE_AA)

        for item in a2.furniture:
            # Use agent2's color palette (muted hex), not harsh BGR primaries
            hex_col    = getattr(item, "color", None) or "#8A7A5A"
            bgr        = _hex_to_bgr(hex_col)
            fill_bgr   = tuple(min(int(c * 0.55), 255) for c in bgr)
            border_bgr = bgr

            x  = int(float(item.position.get("x", 0)) * CANVAS_SCALE)
            z  = int(float(item.position.get("z", 0)) * CANVAS_SCALE)
            bw = int(float(item.size.get("width",  50)) * CANVAS_SCALE)
            bd = int(float(item.size.get("depth",  50)) * CANVAS_SCALE)
            x2 = min(x + bw, w_px - 2)
            z2 = min(z + bd, l_px - 2)

            # Shadow → fill → border
            cv2.rectangle(canvas, (x+3, z+3), (x2+3, z2+3), (15, 14, 13), -1)
            cv2.rectangle(canvas, (x, z),     (x2, z2),     fill_bgr,     -1)
            cv2.rectangle(canvas, (x, z),     (x2, z2),     border_bgr,    2)

            # Label (only if box is big enough)
            fw, fh = x2-x, z2-z
            label  = item.label[:14]
            fs, th = 0.32, 1
            if fw > 28 and fh > 18:
                (tw, th2), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, fs, th)
                lx1, ly1 = x+4, z+4
                lx2 = min(lx1 + tw + 6, x2 - 2)
                ly2 = ly1 + th2 + 4
                cv2.rectangle(canvas, (lx1, ly1), (lx2, ly2), LABEL_BG, -1)
                cv2.putText(canvas, label, (lx1+3, ly2-3),
                            cv2.FONT_HERSHEY_SIMPLEX, fs, TEXT_COL, th, cv2.LINE_AA)

        cv2.imwrite(output_path, canvas)
        return True
    except Exception as e:
        logger.error(f"[Agent4] Canvas generation failed: {e}")
        return False


async def run(
    session_id: str,
    a2: Agent2Output,
    a3: Optional[Agent3Output] = None,
) -> Tuple[Agent4Output, str]:
    logger.info(f"[Agent4] Session {session_id} — validating spatial layout")

    rd     = a2.room_dimensions
    room_w = float(rd.get("width",  400))
    room_l = float(rd.get("length", 500))

    issues: List[ValidationIssue] = []
    issues.extend(_check_overlaps(a2.furniture))
    issues.extend(_check_bounds(a2.furniture, room_w, room_l))

    output_dir  = os.path.join(settings.OUTPUTS_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)
    canvas_path = os.path.join(output_dir, "floor_plan.png")
    canvas_ok   = _generate_canvas(a2, canvas_path)
    canvas_url  = f"/outputs/{session_id}/floor_plan.png" if canvas_ok else None

    is_valid = not any(i.issue_type in ("overlap", "out_of_bounds") for i in issues)

    output = Agent4Output(
        session_id=session_id,
        is_valid=is_valid,
        issues=issues,
        canvas_image_path=canvas_url,
    )
    logger.info(f"[Agent4] valid={is_valid}, issues={len(issues)}")
    return output, ""