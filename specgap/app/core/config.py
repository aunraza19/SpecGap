"""
Configuration Module for SpecGap
Centralizes all environment variables and settings.
"""

import os
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv
import google.generativeai as genai

# Load env variables
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    Uses class attributes for type hints and defaults.
    """

    # ===== Project Info =====
    PROJECT_NAME: str = "SpecGap AI Audit"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered specification gap and contract risk analyzer"
    API_PREFIX: str = "/api/v1"

    # ===== Environment =====
    ENV: str = os.getenv("ENV", "development")  # development, staging, production
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # ===== AI Configuration =====
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_TEXT: str = os.getenv("GEMINI_MODEL_TEXT", "gemini-2.0-flash")
    GEMINI_MODEL_VISION: str = os.getenv("GEMINI_MODEL_VISION", "gemini-2.0-flash")

    # ===== Rate Limiting =====
    AI_RATE_LIMIT_REQUESTS: int = int(os.getenv("AI_RATE_LIMIT_REQUESTS", "30"))
    AI_RATE_LIMIT_WINDOW: int = int(os.getenv("AI_RATE_LIMIT_WINDOW", "60"))  # seconds
    AI_REQUEST_DELAY: float = float(os.getenv("AI_REQUEST_DELAY", "2.0"))  # delay between AI calls

    # ===== Database =====
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./specgap_audits.db")

    # ===== Logging =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT_JSON: bool = os.getenv("LOG_FORMAT_JSON", "false").lower() == "true"
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

    # ===== CORS (for frontend) =====
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

    # ===== File Processing =====
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    MAX_CONTEXT_CHARS: int = int(os.getenv("MAX_CONTEXT_CHARS", "100000"))
    CHUNK_SIZE_TOKENS: int = int(os.getenv("CHUNK_SIZE_TOKENS", "8000"))

    # ===== Retry Configuration =====
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "5.0"))

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Use this instead of creating new Settings() objects.
    """
    return Settings()


# Global settings instance
settings = get_settings()


# ===== Gemini Configuration =====

def configure_gemini() -> tuple:
    """
    Configure and return Gemini models.
    Raises ValueError if API key is missing.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "❌ GEMINI_API_KEY missing! "
            "Create a .env file with: GEMINI_API_KEY=your_key_here"
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Model configuration for better responses
    generation_config = {
        "temperature": 0.3,  # Lower for more consistent analysis
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    model_text = genai.GenerativeModel(
        settings.GEMINI_MODEL_TEXT,
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    model_vision = genai.GenerativeModel(
        settings.GEMINI_MODEL_VISION,
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    return model_text, model_vision


# Initialize models
try:
    model_text, model_vision = configure_gemini()
except ValueError as e:
    # Allow import without API key for testing
    import warnings
    warnings.warn(str(e))
    model_text = None
    model_vision = None
