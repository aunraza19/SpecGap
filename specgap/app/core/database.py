"""
Database module for SpecGap - Audit History & Persistence
Uses SQLAlchemy with SQLite (easily switchable to PostgreSQL)
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import json

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# Database URL - defaults to SQLite, can be overridden via env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./specgap_audits.db")

# Create engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ============== MODELS ==============

class AuditRecord(Base):
    """
    Main audit record - stores complete analysis results
    """
    __tablename__ = "audit_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Project identification
    project_name = Column(String(255), nullable=True, index=True)
    audit_type = Column(String(50), nullable=False)  # 'tech_spec', 'proposal', 'full_audit'
    
    # File metadata
    tech_spec_filename = Column(String(255), nullable=True)
    tech_spec_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for deduplication
    proposal_filename = Column(String(255), nullable=True)
    proposal_hash = Column(String(64), nullable=True, index=True)
    has_diagram = Column(Boolean, default=False)
    
    # Analysis results (stored as JSON)
    tech_gaps = Column(JSON, nullable=True)
    proposal_risks = Column(JSON, nullable=True)
    contradictions = Column(JSON, nullable=True)
    patch_pack = Column(JSON, nullable=True)
    
    # Computed scores
    ambiguity_score = Column(Float, nullable=True)
    leverage_score = Column(Float, nullable=True)
    composite_risk_score = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)  # 'Low', 'Medium', 'High', 'Critical'
    
    # Extracted text (for re-analysis without re-uploading)
    tech_spec_text = Column(Text, nullable=True)
    proposal_text = Column(Text, nullable=True)
    
    # User tracking (for future multi-tenancy)
    user_id = Column(String(36), nullable=True, index=True)
    organization_id = Column(String(36), nullable=True, index=True)
    
    # Status
    status = Column(String(20), default="completed")  # 'processing', 'completed', 'failed'
    error_message = Column(Text, nullable=True)


class AuditComment(Base):
    """
    User comments/notes on audit findings
    """
    __tablename__ = "audit_comments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    finding_type = Column(String(50), nullable=True)  # 'gap', 'trap', 'contradiction'
    finding_index = Column(Integer, nullable=True)  # Which finding this comment is about
    
    comment_text = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    
    user_id = Column(String(36), nullable=True)


# ============== DATABASE INITIALIZATION ==============

def init_db():
    """
    Create all tables. Call this on application startup.
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all tables. USE WITH CAUTION - for testing only.
    """
    Base.metadata.drop_all(bind=engine)


# ============== SESSION MANAGEMENT ==============

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Ensures proper cleanup even if errors occur.
    
    Usage:
        with get_db_session() as db:
            db.query(AuditRecord).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db():
    """
    Dependency for FastAPI endpoints.
    
    Usage:
        @app.get("/audits")
        def list_audits(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============== CRUD OPERATIONS ==============

class AuditRepository:
    """
    Repository pattern for audit operations.
    Encapsulates all database queries.
    """
    
    @staticmethod
    def create_audit(
        db: Session,
        audit_type: str,
        tech_gaps: Optional[Dict] = None,
        proposal_risks: Optional[Dict] = None,
        contradictions: Optional[Dict] = None,
        patch_pack: Optional[Dict] = None,
        tech_spec_filename: Optional[str] = None,
        tech_spec_hash: Optional[str] = None,
        tech_spec_text: Optional[str] = None,
        proposal_filename: Optional[str] = None,
        proposal_hash: Optional[str] = None,
        proposal_text: Optional[str] = None,
        has_diagram: bool = False,
        project_name: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> AuditRecord:
        """
        Create a new audit record with all analysis results.
        """
        # Calculate scores from results
        ambiguity_score = None
        leverage_score = None
        composite_risk_score = None
        risk_level = None
        
        if tech_gaps:
            ambiguity_score = tech_gaps.get("ambiguity_score")
        
        if proposal_risks:
            leverage_score = proposal_risks.get("leverage_score")
        
        # Calculate composite risk if we have enough data
        if ambiguity_score is not None or leverage_score is not None:
            composite_risk_score, risk_level = AuditRepository._calculate_composite_risk(
                tech_gaps, proposal_risks, contradictions
            )
        
        audit = AuditRecord(
            audit_type=audit_type,
            project_name=project_name,
            tech_spec_filename=tech_spec_filename,
            tech_spec_hash=tech_spec_hash,
            tech_spec_text=tech_spec_text,
            proposal_filename=proposal_filename,
            proposal_hash=proposal_hash,
            proposal_text=proposal_text,
            has_diagram=has_diagram,
            tech_gaps=tech_gaps,
            proposal_risks=proposal_risks,
            contradictions=contradictions,
            patch_pack=patch_pack,
            ambiguity_score=ambiguity_score,
            leverage_score=leverage_score,
            composite_risk_score=composite_risk_score,
            risk_level=risk_level,
            user_id=user_id,
            organization_id=organization_id,
            status="completed"
        )
        
        db.add(audit)
        db.flush()  # Get the ID without committing
        return audit
    
    @staticmethod
    def _calculate_composite_risk(
        tech_gaps: Optional[Dict],
        proposal_risks: Optional[Dict],
        contradictions: Optional[Dict]
    ) -> tuple[float, str]:
        """
        Calculate composite risk score from individual analyses.
        Returns (score, level) tuple.
        """
        ambiguity = (tech_gaps or {}).get("ambiguity_score", 50)
        leverage = (proposal_risks or {}).get("leverage_score", 50)
        
        # Count critical issues
        critical_gaps = len([
            g for g in (tech_gaps or {}).get("critical_gaps", [])
            if isinstance(g, dict) and g.get("risk_level") == "High"
        ])
        trap_count = len((proposal_risks or {}).get("trap_clauses", []))
        contradiction_count = len((contradictions or {}).get("contradictions", []))
        
        # Weighted composite (0-100, higher = more risk)
        composite = (
            (100 - ambiguity) * 0.25 +  # Tech clarity (inverted)
            leverage * 0.30 +            # Vendor leverage
            min(critical_gaps * 10, 25) + # Gap penalty
            min(trap_count * 8, 15) +     # Trap penalty
            min(contradiction_count * 5, 10)  # Contradiction penalty
        )
        
        composite = min(max(composite, 0), 100)  # Clamp to 0-100
        
        if composite > 70:
            level = "Critical"
        elif composite > 50:
            level = "High"
        elif composite > 30:
            level = "Medium"
        else:
            level = "Low"
        
        return round(composite, 1), level
    
    @staticmethod
    def get_audit_by_id(db: Session, audit_id: str) -> Optional[AuditRecord]:
        """Retrieve a single audit by ID."""
        return db.query(AuditRecord).filter(AuditRecord.id == audit_id).first()
    
    @staticmethod
    def get_audits(
        db: Session,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        audit_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AuditRecord]:
        """
        Retrieve audits with optional filtering.
        """
        query = db.query(AuditRecord)
        
        if user_id:
            query = query.filter(AuditRecord.user_id == user_id)
        if organization_id:
            query = query.filter(AuditRecord.organization_id == organization_id)
        if audit_type:
            query = query.filter(AuditRecord.audit_type == audit_type)
        if risk_level:
            query = query.filter(AuditRecord.risk_level == risk_level)
        
        return query.order_by(AuditRecord.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def find_by_file_hash(db: Session, file_hash: str) -> Optional[AuditRecord]:
        """
        Find existing audit by file hash (for duplicate detection).
        """
        return db.query(AuditRecord).filter(
            (AuditRecord.tech_spec_hash == file_hash) | 
            (AuditRecord.proposal_hash == file_hash)
        ).order_by(AuditRecord.created_at.desc()).first()
    
    @staticmethod
    def get_statistics(db: Session, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregate statistics for dashboard.
        """
        query = db.query(AuditRecord)
        if organization_id:
            query = query.filter(AuditRecord.organization_id == organization_id)
        
        audits = query.all()
        
        if not audits:
            return {
                "total_audits": 0,
                "by_type": {},
                "by_risk_level": {},
                "avg_risk_score": None
            }
        
        by_type = {}
        by_risk = {}
        risk_scores = []
        
        for audit in audits:
            # Count by type
            by_type[audit.audit_type] = by_type.get(audit.audit_type, 0) + 1
            
            # Count by risk level
            if audit.risk_level:
                by_risk[audit.risk_level] = by_risk.get(audit.risk_level, 0) + 1
            
            # Collect risk scores
            if audit.composite_risk_score is not None:
                risk_scores.append(audit.composite_risk_score)
        
        return {
            "total_audits": len(audits),
            "by_type": by_type,
            "by_risk_level": by_risk,
            "avg_risk_score": round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else None
        }
    
    @staticmethod
    def delete_audit(db: Session, audit_id: str) -> bool:
        """Delete an audit record."""
        audit = db.query(AuditRecord).filter(AuditRecord.id == audit_id).first()
        if audit:
            db.delete(audit)
            return True
        return False


# ============== COMMENT OPERATIONS ==============

class CommentRepository:
    """Repository for audit comments."""
    
    @staticmethod
    def add_comment(
        db: Session,
        audit_id: str,
        comment_text: str,
        finding_type: Optional[str] = None,
        finding_index: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> AuditComment:
        """Add a comment to an audit finding."""
        comment = AuditComment(
            audit_id=audit_id,
            comment_text=comment_text,
            finding_type=finding_type,
            finding_index=finding_index,
            user_id=user_id
        )
        db.add(comment)
        db.flush()
        return comment
    
    @staticmethod
    def get_comments(db: Session, audit_id: str) -> List[AuditComment]:
        """Get all comments for an audit."""
        return db.query(AuditComment).filter(
            AuditComment.audit_id == audit_id
        ).order_by(AuditComment.created_at).all()
    
    @staticmethod
    def resolve_comment(db: Session, comment_id: str) -> Optional[AuditComment]:
        """Mark a comment as resolved."""
        comment = db.query(AuditComment).filter(AuditComment.id == comment_id).first()
        if comment:
            comment.resolved = True
            comment.resolved_at = datetime.utcnow()
        return comment
