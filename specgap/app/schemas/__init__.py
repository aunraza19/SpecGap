"""
SpecGap Schemas Package
"""

from .responses import (
    # Enums
    SeverityLevel,
    AuditType,
    FavorDirection,
    CardType,

    # Common
    HealthResponse,
    ErrorResponse,

    # Tech Engine
    TechGap,
    TechAnalysisResult,

    # Biz Engine
    RedlineSuggestion,
    TrapClause,
    LegalAnalysisResult,

    # Council
    Flashcard,
    AgentFlashcards,
    CouncilVerdict,
    CouncilSessionResponse,

    # Cross-Check
    JiraTicket,
    Contradiction,
    CrossCheckResult,

    # Endpoints
    DeepAnalysisResponse,
    PatchPackRequest,
    PatchPackFiles,
    PatchPackResponse,
    FullSpectrumResponse,

    # Audit History
    AuditSummary,
    AuditListResponse,
    AuditStatistics,

    # Document
    DocumentClassification,
    FileMetadata,
)

__all__ = [
    "SeverityLevel",
    "AuditType",
    "FavorDirection",
    "CardType",
    "HealthResponse",
    "ErrorResponse",
    "TechGap",
    "TechAnalysisResult",
    "RedlineSuggestion",
    "TrapClause",
    "LegalAnalysisResult",
    "Flashcard",
    "AgentFlashcards",
    "CouncilVerdict",
    "CouncilSessionResponse",
    "JiraTicket",
    "Contradiction",
    "CrossCheckResult",
    "DeepAnalysisResponse",
    "PatchPackRequest",
    "PatchPackFiles",
    "PatchPackResponse",
    "FullSpectrumResponse",
    "AuditSummary",
    "AuditListResponse",
    "AuditStatistics",
    "DocumentClassification",
    "FileMetadata",
]

