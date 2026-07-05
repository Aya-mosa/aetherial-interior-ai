"""
Agent 3: Vision Analyser
Primary:  Gemini (only model that sees images via free key)
Fallback: OpenRouter llama-4-scout (multimodal, free) → text-only defaults
"""
import asyncio, base64, io, json, logging
from pathlib import Path
from typing import Optional, Tuple

import google.generativeai as genai
from PIL import Image

from core.config import settings
from api.schemas.models import Agent3Output
from agents._openrouter import call_vision as or_vision

logger = logging.getLogger(__name__)
MAX_DIM = 1024


def _prepare_image(image_path: str) -> Optional[dict]:
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            w, h = img.size
            if max(w, h) > MAX_DIM:
                ratio = MAX_DIM / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            b64 = base64.b64encode(buf.getvalue()).decode()
            return {"b64": b64, "mime": "image/jpeg"}
    except Exception as e:
        logger.error(f"[Agent3] Image prep failed: {e}")
        return None


VISION_PROMPT = """Analyse this interior room photo. Return ONLY valid JSON — no markdown.

{
  "room_type_detected": "bedroom",
  "estimated_room_shape": "rectangular",
  "wall_colors": ["#F5F5F0"],
  "floor_type": "hardwood",
  "ceiling_height_estimate": "medium (2.5-3m)",
  "openings": {
    "windows_count": 1,
    "doors_count": 1,
    "window_positions": ["north"],
    "door_positions": ["south"]
  },
  "lighting": {
    "primary_source": "Natural Light",
    "time_of_day_estimate": "afternoon",
    "ambient_mood": "Neutral",
    "shadow_direction": "diffuse"
  },
  "existing_furniture": [],
  "design_constraints": {
    "focal_wall": "North Wall",
    "avoid_wall": "none",
    "structural_elements": [],
    "problematic_areas": []
  },
  "image_dimensions": {"aspect_ratio": "16:9", "estimated_room_shape": "rectangular"},
  "style_hints": ["minimalist"],
  "renovation_potential": "high",
  "key_features_to_preserve": []
}"""


def _get(obj, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _default_output(session_id: str) -> Agent3Output:
    """Returns a sensible default when all vision attempts fail."""
    return Agent3Output(
        session_id=session_id,
        openings={"windows_count": 1, "doors_count": 1,
                  "window_positions": ["north"], "door_positions": ["south"]},
        lighting={"primary_source": "Natural Light", "time_of_day_estimate": "afternoon",
                  "ambient_mood": "Neutral", "shadow_direction": "diffuse"},
        design_constraints={"focal_wall": "North Wall", "avoid_wall": "none",
                            "structural_elements": [], "problematic_areas": []},
        image_dimensions={"aspect_ratio": "16:9", "estimated_room_shape": "rectangular"},
        existing_furniture=[],
        wall_colors=["#F5F5F0"],
        floor_type="unknown",
        ceiling_height_estimate="medium (2.5-3m)",
        style_hints=[],
        renovation_potential="medium",
        key_features_to_preserve=[],
        room_type_detected="",
    )


def _parse_vision_json(raw: str, session_id: str) -> Optional[Agent3Output]:
    try:
        start = raw.find("{"); end = raw.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(raw[start:end + 1])
        return Agent3Output(
            session_id=session_id,
            openings=data.get("openings", {}),
            lighting=data.get("lighting", {}),
            design_constraints=data.get("design_constraints", {}),
            image_dimensions=data.get("image_dimensions", {}),
            existing_furniture=data.get("existing_furniture", []),
            wall_colors=data.get("wall_colors", []),
            floor_type=data.get("floor_type", "unknown"),
            ceiling_height_estimate=data.get("ceiling_height_estimate", "medium"),
            style_hints=data.get("style_hints", []),
            renovation_potential=data.get("renovation_potential", "medium"),
            key_features_to_preserve=data.get("key_features_to_preserve", []),
            room_type_detected=data.get("room_type_detected", ""),
        )
    except Exception:
        return None


async def _call_gemini(blob: dict) -> Optional[str]:
    """Primary: Gemini vision (supports real image analysis)."""
    for attempt in range(3):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL.strip(),
                generation_config=genai.types.GenerationConfig(temperature=0.1),
            )
            response = model.generate_content([
                {"mime_type": blob["mime"], "data": blob["b64"]},
                VISION_PROMPT,
            ])
            return response.text.strip()
        except Exception as e:
            if "429" in str(e):
                wait = 20 * (attempt + 1)
                logger.warning(f"[Agent3] Gemini 429 — waiting {wait}s")
                await asyncio.sleep(wait)
            else:
                logger.warning(f"[Agent3] Gemini error: {e}")
                return None
    return None


async def _call_openrouter_vision(blob: dict) -> Optional[str]:
    """Fallback: OpenRouter multimodal models via shared helper."""
    return await or_vision(blob["b64"], blob["mime"], VISION_PROMPT)


async def run(session_id: str, image_path: str) -> Tuple[Optional[Agent3Output], str]:
    logger.info(f"[Agent3] {session_id} — analysing room image")
    await asyncio.sleep(settings.GEMINI_RATE_LIMIT_SLEEP)

    blob = _prepare_image(image_path)
    if not blob:
        logger.warning("[Agent3] Image prep failed — using defaults")
        return _default_output(session_id), ""

    # 1. Gemini (best for vision)
    raw = await _call_gemini(blob)
    result = _parse_vision_json(raw, session_id) if raw else None
    if result:
        wins = _get(result.openings, "windows_count", 0)
        mood = _get(result.lighting, "ambient_mood", "?")
        logger.info(f"[Agent3] ✅ Gemini vision — windows={wins}, mood={mood}")
        return result, ""

    # 2. OpenRouter vision models
    logger.info("[Agent3] Gemini failed — trying OR vision fallback")
    raw = await _call_openrouter_vision(blob)
    result = _parse_vision_json(raw, session_id) if raw else None
    if result:
        logger.info("[Agent3] ✅ OR vision fallback succeeded")
        return result, ""

    # 3. Safe defaults (Agent3 is optional — pipeline continues without it)
    logger.warning("[Agent3] All vision failed — using sensible defaults")
    return _default_output(session_id), ""
