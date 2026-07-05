"""
Shared OpenRouter helper v2 — updated model list July 2026.
Removed all 404 models. Only verified-working models kept.
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)
OR_URL = "https://openrouter.ai/api/v1/chat/completions"


def _key() -> str:
    try:
        from core.config import settings
        return (settings.OPENROUTER_API_KEY or "").strip()
    except Exception:
        import os
        return os.getenv("OPENROUTER_API_KEY", "").strip()


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://aetherial.app",
        "X-Title": "Aetherial Interior AI",
    }


# ── Verified working models (July 2026) ───────────────────────────────────────
# Strategy: 1 free model first, then paid (cheap) fallbacks
MODELS = {
    "agent1": [
        "meta-llama/llama-3.3-70b-instruct:free",   # free, fast
        "meta-llama/llama-3.1-8b-instruct",          # paid fallback ~$0.0001
        "microsoft/phi-3-mini-128k-instruct:free",   # free fallback
    ],
    "agent2": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1",                      # paid, best for JSON/reasoning
        "meta-llama/llama-3.1-8b-instruct",
    ],
    "agent5": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct",         # paid version
        "meta-llama/llama-3.1-8b-instruct",
    ],
}

# Vision models for agent3
VISION_MODELS = [
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "meta-llama/llama-3.2-11b-vision-instruct",      # paid fallback
    "google/gemini-2.0-flash-001",                   # paid, good vision
]

# Image generation models for agent6 (correct OR model IDs)
IMAGE_MODELS = [
    ("google/gemini-2.5-flash-image",            ["image", "text"]),
    ("google/gemini-3.1-flash-image-preview",    ["image", "text"]),
]


async def call(
    role: str,
    system: str,
    user: str,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> Optional[str]:
    key = _key()
    if not key:
        logger.warning("[OR] OPENROUTER_API_KEY not set")
        return None

    models  = MODELS.get(role, MODELS["agent5"])
    headers = _headers()

    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            try:
                logger.info(f"[OR] {role} → {model}")
                resp = await client.post(OR_URL, headers=headers, json=payload)

                if resp.status_code == 429:
                    logger.warning(f"[OR] Rate limit on {model}")
                    continue
                if resp.status_code == 404:
                    logger.warning(f"[OR] 404 on {model} — removing from list")
                    continue
                if resp.status_code in (401, 402, 403):
                    logger.warning(f"[OR] Auth/billing {resp.status_code} on {model}")
                    continue
                if resp.status_code != 200:
                    logger.warning(f"[OR] HTTP {resp.status_code} on {model}: {resp.text[:100]}")
                    continue

                text = (resp.json()
                            .get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                            .strip())
                if text:
                    logger.info(f"[OR] ✅ {role} via {model}")
                    return text

            except httpx.TimeoutException:
                logger.warning(f"[OR] Timeout on {model}")
            except Exception as e:
                logger.error(f"[OR] Error on {model}: {e}")

    logger.error(f"[OR] All models failed for role={role}")
    return None


async def call_vision(b64: str, mime: str, prompt: str) -> Optional[str]:
    key = _key()
    if not key:
        return None

    headers = _headers()
    payload_base = {
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
        "temperature": 0.1,
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in VISION_MODELS:
            try:
                logger.info(f"[OR-vision] → {model}")
                resp = await client.post(OR_URL, headers=headers,
                                         json={**payload_base, "model": model})
                if resp.status_code == 200:
                    text = (resp.json().get("choices", [{}])[0]
                                       .get("message", {})
                                       .get("content", "").strip())
                    if text:
                        logger.info(f"[OR-vision] ✅ via {model}")
                        return text
                else:
                    logger.warning(f"[OR-vision] {model} → HTTP {resp.status_code}")
            except Exception as e:
                logger.warning(f"[OR-vision] {model} error: {e}")
    return None


