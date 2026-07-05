"""
Design router v4 — fixes:
  1. /rerender: deserialize agent outputs from dict → Pydantic
  2. /chat: bilingual (AR/EN) + site context + OR fallback
  3. Canvas 422: handled in canvas.py
"""

import json, logging, os
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from PIL import Image
import io

from api.schemas.models import (
    AIMode, ChatCommandRequest, ChatResponse, ColorPalette, DesignRequest,
    DesignStyle, FurnitureItem, PipelineStatusResponse, RegenerateAreaRequest,
    RoomDimensions, RoomType, SessionResponse, TaskStatus,
    Agent1Output, Agent2Output, Agent3Output, Agent4Output,
)
from core.config import settings
from services.pipeline import run_pipeline, _resolve_canvas_path
from services.session_manager import session_manager
from services.history_manager import history_manager
from agents import agent5_prompt, agent6_renderer

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES   = 10 * 1024 * 1024
MIN_DIMENSION_PX      = 512

# ── Site context for the chat AI ──────────────────────────────────────────────
SITE_CONTEXT = """
You are the AI Interior Architect of "Aetherial Interior AI" — an intelligent interior design platform built for DEPI (Digital Egypt Pioneers Initiative).

You are BILINGUAL: always respond in the SAME LANGUAGE as the user.
- If user writes in Arabic → respond fully in Arabic
- If user writes in English → respond in English

ABOUT THE PLATFORM:
- AI-powered interior design tool that transforms room photos into redesigned renders
- Uses a 6-agent pipeline: preprocessing → spatial planning → vision analysis → validation → prompt engineering → image generation
- Supported styles: Modern, Minimalist, Bohemian, Industrial, Scandinavian, Japandi, Classic, Farmhouse
- Supported rooms: Bedroom, Living Room, Kitchen, Bathroom, Office, Dining Room
- Features: Before/After comparison, interactive floor plan, drag & drop furniture, AI chat, re-rendering, image download
- Free to use platform

YOUR ROLE:
1. Answer questions about the platform and how it works (in Arabic or English)
2. Provide interior design advice
3. Process furniture movement requests → return layout_changes
4. Be professional, friendly, and helpful

ALWAYS reply ONLY in valid JSON (no markdown):
{"reply":"your response here","action_taken":null,"layout_changes":[]}
"""


async def _validate_image(file: UploadFile) -> bytes:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Unsupported image type '{file.content_type}'.")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail=f"Image too large ({len(content)/1024/1024:.1f} MB). Max 10 MB.")
    if len(content) < 1024:
        raise HTTPException(status_code=422, detail="File too small to be a valid image.")
    try:
        img = Image.open(io.BytesIO(content)); img.verify()
        img = Image.open(io.BytesIO(content)); w, h = img.size
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Cannot read image: {e}")
    if w < MIN_DIMENSION_PX or h < MIN_DIMENSION_PX:
        raise HTTPException(status_code=422, detail=f"Image too small ({w}×{h}px). Min {MIN_DIMENSION_PX}px.")
    return content


def _deserialize(model_class, data):
    if data is None:
        return None
    if isinstance(data, model_class):
        return data
    if isinstance(data, dict):
        try:
            return model_class(**data)
        except Exception as e:
            logger.warning(f"[deserialize] {model_class.__name__} failed: {e}")
            return None
    return None


# ── /start ────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=SessionResponse)
async def start_design(
    background_tasks: BackgroundTasks,
    room_image:     UploadFile = File(...),
    room_type:      str        = Form(...),
    style:          str        = Form(...),
    furniture:      str        = Form(...),
    width_cm:       int        = Form(400),
    length_cm:      int        = Form(500),
    color_palette:  str        = Form("Warm Woods & Neutrals"),
    ai_mode:        str        = Form("strict"),
    num_variations: int        = Form(3),
    user_id:        str        = Form("anonymous"),
):
    try:
        furniture_list = json.loads(furniture)
        if not isinstance(furniture_list, list):
            raise ValueError
    except Exception:
        furniture_list = [furniture]

    try:
        request = DesignRequest(
            room_type=RoomType(room_type),
            style=DesignStyle(style),
            furniture=[FurnitureItem(f) for f in furniture_list],
            dimensions=RoomDimensions(width_cm=width_cm, length_cm=length_cm),
            color_palette=ColorPalette(color_palette),
            ai_mode=AIMode(ai_mode),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid parameters: {e}")

    image_content = await _validate_image(room_image)
    session_id    = session_manager.new_session()

    upload_dir = session_manager.get_upload_path(session_id)
    image_path = os.path.join(upload_dir, "room.jpg")
    with open(image_path, "wb") as f:
        f.write(image_content)

    session_manager.get(session_id)["user_id"]    = user_id
    session_manager.get(session_id)["image_path"] = image_path

    history_manager.create(session_id=session_id, user_id=user_id, style=style, room_type=room_type)
    background_tasks.add_task(run_pipeline, session_id, request, image_path, num_variations)
    logger.info(f"[/design/start] {session_id} user={user_id}")

    return SessionResponse(session_id=session_id, status=TaskStatus.PENDING, message="Pipeline started.")


# ── /status ───────────────────────────────────────────────────────────────────

@router.get("/status/{session_id}", response_model=PipelineStatusResponse)
async def get_status(session_id: str):
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return PipelineStatusResponse(
        session_id=session_id,
        status=session["status"],
        current_step=session.get("current_step"),
        progress_percent=session.get("progress_percent", 0),
        agent1=session.get("agent1"), agent2=session.get("agent2"),
        agent3=session.get("agent3"), agent4=session.get("agent4"),
        agent5=session.get("agent5"), agent6=session.get("agent6"),
        error=session.get("error"),
    )


# ── /rerender ─────────────────────────────────────────────────────────────────

@router.post("/rerender", response_model=SessionResponse)
async def rerender_design(body: dict, background_tasks: BackgroundTasks):
    session_id = body.get("session_id")
    session    = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    a1_out = _deserialize(Agent1Output, session.get("agent1"))
    a2_out = _deserialize(Agent2Output, session.get("agent2"))
    a3_out = _deserialize(Agent3Output, session.get("agent3"))
    a4_out = _deserialize(Agent4Output, session.get("agent4"))
    image_path = session.get("image_path", "")

    if not a1_out or not a2_out:
        raise HTTPException(status_code=400, detail="Pipeline data incomplete — run full design first")

    async def _partial():
        try:
            session_manager.set_status(session_id, TaskStatus.PROCESSING, "Re-engineering prompts…", 70)
            a5_out, err = await agent5_prompt.run(session_id, a1_out, a2_out, a3_out)
            if not a5_out:
                session_manager.set_error(session_id, f"Rerender A5 failed: {err}")
                return
            session_manager.set_agent_output(session_id, 5, a5_out)

            session_manager.set_status(session_id, TaskStatus.PROCESSING, "Re-rendering design…", 85)
            canvas_path = _resolve_canvas_path(a4_out.canvas_image_path if a4_out else None)
            a6_out, err = await agent6_renderer.run(
                session_id=session_id, a5=a5_out,
                original_image_path=image_path,
                canvas_path=canvas_path, num_variations=3,
            )
            if not a6_out:
                session_manager.set_error(session_id, f"Rerender A6 failed: {err}")
                return
            session_manager.set_agent_output(session_id, 6, a6_out)
            session_manager.set_status(session_id, TaskStatus.DONE, "Re-render complete!", 100)

            if a6_out.variations:
                first = a6_out.variations[0]
                history_manager.complete(session_id, first.thumbnail_url or first.image_url, first.image_url)

        except Exception as e:
            logger.exception("[/rerender] error")
            session_manager.set_error(session_id, f"Rerender error: {e}")

    background_tasks.add_task(_partial)
    return SessionResponse(session_id=session_id, status=TaskStatus.PROCESSING, message="Re-rendering…")


# ── /chat ─────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def ai_chat_command(body: ChatCommandRequest):
    session = session_manager.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_layout = session.get("agent2")

    # Extract actual user message (frontend may inject [CONTEXT:...] prefix)
    raw_message = body.message
    if "[CONTEXT:" in raw_message and "User message:" in raw_message:
        actual_msg = raw_message.split("User message:")[-1].strip()
    else:
        actual_msg = raw_message

    user_prompt = f"""Current room layout (JSON): {json.dumps(current_layout)}

User message: "{actual_msg}"

Reply ONLY in valid JSON (no markdown). Match the language of the user message.
If user asks about the platform/website, answer using your knowledge about Aetherial.
If user requests furniture movement, include layout_changes.

Format:
{{"reply":"your response","action_taken":null,"layout_changes":[]}}"""

    raw = None

    # 1. Try Gemini first
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model    = genai.GenerativeModel(settings.GEMINI_MODEL.strip())
        response = model.generate_content(
            f"System: {SITE_CONTEXT}\n\n{user_prompt}"
        )
        raw = response.text.strip()
        logger.info("[/chat] Gemini ✅")
    except Exception as e:
        if "429" in str(e):
            logger.warning("[/chat] Gemini 429 — falling back to OpenRouter")
        else:
            logger.warning(f"[/chat] Gemini error: {e}")
        raw = None

    # 2. OpenRouter fallback
    if not raw:
        try:
            from agents._openrouter import call as or_call
            raw = await or_call(
                role="agent5",
                system=SITE_CONTEXT,
                user=user_prompt,
                temperature=0.3,
                max_tokens=600,
            )
            if raw:
                logger.info("[/chat] OR ✅")
        except Exception as e:
            logger.error(f"[/chat] OR error: {e}")
            raw = None

    if not raw:
        # Detect Arabic in original message
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in actual_msg)
        return ChatResponse(
            session_id=body.session_id,
            reply="عذراً، حدث خطأ. يرجى المحاولة مجدداً." if is_arabic
                  else "I'm having trouble right now — please try again in a moment."
        )

    try:
        clean = raw.strip().replace("```json", "").replace("```", "")
        if "<think>" in clean:
            end = clean.find("</think>")
            if end != -1:
                clean = clean[end + 8:]
        data    = json.loads(clean[clean.find("{"):clean.rfind("}")+1])
        reply   = data.get("reply", "Understood.")
        action  = data.get("action_taken")
        changes = data.get("layout_changes", [])

        if changes and current_layout:
            furniture = current_layout.get("furniture", [])
            for change in changes:
                for item in furniture:
                    if item.get("id") == change.get("id"):
                        if "position" in change: item["position"] = change["position"]
                        if "size"     in change: item["size"]     = change["size"]
            if isinstance(session.get("agent2"), dict):
                session["agent2"]["furniture"] = furniture

        return ChatResponse(session_id=body.session_id, reply=reply, action_taken=action)

    except Exception as e:
        logger.error(f"[/chat] parse error: {e}")
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in actual_msg)
        return ChatResponse(
            session_id=body.session_id,
            reply="مفهوم! هل تريد إجراء أي تغييرات أخرى؟" if is_arabic
                  else "Understood! Let me know if you'd like any other changes."
        )


# ── /regenerate-area ──────────────────────────────────────────────────────────

@router.post("/regenerate-area", response_model=SessionResponse)
async def regenerate_area(body: RegenerateAreaRequest, background_tasks: BackgroundTasks):
    import base64
    session = session_manager.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    output_dir = session_manager.get_output_path(body.session_id)
    mask_path  = os.path.join(output_dir, "inpaint_mask.png")
    try:
        with open(mask_path, "wb") as f:
            f.write(base64.b64decode(body.mask_base64))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid mask: {e}")
    return SessionResponse(session_id=body.session_id, status=TaskStatus.PENDING,
                           message="Area regeneration queued.")
