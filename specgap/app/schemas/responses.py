"""
Pydantic Schemas for SpecGap API
Provides request/response validation and OpenAPI documentation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


# ============== ENUMS ==============

class SeverityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class AuditType(str, Enum):
    TECH_SPEC = "tech_spec"
    PROPOSAL = "proposal"
    FULL_AUDIT = "full_audit"
    COUNCIL_SESSION = "council_session"
    DEEP_ANALYSIS = "deep_analysis"
    FULL_SPECTRUM = "full_spectrum"


class FavorDirection(str, Enum):
    VENDOR = "Vendor"
    CLIENT = "Client"
    NEUTRAL = "Neutral"


class CardType(str, Enum):
    RISK = "Risk"
    GAP = "Gap"
    OPPORTUNITY = "Opportunity"
    WARNING = "Warning"


# ============== COMMON SCHEMAS ==============

def _utc_now():
    """Get current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="System status")
    system: str = Field(..., description="System name")
    architecture: str = Field(..., description="Architecture description")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(default_factory=_utc_now)


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = Field(default="error")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")
    error_code: Optional[str] = Field(default=None, description="Error code for frontend handling")


# ============== TECH ENGINE SCHEMAS ==============

class TechGap(BaseModel):
    """Single technical gap finding"""
    feature: str = Field(..., description="Feature name with the gap")
    missing_component: str = Field(..., description="What is missing")
    risk_level: SeverityLevel = Field(..., description="Risk severity")
    recommendation: str = Field(..., description="Suggested fix")
    source_reference: str = Field(..., description="Citation from document")


class TechAnalysisResult(BaseModel):
    """Tech engine analysis output"""
    project_name: Optional[str] = Field(default=None)
    critical_gaps: List[TechGap] = Field(default_factory=list)
    ambiguity_score: int = Field(..., ge=0, le=100, description="Document clarity score (0-100)")
    error: Optional[str] = Field(default=None)


# ============== BIZ ENGINE SCHEMAS ==============

class RedlineSuggestion(BaseModel):
    """Suggested contract modification"""
    original_text: str = Field(..., description="Original clause text")
    proposed_text: str = Field(..., description="Suggested replacement")
    negotiation_argument: str = Field(..., description="Argument for the change")


class TrapClause(BaseModel):
    """Detected contract trap"""
    clause_snippet: str = Field(..., description="Quoted text from document")
    risk_explanation: str = Field(..., description="Why this is dangerous")
    severity: SeverityLevel = Field(...)
    redline_suggestion: Optional[RedlineSuggestion] = Field(default=None)


class LegalAnalysisResult(BaseModel):
    """Legal/business engine analysis output"""
    leverage_score: int = Field(..., ge=0, le=100, description="Negotiation leverage (0=client favor, 100=vendor favor)")
    favor_direction: FavorDirection = Field(...)
    trap_clauses: List[TrapClause] = Field(default_factory=list)
    negotiation_tips: List[str] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)


# ============== COUNCIL/FLASHCARD SCHEMAS ==============

class Flashcard(BaseModel):
    """Single actionable flashcard"""
    id: str = Field(..., description="Unique flashcard ID")
    card_type: CardType = Field(...)
    title: str = Field(..., description="Short headline")
    description: str = Field(..., description="2-3 sentence explanation")
    fix_action: str = Field(..., description="Action to take")
    severity: SeverityLevel = Field(...)
    swipe_right_payload: str = Field(..., description="Clause/text to add if accepted")
    source_agent: Optional[str] = Field(default=None, description="Which agent generated this")

    model_config = ConfigDict(extra="allow")


class AgentFlashcards(BaseModel):
    """Flashcards from a single agent"""
    flashcards: List[Flashcard] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)
    raw: Optional[str] = Field(default=None, description="Raw response if parsing failed")


class CouncilVerdict(BaseModel):
    """Final council output"""
    flashcards: List[Flashcard] = Field(default_factory=list)


class CouncilSessionResponse(BaseModel):
    """Response from council session endpoint"""
    status: str = Field(...)
    files_analyzed: List[str] = Field(default_factory=list)
    domain: str = Field(...)
    council_verdict: CouncilVerdict = Field(...)


# ============== CROSS-CHECK SCHEMAS ==============

class JiraTicket(BaseModel):
    """Auto-generated JIRA ticket"""
    title: str = Field(...)
    description: str = Field(...)
    priority: SeverityLevel = Field(...)
    labels: List[str] = Field(default_factory=list)
    acceptance_criteria: Optional[str] = Field(default=None)


class Contradiction(BaseModel):
    """Document contradiction finding"""
    topic: str = Field(..., description="Subject of contradiction")
    document_a_says: str = Field(..., description="What first document states")
    document_b_says: str = Field(..., description="What second document states")
    impact: str = Field(..., description="Business impact")


class CrossCheckResult(BaseModel):
    """Cross-check synthesis output"""
    contradictions: List[Contradiction] = Field(default_factory=list)
    strategic_synthesis: str = Field(..., description="Executive summary")
    reality_diagram_mermaid: Optional[str] = Field(default=None, description="Mermaid.js code")
    patch_pack: Optional[Dict[str, Any]] = Field(default=None)
    jira_tickets: List[JiraTicket] = Field(default_factory=list)
    negotiation_email: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)


# ============== DEEP ANALYSIS SCHEMAS ==============

class DeepAnalysisResponse(BaseModel):
    """Response from deep analysis endpoint"""
    status: str = Field(...)
    mode: str = Field(default="deep_analysis")
    files_analyzed: List[str] = Field(default_factory=list)
    domain: str = Field(...)
    tech_audit: TechAnalysisResult = Field(...)
    legal_audit: LegalAnalysisResult = Field(...)
    executive_synthesis: CrossCheckResult = Field(...)


# ============== PATCH PACK SCHEMAS ==============

class PatchPackRequest(BaseModel):
    """Request for patch pack generation"""
    selected_cards: List[Dict[str, Any]] = Field(..., description="Flashcards user accepted")
    domain: str = Field(default="Software Engineering")


class PatchPackFiles(BaseModel):
    """Generated patch pack files"""
    contract_addendum: str = Field(alias="Contract_Addendum.txt")
    spec_update: str = Field(alias="Spec_Update.md")
    negotiation_email: str = Field(alias="Negotiation_Email.txt")

    model_config = ConfigDict(populate_by_name=True)


class PatchPackResponse(BaseModel):
    """Response from patch pack endpoint"""
    status: str = Field(...)
    files: Dict[str, str] = Field(..., description="Generated file contents")


# ============== FULL SPECTRUM SCHEMAS ==============

class FullSpectrumResponse(BaseModel):
    """Response from full spectrum analysis"""
    status: str = Field(...)
    mode: str = Field(default="full_spectrum")
    files_analyzed: List[str] = Field(default_factory=list)
    domain: str = Field(...)
    council_verdict: CouncilVerdict = Field(...)
    deep_analysis: Dict[str, Any] = Field(...)


# ============== AUDIT HISTORY SCHEMAS ==============

class AuditSummary(BaseModel):
    """Summary of a saved audit"""
    id: str = Field(...)
    created_at: datetime = Field(...)
    audit_type: str = Field(...)
    project_name: Optional[str] = Field(default=None)
    tech_spec_filename: Optional[str] = Field(default=None)
    proposal_filename: Optional[str] = Field(default=None)
    risk_level: Optional[str] = Field(default=None)
    composite_risk_score: Optional[float] = Field(default=None)


class AuditListResponse(BaseModel):
    """Paginated list of audits"""
    audits: List[AuditSummary] = Field(default_factory=list)
    total: int = Field(...)
    limit: int = Field(...)
    offset: int = Field(...)


class AuditStatistics(BaseModel):
    """Dashboard statistics"""
    total_audits: int = Field(...)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_risk_level: Dict[str, int] = Field(default_factory=dict)
    avg_risk_score: Optional[float] = Field(default=None)


# ============== DOCUMENT CLASSIFICATION ==============

class DocumentClassification(BaseModel):
    """Document type classification result"""
    detected_type: str = Field(...)
    confidence: float = Field(..., ge=0, le=1)
    recommended_agents: List[str] = Field(default_factory=list)


class FileMetadata(BaseModel):
    """Uploaded file metadata"""
    filename: str = Field(...)
    size_bytes: int = Field(...)
    content_type: Optional[str] = Field(default=None)
    format: str = Field(...)
    classification: Optional[DocumentClassification] = Field(default=None)


# ============== QUEUE MANAGEMENT SCHEMAS ==============

class QueueStatusEnum(str, Enum):
    """Status of a queue entry"""
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class QueueEntryResponse(BaseModel):
    """Response for a queue entry"""
    id: str = Field(..., description="Unique queue entry ID")
    session_id: str = Field(..., description="User's session ID")
    status: QueueStatusEnum = Field(..., description="Current status")
    position: int = Field(..., description="Position in queue (0 = processing)")
    created_at: datetime = Field(...)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    wait_time: Optional[dict] = Field(default=None, description="Estimated wait time")


class QueueInfoResponse(BaseModel):
    """Current queue status information"""
    queue_length: int = Field(..., description="Number of requests waiting")
    is_processing: bool = Field(..., description="Whether an analysis is currently running")
    estimated_wait_seconds: int = Field(..., description="Estimated wait time in seconds")
    daily_quota: dict = Field(..., description="Daily quota information")


class EnqueueRequest(BaseModel):
    """Request to join the analysis queue"""
    session_id: Optional[str] = Field(default=None, description="Existing session ID (auto-generated if not provided)")
    domain: str = Field(default="Software Engineering", description="Analysis domain")


class EnqueueResponse(BaseModel):
    """Response after joining the queue"""
    status: str = Field(...)
    entry: QueueEntryResponse = Field(...)
    queue_info: QueueInfoResponse = Field(...)
    message: str = Field(..., description="User-friendly message")


class QueueErrorResponse(BaseModel):
    """Error response for queue operations"""
    status: str = Field(default="error")
    error_code: str = Field(..., description="Error code: QUOTA_EXHAUSTED, ALREADY_QUEUED, etc.")
    message: str = Field(..., description="User-friendly error message")
    retry_after_seconds: Optional[int] = Field(default=None, description="When to retry (if applicable)")
