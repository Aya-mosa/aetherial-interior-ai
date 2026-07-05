"""
Agent 2: Spatial Planner
Primary:  OpenRouter DeepSeek-R1 (best for JSON/spatial reasoning, free)
Fallback: Gemini (with retry) → other OR models
"""
import json
import logging
import asyncio
from typing import Tuple, Optional

import google.generativeai as genai

from core.config import settings
from api.schemas.models import Agent1Output, Agent2Output, FurniturePosition
from agents._openrouter import call as or_call

logger = logging.getLogger(__name__)

FURNITURE_COLORS = [
    "#C8873A", "#4A7C59", "#5B7FA6", "#9B5EA2",
    "#A25E5E", "#6B8E6B", "#7A7A9B", "#B8934A",
]

SYSTEM_PROMPT = """You are a Spatial Planning AI for interior design.
You must always respond with valid JSON only — no markdown, no explanation, no preamble.
You are expert at calculating non-overlapping furniture positions within room boundaries."""


def _build_prompt(a1: Agent1Output) -> str:
    w = a1.dimensions.width_cm
    l = a1.dimensions.length_cm
    style = a1.style_preference
    furniture = ", ".join(a1.selected_furniture)
    ai_mode = a1.ai_mode.value

    mode_rule = (
        "STRICT: Place ONLY the exact furniture items listed. Zero additions."
        if ai_mode == "strict"
        else f"CREATIVE: Add 1-2 complementary items that suit a {style} room."
    )

    return f"""Room: {w}cm wide × {l}cm long. Style: {style}.
Furniture requested: {furniture}.
Mode: {mode_rule}

HARD RULES:
1. ALL items must fit within {w}×{l} boundary.
2. NO overlapping bounding boxes.
3. Minimum 30cm clearance between items.
4. Output ONLY valid JSON. No markdown.

SCHEMA:
{{
  "room_dimensions": {{"width": {w}, "length": {l}}},
  "furniture": [
    {{"id": "bed", "label": "Queen Bed", "position": {{"x": 10, "z": 10}}, "size": {{"width": 180, "depth": 200}}}}
  ]
}}"""


def _parse_response(raw: str, session_id: str) -> Optional[Agent2Output]:
    # Strip DeepSeek <think> tags if present
    if "<think>" in raw:
        end_think = raw.find("</think>")
        if end_think != -1:
            raw = raw[end_think + 8:]

    start = raw.find("{"); end = raw.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return None

    furniture_raw = data.get("furniture", [])
    furniture = []
    for idx, item in enumerate(furniture_raw):
        pos  = item.get("position", {})
        size = item.get("size", {})
        w    = max(float(size.get("width", 50)), 20)
        d    = max(float(size.get("depth", 50)), 20)
        furniture.append(FurniturePosition(
            id=str(item.get("id", f"item_{idx}")),
            label=str(item.get("label", "Item")),
            position={"x": float(pos.get("x", 0)), "z": float(pos.get("z", 0))},
            size={"width": w, "depth": d},
            color=FURNITURE_COLORS[idx % len(FURNITURE_COLORS)],
        ))

    return Agent2Output(
        session_id=session_id,
        room_dimensions=data.get("room_dimensions", {}),
        furniture=furniture,
    )


async def _call_openrouter(a1: Agent1Output) -> Optional[str]:
    """Primary: OpenRouter DeepSeek-R1 (best for spatial JSON reasoning)."""
    return await or_call(
        role="agent2",
        system=SYSTEM_PROMPT,
        user=_build_prompt(a1),
        temperature=0.1,
        max_tokens=2048,
    )


async def _call_gemini(a1: Agent1Output) -> Optional[str]:
    """Fallback: Gemini with retry on 429."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL.strip(),
        generation_config=genai.types.GenerationConfig(
            temperature=settings.GEMINI_TEMPERATURE, top_p=0.95,
        ),
    )
    prompt = _build_prompt(a1)
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e):
                wait = 20 * (attempt + 1)
                logger.warning(f"[Agent2] Gemini 429 — waiting {wait}s")
                await asyncio.sleep(wait)
            else:
                logger.warning(f"[Agent2] Gemini error: {e}")
                return None
    return None


async def run(session_id: str, a1: Agent1Output) -> Tuple[Optional[Agent2Output], str]:
    logger.info(f"[Agent2] Session {session_id} — generating spatial layout")

    # 1. OpenRouter first (DeepSeek-R1 is excellent for structured JSON)
    raw = await _call_openrouter(a1)
    result = _parse_response(raw, session_id) if raw else None

    # 2. Gemini fallback
    if not result:
        logger.info("[Agent2] OR failed — trying Gemini fallback")
        await asyncio.sleep(settings.GEMINI_RATE_LIMIT_SLEEP)
        raw = await _call_gemini(a1)
        result = _parse_response(raw, session_id) if raw else None

    # 3. Hard fallback — generate a basic layout without AI
    if not result:
        logger.warning("[Agent2] All AI failed — using rule-based layout")
        result = _rule_based_layout(session_id, a1)

    logger.info(f"[Agent2] Session {session_id} — {len(result.furniture)} items placed")
    return result, ""


def _rule_based_layout(session_id: str, a1: Agent1Output) -> Agent2Output:
    """
    Emergency fallback: places furniture in a simple grid without AI.
    Always succeeds — never returns None.
    """
    w = a1.dimensions.width_cm
    l = a1.dimensions.length_cm
    furniture = []

    # Predefined sizes per furniture type (cm)
    size_map = {
        "bed": (180, 210), "sofa": (220, 90), "dining table": (160, 90),
        "coffee table": (120, 60), "desk": (140, 70), "wardrobe": (180, 60),
        "tv unit": (160, 45), "bookshelf": (100, 35), "armchair": (85, 85),
        "dresser": (120, 50),
    }

    x_cursor, z_cursor = 20, 20
    row_height = 0

    for idx, name in enumerate(a1.selected_furniture):
        key = name.lower()
        fw, fd = size_map.get(key, (100, 80))

        # Wrap to next row if needed
        if x_cursor + fw > w - 20:
            x_cursor = 20
            z_cursor += row_height + 40
            row_height = 0

        if z_cursor + fd > l - 20:
            break  # Room full

        furniture.append(FurniturePosition(
            id=key.replace(" ", "_"),
            label=name,
            position={"x": float(x_cursor), "z": float(z_cursor)},
            size={"width": float(fw), "depth": float(fd)},
            color=FURNITURE_COLORS[idx % len(FURNITURE_COLORS)],
        ))

        x_cursor += fw + 40
        row_height = max(row_height, fd)

    return Agent2Output(
        session_id=session_id,
        room_dimensions={"width": w, "length": l},
        furniture=furniture,
    )
