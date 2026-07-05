"""
Agent 6 — Image Renderer v11
Clean model list — only verified working models (July 2026).
Removed: flux-1-schnell-free (invalid ID), flux-1.1-pro (invalid ID)
Working: gemini-2.5-flash-image, gemini-3.1-flash-image-preview via OR
"""

import asyncio, base64, io, logging, os, time, re
from pathlib import Path
from typing import Optional, Tuple

import httpx
from PIL import Image

from api.schemas.models import Agent5Output, Agent6Output, RenderVariation
from core.config import settings

logger = logging.getLogger(__name__)


def _or_key()  -> str: return (settings.OPENROUTER_API_KEY  or "").strip()
def _hf_key()  -> str: return (settings.HUGGINGFACE_API_KEY or "").strip()
def _gem_key() -> str: return (settings.GEMINI_API_KEY       or "").strip()

OR_BASE = "https://openrouter.ai/api/v1/chat/completions"

def _or_headers() -> dict:
    return {
        "Authorization": f"Bearer {_or_key()}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://aetherial.app",
        "X-Title":       "Aetherial Interior AI",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _path_to_url(file_path: str, session_id: str) -> str:
    try:
        parts = Path(file_path).parts
        idx   = next((i for i, p in enumerate(parts) if p == "outputs"), None)
        if idx is not None:
            return "/" + "/".join(parts[idx:])
    except Exception:
        pass
    return f"/outputs/{session_id}/{Path(file_path).name}"


def _save_image(image_bytes: bytes, session_id: str, variation: int) -> Optional[str]:
    try:
        out = Path(f"pipeline_data/outputs/{session_id}")
        out.mkdir(parents=True, exist_ok=True)
        img_path   = out / f"variation_{variation}.jpg"
        thumb_path = out / f"variation_{variation}_thumb.jpg"
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.save(img_path, "JPEG", quality=92)
        thumb = img.copy()
        thumb.thumbnail((400, 300), Image.LANCZOS)
        thumb.save(thumb_path, "JPEG", quality=80)
        return str(img_path)
    except Exception as e:
        logger.error(f"[Agent6] Save error var {variation}: {e}")
        return None


def _detect_mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")


def _extract_image_bytes(data: dict) -> Optional[bytes]:
    try:
        msg = data.get("choices", [{}])[0].get("message", {})

        # Primary: OR images array
        images = msg.get("images") or []
        for img_obj in images:
            if isinstance(img_obj, dict):
                image_url_obj = img_obj.get("imageUrl") or img_obj.get("image_url") or {}
                url = ""
                if isinstance(image_url_obj, dict):
                    url = image_url_obj.get("url", "")
                elif isinstance(image_url_obj, str):
                    url = image_url_obj
                if not url:
                    url = img_obj.get("url", "")
                if url.startswith("data:image"):
                    return base64.b64decode(url.split(",", 1)[1].replace("\n", ""))
                elif url.startswith("http"):
                    return url  # caller downloads

        # Fallback: content list blocks
        content = msg.get("content", "")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "image_url":
                    url = (block.get("image_url") or {}).get("url", "")
                    if url.startswith("data:image"):
                        return base64.b64decode(url.split(",", 1)[1].replace("\n", ""))
                    elif url.startswith("http"):
                        return url
                if block.get("type") == "image":
                    src = block.get("source") or {}
                    if src.get("type") == "base64":
                        return base64.b64decode(src["data"])

        # Fallback: base64 in string
        if isinstance(content, str):
            m = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=\n]+)', content)
            if m:
                return base64.b64decode(m.group(1).replace("\n", ""))

    except Exception as e:
        logger.debug(f"[Agent6] extract error: {e}")
    return None


# ── Verified OR image models (July 2026) ──────────────────────────────────────
OR_IMG_MODELS = [
    ("google/gemini-2.5-flash-image",         ["image", "text"]),
    ("google/gemini-3.1-flash-image-preview", ["image", "text"]),
]


async def _generate_or_image(
    prompt: str, image_path: str, session_id: str, variation: int
) -> Optional[str]:
    key = _or_key()
    if not key:
        return None

    headers = _or_headers()

    # Build reference image part if available
    has_ref = bool(image_path and os.path.exists(image_path))
    ref_b64, ref_mime = None, None
    if has_ref:
        try:
            with open(image_path, "rb") as f:
                ref_b64 = base64.b64encode(f.read()).decode()
            ref_mime = _detect_mime(image_path)
        except Exception:
            has_ref = False

    async with httpx.AsyncClient(timeout=120.0) as client:
        for model_id, modalities in OR_IMG_MODELS:
            if has_ref and ref_b64:
                msg_content = [
                    {"type": "image_url", "image_url": {"url": f"data:{ref_mime};base64,{ref_b64}"}},
                    {"type": "text", "text": f"Redesign this room with: {prompt[:400]}"},
                ]
            else:
                msg_content = prompt[:500]

            payload = {
                "model":      model_id,
                "modalities": modalities,
                "messages":   [{"role": "user", "content": msg_content}],
                "image_config": {"aspect_ratio": "4:3"},
            }

            logger.info(f"[Agent6] OR img var {variation} → {model_id.split('/')[-1]}")
            try:
                resp = await client.post(OR_BASE, headers=headers, json=payload)

                # If failed with image, retry without reference
                if resp.status_code in (400, 422) and has_ref:
                    payload["messages"][0]["content"] = prompt[:500]
                    resp = await client.post(OR_BASE, headers=headers, json=payload)

                if resp.status_code == 404:
                    logger.warning(f"[Agent6] {model_id} → 404")
                    continue
                if resp.status_code == 402:
                    logger.warning(f"[Agent6] {model_id} → 402 insufficient credits")
                    continue
                if resp.status_code not in (200, 201):
                    logger.warning(f"[Agent6] {model_id} → HTTP {resp.status_code}: {resp.text[:120]}")
                    continue

                result = _extract_image_bytes(resp.json())
                if result is None:
                    msg = resp.json().get("choices", [{}])[0].get("message", {})
                    logger.warning(f"[Agent6] {model_id} → no image. Keys: {list(msg.keys())}")
                    continue

                # Download if URL
                if isinstance(result, str) and result.startswith("http"):
                    try:
                        dl = await client.get(result, timeout=60.0, follow_redirects=True)
                        if dl.status_code == 200 and len(dl.content) > 2000:
                            result = dl.content
                        else:
                            continue
                    except Exception as e:
                        logger.warning(f"[Agent6] download failed: {e}")
                        continue

                if isinstance(result, bytes) and len(result) > 2000:
                    path = _save_image(result, session_id, variation)
                    if path:
                        logger.info(f"[Agent6] ✅ OR {model_id.split('/')[-1]} var {variation}")
                        return path

            except httpx.TimeoutException:
                logger.warning(f"[Agent6] {model_id} timeout")
            except Exception as e:
                logger.error(f"[Agent6] {model_id} error: {e}")

    return None


async def _generate_hf(prompt: str, session_id: str, variation: int) -> Optional[str]:
    key = _hf_key()
    if not key:
        return None
    HF_API = "https://api-inference.huggingface.co/models/{model}"
    models = [
        ("black-forest-labs/FLUX.1-schnell", {"num_inference_steps": 4, "guidance_scale": 0.0}),
        ("stabilityai/stable-diffusion-xl-base-1.0", {"num_inference_steps": 20}),
    ]
    async with httpx.AsyncClient(timeout=180.0) as client:
        for model_id, params in models:
            payload = {"inputs": prompt[:500], "parameters": {**params, "width": 1024, "height": 768}}
            try:
                resp = await client.post(
                    HF_API.format(model=model_id),
                    headers={"Authorization": f"Bearer {key}"},
                    json=payload,
                )
                if resp.status_code == 503:
                    wait = min(float(resp.json().get("estimated_time", 20)), 30)
                    await asyncio.sleep(wait)
                    resp = await client.post(
                        HF_API.format(model=model_id),
                        headers={"Authorization": f"Bearer {key}"},
                        json=payload,
                    )
                if resp.status_code == 200 and len(resp.content) > 2000:
                    path = _save_image(resp.content, session_id, variation)
                    if path:
                        logger.info(f"[Agent6] ✅ HF {model_id.split('/')[-1]} var {variation}")
                        return path
            except Exception as e:
                logger.warning(f"[Agent6] HF {model_id.split('/')[-1]}: {e}")
    return None


async def _generate_gemini(
    prompt: str, image_path: str, session_id: str, variation: int
) -> Optional[str]:
    api_key = _gem_key()
    if not api_key or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()
        mime = _detect_mime(image_path)
    except Exception:
        return None

    payload = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime, "data": image_b64}},
            {"text": f"Redesign this room: {prompt[:300]}. Keep structure, change decor."},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"], "temperature": 1.0},
    }
    url_base = "https://generativelanguage.googleapis.com/v1beta/models"
    models = ["gemini-2.0-flash-exp", "gemini-2.5-flash"]

    async with httpx.AsyncClient(timeout=120.0) as client:
        for model in models:
            try:
                resp = await client.post(
                    f"{url_base}/{model}:generateContent?key={api_key}", json=payload)
                if resp.status_code == 404:
                    continue
                if resp.status_code == 400:
                    if "not available in your country" in resp.text:
                        return None
                    continue
                if resp.status_code == 429:
                    await asyncio.sleep(15)
                    resp = await client.post(
                        f"{url_base}/{model}:generateContent?key={api_key}", json=payload)
                if resp.status_code != 200:
                    continue
                parts = (resp.json().get("candidates", [{}])[0]
                              .get("content", {}).get("parts", []))
                for part in parts:
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline:
                        path = _save_image(
                            base64.b64decode(inline["data"]), session_id, variation)
                        if path:
                            logger.info(f"[Agent6] ✅ Gemini img2img var {variation}")
                            return path
            except Exception as e:
                logger.warning(f"[Agent6] Gemini {model}: {e}")
    return None


# ── Main ───────────────────────────────────────────────────────────────────────

async def run(
    session_id: str,
    a5: Agent5Output,
    original_image_path: str,
    canvas_path: str,
    num_variations: int = 3,
) -> Tuple[Optional[Agent6Output], str]:

    has_or  = bool(_or_key())
    has_hf  = bool(_hf_key())
    has_gem = bool(_gem_key())
    has_img = bool(original_image_path and os.path.exists(original_image_path))

    logger.info(f"[Agent6] {session_id} — {num_variations} variation(s)")
    logger.info(
        f"[Agent6] OR img-gen: {'✅' if has_or else '❌'} | "
        f"HF: {'✅' if has_hf else '❌'} | "
        f"Gemini: {'✅' if has_gem else '❌'}"
    )

    base_prompt = a5.positive_prompt or "photorealistic modern interior design, 8k"
    suffixes = [
        "warm golden hour lighting, cozy atmosphere, 8k photorealistic",
        "natural daylight, wide angle, bright and airy, professional render",
        "dramatic accent lighting, luxury feel, architectural photography",
    ]

    async def _one(i: int) -> Optional[str]:
        suffix = suffixes[(i - 1) % len(suffixes)]
        prompt = f"{base_prompt}, {suffix}"

        if has_or:
            path = await _generate_or_image(prompt, original_image_path or "", session_id, i)
            if path:
                return path
            logger.warning(f"[Agent6] OR failed var {i}")

        if has_hf:
            path = await _generate_hf(prompt, session_id, i)
            if path:
                return path

        if has_gem and has_img:
            path = await _generate_gemini(prompt, original_image_path, session_id, i)
            if path:
                return path

        logger.error(f"[Agent6] All sources failed var {i}")
        return None

    t0      = time.monotonic()
    results = []
    for i in range(1, num_variations + 1):
        result = await _one(i)
        results.append(result)
        if i < num_variations:
            await asyncio.sleep(1)

    variations, n_ok = [], 0
    for i, img_path in enumerate(results, 1):
        if img_path:
            url   = _path_to_url(img_path, session_id)
            thumb = img_path.replace(".jpg", "_thumb.jpg")
            t_url = _path_to_url(thumb, session_id) if Path(thumb).exists() else url
            variations.append(RenderVariation(variation_id=i, image_url=url, thumbnail_url=t_url))
            n_ok += 1

    render_time = round(time.monotonic() - t0, 2)
    logger.info(f"[Agent6] Done — {n_ok}/{num_variations} in {render_time}s")

    if n_ok == 0:
        return None, "All image sources failed"

    return Agent6Output(
        session_id=session_id, variations=variations, render_time_seconds=render_time
    ), ""
