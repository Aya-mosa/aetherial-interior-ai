"""AI Interior Architect — FastAPI Backend (v2)"""

import asyncio, os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import design, health, canvas, history   # ← history added
from core.config import settings
from core.logging import setup_logging
from services.session_manager import periodic_cleanup_task

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.PIPELINE_DATA_DIR, exist_ok=True)
    os.makedirs(settings.UPLOADS_DIR,       exist_ok=True)
    os.makedirs(settings.OUTPUTS_DIR,       exist_ok=True)
    cleanup_task = asyncio.create_task(
        periodic_cleanup_task(interval_seconds=600, max_age_seconds=3600)
    )
    yield
    cleanup_task.cancel()


app = FastAPI(
    title="AI Interior Architect API",
    description="Multi-agent AI platform for interior design generation",
    version="2.0.0",
    lifespan=lifespan,
)

_allowed_origins = list(settings.ALLOWED_ORIGINS)
if settings.FRONTEND_URL:
    _allowed_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(settings.OUTPUTS_DIR):
    app.mount("/outputs", StaticFiles(directory=settings.OUTPUTS_DIR), name="outputs")

app.include_router(health.router,   prefix="/api",          tags=["health"])
app.include_router(design.router,   prefix="/api/design",   tags=["design"])
app.include_router(canvas.router,   prefix="/api/canvas",   tags=["canvas"])
app.include_router(history.router,  prefix="/api/history",  tags=["history"])  # ← NEW