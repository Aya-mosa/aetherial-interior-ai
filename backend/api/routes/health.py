from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "hf_configured": bool(settings.HF_SPACE_URL),
    }
