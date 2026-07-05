"""
Core configuration — reads from .env file
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY:      str = ""
    HUGGINGFACE_API_KEY: str = ""
    OPENROUTER_API_KEY:  str = ""

    # App
    APP_ENV:    str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Directories
    PIPELINE_DATA_DIR: str = "pipeline_data"
    UPLOADS_DIR:       str = "pipeline_data/uploads"
    OUTPUTS_DIR:       str = "pipeline_data/outputs"

    # Gemini
    GEMINI_MODEL:            str   = "gemini-2.0-flash"
    GEMINI_TEMPERATURE:      float = 0.1
    GEMINI_RATE_LIMIT_SLEEP: float = 3.0

    # HuggingFace / Rendering
    HF_SPACE_URL:       str   = ""
    RENDER_MAX_RETRIES: int   = 5
    RENDER_RETRY_DELAY: float = 5.0

    # Queue / Cache
    REDIS_URL:             str = "redis://localhost:6379/0"
    TASK_TIMEOUT_SECONDS:  int = 300
    CACHE_TTL:             int = 3600

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
