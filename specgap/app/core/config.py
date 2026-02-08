"""
Configuration Module for SpecGap
Centralizes all environment variables and settings.

Multi-API Key Strategy:
- Free tier Gemini has 5 RPM per project
- We need 9 calls (3 agents × 3 rounds)
- Solution: Use 3 different API keys (one per round)
- Each round makes 3 parallel calls, staying under 5 RPM
"""

import os
from typing import Optional, Dict
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
    # Primary API key (fallback if round-specific keys not provided)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Round-specific API keys for parallel execution without rate limits
    GEMINI_API_KEY_ROUND1: str = os.getenv("GEMINI_API_KEY_ROUND1", "")
    GEMINI_API_KEY_ROUND2: str = os.getenv("GEMINI_API_KEY_ROUND2", "")
    GEMINI_API_KEY_ROUND3: str = os.getenv("GEMINI_API_KEY_ROUND3", "")

    GEMINI_MODEL_TEXT: str = os.getenv("GEMINI_MODEL_TEXT", "gemini-3-flash-preview")
    GEMINI_MODEL_VISION: str = os.getenv("GEMINI_MODEL_VISION", "gemini-3-flash-preview")

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

# Model configuration for better responses
GENERATION_CONFIG = {
    "temperature": 0.3,  # Lower for more consistent analysis
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


# Store API keys for each round (to be configured at request time)
def get_round_api_keys() -> Dict[str, str]:
    """
    Get API keys for each round.
    Each round uses a different API key to avoid rate limits.
    """
    primary_key = settings.GEMINI_API_KEY
    return {
        "ROUND_1": settings.GEMINI_API_KEY_ROUND1 or primary_key,
        "ROUND_2": settings.GEMINI_API_KEY_ROUND2 or primary_key,
        "ROUND_3": settings.GEMINI_API_KEY_ROUND3 or primary_key,
        "default": primary_key or settings.GEMINI_API_KEY_ROUND1,
    }


def create_model_for_round(round_type: str) -> genai.GenerativeModel:
    """
    Create a Gemini model configured with the API key for the specified round.
    This must be called immediately before making API calls to ensure
    the correct API key is active (genai.configure is global).

    Args:
        round_type: ROUND_1, ROUND_2, ROUND_3, or default

    Returns:
        Configured GenerativeModel instance
    """
    api_keys = get_round_api_keys()
    api_key = api_keys.get(round_type) or api_keys.get("default")

    if not api_key:
        raise ValueError(
            "❌ No GEMINI API keys found! "
            "Create a .env file with:\n"
            "  GEMINI_API_KEY_ROUND1=your_key_1\n"
            "  GEMINI_API_KEY_ROUND2=your_key_2\n"
            "  GEMINI_API_KEY_ROUND3=your_key_3\n"
            "Or use a single key: GEMINI_API_KEY=your_key"
        )

    # Configure with the round-specific API key
    genai.configure(api_key=api_key)

    return genai.GenerativeModel(
        settings.GEMINI_MODEL_TEXT,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )


# Legacy: Single model instances for backward compatibility
def configure_default_models():
    """Configure default models using primary API key."""
    primary_key = settings.GEMINI_API_KEY or settings.GEMINI_API_KEY_ROUND1

    if not primary_key:
        return None, None

    genai.configure(api_key=primary_key)

    model_text = genai.GenerativeModel(
        settings.GEMINI_MODEL_TEXT,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )

    model_vision = genai.GenerativeModel(
        settings.GEMINI_MODEL_VISION,
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )

    return model_text, model_vision


# For backward compatibility - these use the default/primary key
try:
    model_text, model_vision = configure_default_models()
except Exception as e:
    import warnings
    warnings.warn(str(e))
    model_text = None
    model_vision = None

# Export round_models as empty dict for backward compatibility
# Actual model creation happens at request time via create_model_for_round()
round_models = {}

