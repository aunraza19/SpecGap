"""
Custom Exceptions for SpecGap
Provides structured error handling across the application.
"""

from typing import Optional


class SpecGapError(Exception):
    """Base exception for all SpecGap errors"""

    def __init__(
        self,
        message: str,
        error_code: str = "SPECGAP_ERROR",
        details: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "status": "error",
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# ===== File Processing Errors =====

class FileProcessingError(SpecGapError):
    """Error during file parsing or extraction"""

    def __init__(self, message: str, filename: str = None, details: str = None):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details=details
        )
        self.filename = filename


class UnsupportedFileTypeError(FileProcessingError):
    """File type not supported"""

    def __init__(self, filename: str, supported_types: list = None):
        supported = supported_types or ["pdf", "docx", "txt", "md"]
        super().__init__(
            message=f"Unsupported file type: {filename}",
            filename=filename,
            details=f"Supported types: {', '.join(supported)}"
        )
        self.error_code = "UNSUPPORTED_FILE_TYPE"


class FileTooLargeError(FileProcessingError):
    """File exceeds size limit"""

    def __init__(self, filename: str, size_mb: float, max_mb: int):
        super().__init__(
            message=f"File too large: {filename}",
            filename=filename,
            details=f"Size: {size_mb:.1f}MB, Max: {max_mb}MB"
        )
        self.error_code = "FILE_TOO_LARGE"


class OCRError(FileProcessingError):
    """OCR processing failed"""

    def __init__(self, filename: str, details: str = None):
        super().__init__(
            message=f"OCR failed for scanned document: {filename}",
            filename=filename,
            details=details or "Install pytesseract and pdf2image for OCR support"
        )
        self.error_code = "OCR_ERROR"


# ===== AI/Model Errors =====

class AIError(SpecGapError):
    """Base class for AI-related errors"""
    pass


class AIRateLimitError(AIError):
    """Rate limit exceeded for AI API"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="AI rate limit exceeded",
            error_code="AI_RATE_LIMIT",
            details=f"Please retry after {retry_after} seconds"
        )
        self.retry_after = retry_after


class AIModelError(AIError):
    """AI model returned an error"""

    def __init__(self, model: str, details: str = None):
        super().__init__(
            message=f"AI model error: {model}",
            error_code="AI_MODEL_ERROR",
            details=details
        )
        self.model = model


class AIResponseParseError(AIError):
    """Failed to parse AI response"""

    def __init__(self, agent: str = None, raw_response: str = None):
        super().__init__(
            message="Failed to parse AI response as JSON",
            error_code="AI_PARSE_ERROR",
            details=f"Agent: {agent}" if agent else None
        )
        self.agent = agent
        self.raw_response = raw_response[:500] if raw_response else None


class AIContextTooLongError(AIError):
    """Input context exceeds model limits"""

    def __init__(self, current_chars: int, max_chars: int):
        super().__init__(
            message="Document context too long for AI model",
            error_code="CONTEXT_TOO_LONG",
            details=f"Current: {current_chars:,} chars, Max: {max_chars:,} chars"
        )


# ===== Audit Errors =====

class AuditError(SpecGapError):
    """Base class for audit-related errors"""
    pass


class AuditNotFoundError(AuditError):
    """Audit record not found"""

    def __init__(self, audit_id: str):
        super().__init__(
            message=f"Audit not found: {audit_id}",
            error_code="AUDIT_NOT_FOUND",
            details=None
        )
        self.audit_id = audit_id


class CouncilError(AuditError):
    """Council workflow failed"""

    def __init__(self, round_num: int = None, agent: str = None, details: str = None):
        msg = "Council failed to reach verdict"
        if round_num:
            msg += f" (Round {round_num})"
        if agent:
            msg += f" - Agent: {agent}"

        super().__init__(
            message=msg,
            error_code="COUNCIL_ERROR",
            details=details
        )
        self.round_num = round_num
        self.agent = agent


# ===== Database Errors =====

class DatabaseError(SpecGapError):
    """Database operation failed"""

    def __init__(self, operation: str, details: str = None):
        super().__init__(
            message=f"Database error during: {operation}",
            error_code="DATABASE_ERROR",
            details=details
        )


# ===== Validation Errors =====

class ValidationError(SpecGapError):
    """Input validation failed"""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error: {message}",
            error_code="VALIDATION_ERROR",
            details=f"Field: {field}"
        )
        self.field = field

