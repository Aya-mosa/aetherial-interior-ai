"""
Agent 5: Prompt Engineer
Primary:  OpenRouter Llama-3.3-70B (best for creative language, free)
Fallback: Gemini → DeepSeek → hard-coded prompt builder

FIX (v5): model.generate_content() is a BLOCKING sync call — no async client
exists in google.generativeai. Calling it directly inside `async def` freezes
the whole event loop for the entire Gemini round-trip, which was causing 502
Bad Gateway on Railway. Fixed via asyncio.to_thread().
"""
import asyncio, json, logging
from typing import Optional, Tuple

import google.generativeai as genai

from core.config import settings
from api.schemas.models import Agent1Output, Agent2Output, Agent3Output, Agent5Output
from agents._openrouter import call as or_call

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a world-class interior design prompt engineer.
Create precise, photorealistic image generation prompts.
Always respond with valid JSON only — no markdown, no preamble."""


def _val(obj) -> str:
    if hasattr(obj, "value"): return str(obj.value)
    return str(obj)


def _get(obj, key: str, default=None):
    if isinstance(obj, dict): return obj.get(key, default)
    return getattr(obj, key, default)


def _build_prompt(a1, a2, a3) -> str:
    style     = _val(a1.style_preference)
    room_type = _val(a1.room_type)
    palette   = _val(a1.color_palette)
    mode      = _val(a1.ai_mode)
    w, l      = a1.dimensions.width_cm, a1.dimensions.length_cm
    furniture = [f.label for f in (a2.furniture or [])]

    room_ctx = ""
    if a3:
        wins     = _get(a3.openings,           "windows_count",  1)
        doors    = _get(a3.openings,           "doors_count",    1)
        light    = _get(a3.lighting,           "primary_source", "Natural Light")
        mood     = _get(a3.lighting,           "ambient_mood",   "Neutral")
        focal    = _get(a3.design_constraints, "focal_wall",     "North Wall")
        preserve = getattr(a3, "key_features_to_preserve", []) or []
        hints    = getattr(a3, "style_hints",  []) or []
        floor    = getattr(a3, "floor_type",   "") or ""
        walls    = getattr(a3, "wall_colors",  []) or []
        room_ctx = f"""
ROOM ANALYSIS (from photo):
- Windows: {wins}, Doors: {doors}
- Lighting: {light}, Mood: {mood}
- Focal wall: {focal}
- Floor: {floor or 'unknown'}
- Wall tones: {', '.join(walls) if walls else 'neutral'}
- Style hints: {', '.join(hints) if hints else 'none'}
- Preserve: {', '.join(preserve) if preserve else 'nothing specific'}"""

    return f"""Create a precise image generation prompt for this interior design project.

DESIGN SPECS:
- Room: {room_type} ({w}×{l}cm)
- Style: {style}
- Colour palette: {palette}
- AI mode: {mode}
- Furniture: {', '.join(furniture) if furniture else 'as appropriate'}
{room_ctx}

Return ONLY this JSON (no markdown):
{{
  "positive_prompt": "photorealistic {style.lower()} {room_type.lower()}, {palette.lower()}, detailed description...",
  "negative_prompt": "ugly, blurry, distorted, watermark, people, text",
  "style_keywords": "keyword1, keyword2, keyword3",
  "lighting_description": "one sentence about lighting"
}}"""


def _parse(raw: str, session_id: str) -> Optional[Agent5Output]:
    if not raw: return None
    # Strip DeepSeek think tags
    if "<think>" in raw:
        end = raw.find("</think>")
        if end != -1: raw = raw[end + 8:]
    try:
        start = raw.find("{"); end = raw.rfind("}")
        if start == -1 or end == -1: return None
        data = json.loads(raw[start:end + 1])
        return Agent5Output(
            session_id=session_id,
            positive_prompt=data.get("positive_prompt", ""),
            negative_prompt=data.get("negative_prompt", ""),
            style_keywords=data.get("style_keywords", ""),
            lighting_description=data.get("lighting_description", ""),
        )
    except Exception:
        return None


def _fallback_prompt(session_id: str, a1, a2, a3) -> Agent5Output:
    """Emergency: build a good prompt without AI."""
    style     = _val(a1.style_preference)
    room_type = _val(a1.room_type)
    palette   = _val(a1.color_palette)
    furniture = ", ".join([f.label for f in (a2.furniture or [])])
    light     = "Natural Light"
    if a3:
        light = _get(a3.lighting, "primary_source", "Natural Light")

    return Agent5Output(
        session_id=session_id,
        positive_prompt=(
            f"photorealistic {style.lower()} {room_type.lower()} interior design, "
            f"{palette.lower()} color scheme, {furniture}, {light.lower()}, "
            f"professional interior photography, 8k resolution, "
            f"high detail, architectural render"
        ),
        negative_prompt="ugly, blurry, distorted, watermark, people, text, low quality, cartoon",
        style_keywords=f"{style}, {room_type}, professional, photorealistic",
        lighting_description=f"{light} creating a welcoming atmosphere.",
    )


async def _call_openrouter(a1, a2, a3) -> Optional[str]:
    return await or_call(
        role="agent5",
        system=SYSTEM_PROMPT,
        user=_build_prompt(a1, a2, a3),
        temperature=0.4,
        max_tokens=1024,
    )


def _sync_generate(model, prompt: str) -> str:
    """Blocking call — MUST only ever be invoked via asyncio.to_thread()."""
    response = model.generate_content(prompt)
    return response.text.strip()


async def _call_gemini(a1, a2, a3) -> Optional[str]:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL.strip(),
        generation_config=genai.types.GenerationConfig(temperature=0.4, top_p=0.95),
    )
    prompt = _build_prompt(a1, a2, a3)
    for attempt in range(3):
        try:
            # ⬇️ THE FIX: offload the blocking network call to a thread pool
            return await asyncio.to_thread(_sync_generate, model, prompt)
        except Exception as e:
            if "429" in str(e):
                wait = 20 * (attempt + 1)
                logger.warning(f"[Agent5] Gemini 429 — waiting {wait}s")
                await asyncio.sleep(wait)
            else:
                logger.warning(f"[Agent5] Gemini error: {e}")
                return None
    return None


async def run(
    session_id: str,
    a1: Agent1Output,
    a2: Agent2Output,
    a3: Optional[Agent3Output] = None,
) -> Tuple[Optional[Agent5Output], str]:
    logger.info(f"[Agent5] {session_id} — engineering prompt (has_a3={a3 is not None})")

    # 1. OpenRouter Llama-3.3-70B (best for creative text, free)
    raw = await _call_openrouter(a1, a2, a3)
    result = _parse(raw, session_id) if raw else None
    if result:
        logger.info(f"[Agent5] ✅ OR prompt — {len(result.positive_prompt)} chars")
        return result, ""

    # 2. Gemini fallback
    logger.info("[Agent5] OR failed — trying Gemini")
    await asyncio.sleep(settings.GEMINI_RATE_LIMIT_SLEEP)
    raw = await _call_gemini(a1, a2, a3)
    result = _parse(raw, session_id) if raw else None
    if result:
        logger.info(f"[Agent5] ✅ Gemini prompt — {len(result.positive_prompt)} chars")
        return result, ""

    # 3. Rule-based fallback — always works
    logger.warning("[Agent5] All AI failed — using rule-based prompt")
    result = _fallback_prompt(session_id, a1, a2, a3)
    return result, ""

    