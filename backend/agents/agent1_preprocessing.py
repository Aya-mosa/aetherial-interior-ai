"""
Agent 1: Preprocessing Engine
Primary:  Gemini (with retry on 429)
Fallback: OpenRouter gemma/llama (free tier)
"""
import json
import logging
import asyncio
from typing import Tuple, Optional

import google.generativeai as genai

from core.config import settings
from api.schemas.models import Agent1Output, DesignRequest, RoomDimensions
from agents._openrouter import call as or_call

logger = logging.getLogger(__name__)


def _get_model():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL.strip(),
        generation_config=genai.types.GenerationConfig(
            temperature=settings.GEMINI_TEMPERATURE, top_p=0.95,
        ),
    )


def _build_prompt(request: DesignRequest) -> str:
    return f"""You are a preprocessing agent for an interior design AI.
Given: room_type={request.room_type}, style={request.style}, furniture={[f.value for f in request.furniture]}

Extract any IMPLICIT design constraints or notes that would help a rendering AI.
Return ONLY a short JSON object with one key: "additional_notes" (string, max 100 chars).
No markdown, no preamble.
Example: {{"additional_notes": "Japandi style requires low-profile furniture and natural materials"}}"""


async def _call_gemini(request: DesignRequest) -> Optional[str]:
    """Try Gemini with up to 2 retries on 429."""
    model = _get_model()
    prompt = _build_prompt(request)
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err:
                wait = 15 * (attempt + 1)
                logger.warning(f"[Agent1] Gemini 429 — waiting {wait}s (attempt {attempt+1})")
                await asyncio.sleep(wait)
            else:
                logger.warning(f"[Agent1] Gemini error: {e}")
                return None
    return None


async def _call_openrouter(request: DesignRequest) -> Optional[str]:
    """Fallback: OpenRouter free models."""
    prompt = _build_prompt(request)
    return await or_call(
        role="agent1",
        system="You are a concise interior design preprocessing AI. Always respond with valid JSON only.",
        user=prompt,
        temperature=0.1,
        max_tokens=200,
    )


def _parse_notes(raw: Optional[str]) -> str:
    if not raw:
        return ""
    try:
        start = raw.find("{"); end = raw.rfind("}")
        if start != -1 and end != -1:
            data = json.loads(raw[start:end + 1])
            return data.get("additional_notes", "")
    except Exception:
        pass
    return ""


async def run(session_id: str, request: DesignRequest) -> Tuple[Optional[Agent1Output], str]:
    logger.info(f"[Agent1] Session {session_id} — starting preprocessing")

    # Try Gemini first, then OpenRouter
    raw = await _call_gemini(request)
    if not raw:
        logger.info("[Agent1] Gemini failed — using OpenRouter fallback")
        raw = await _call_openrouter(request)

    notes = _parse_notes(raw)

    # Agent 1 never fails — notes are optional
    output = Agent1Output(
        session_id=session_id,
        room_type=request.room_type.value,
        style_preference=request.style.value,
        dimensions=RoomDimensions(
            width_cm=request.dimensions.width_cm,
            length_cm=request.dimensions.length_cm,
        ),
        selected_furniture=[f.value for f in request.furniture],
        color_palette=request.color_palette.value,
        avoid_elements=["people", "text", "watermarks"],
        ai_mode=request.ai_mode,
        additional_notes=notes,
    )
    logger.info(f"[Agent1] Session {session_id} — complete")
    return output, ""
