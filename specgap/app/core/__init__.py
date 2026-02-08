"""
SpecGap Core Module
"""

from .config import settings, model_text, model_vision, round_models, create_model_for_round, get_settings
from .database import init_db, get_db, get_db_session, AuditRepository, CommentRepository
from .logging import setup_logging, get_logger
from .exceptions import (
    SpecGapError,
    FileProcessingError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    OCRError,
    AIError,
    AIRateLimitError,
    AIModelError,
    AIResponseParseError,
    AIContextTooLongError,
    AuditError,
    AuditNotFoundError,
    CouncilError,
    DatabaseError,
    ValidationError,
)

__all__ = [
    # Config
    "settings",
    "model_text",
    "model_vision",
    "round_models",
    "create_model_for_round",
    "get_settings",

    # Database
    "init_db",
    "get_db",
    "get_db_session",
    "AuditRepository",
    "CommentRepository",

    # Logging
    "setup_logging",
    "get_logger",

    # Exceptions
    "SpecGapError",
    "FileProcessingError",
    "UnsupportedFileTypeError",
    "FileTooLargeError",
    "OCRError",
    "AIError",
    "AIRateLimitError",
    "AIModelError",
    "AIResponseParseError",
    "AIContextTooLongError",
    "AuditError",
    "AuditNotFoundError",
    "CouncilError",
    "DatabaseError",
    "ValidationError",
]

