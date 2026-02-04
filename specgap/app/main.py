from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import (
    init_db, get_db, AuditRepository, CommentRepository, AuditRecord
)
from app.services.parser import extract_text_from_pdf, compute_file_hash
from app.services.tech_engine import analyze_tech_gaps
from app.services.biz_engine import analyze_proposal_leverage
from app.services.parser import encode_image_for_gemini
from app.services.cross_check import run_cross_check
from app.services.workflow import app_workflow # <--- Import the Graph


app = FastAPI(title=settings.PROJECT_NAME)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def health_check():
    return {"status": "active", "system": "SpecGap Engine", "version": "2.0"}


# ============== ANALYSIS ENDPOINTS ==============

@app.post("/audit/agent-swarm")
async def run_agent_swarm(
    files: List[UploadFile] = File(...),
):
 
    # Initialize State
    initial_state = {
        "raw_files": files,
        "filenames": [f.filename for f in files],
        "document_map": {},
        "combined_context": "",
        "tech_report": {},
        "legal_report": {},
        "final_report": {},
        "errors": []
    }
    
    # Invoke the Graph
    try:
        result = await app_workflow.ainvoke(initial_state)
        
        return {
            "status": "success",
            "files_analyzed": initial_state["filenames"],
            "tech_analysis": result.get("tech_report"),
            "legal_analysis": result.get("legal_report"),
            "final_synthesis": result.get("final_report"),
            "errors": result.get("errors")
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "stage": "Graph Execution"
        }

@app.post("/analyze/tech-spec")
async def analyze_tech_spec_endpoint(
    file: UploadFile = File(...),
    project_name: Optional[str] = Query(None, description="Optional project name for tracking"),
    force_ocr: bool = Query(False, description="Force OCR even for text-based PDFs"),
    db: Session = Depends(get_db)
):
 
    # 1. Validate File Type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported currently.")
    
    file_bytes = await file.read()
    file_hash = compute_file_hash(file_bytes)
    text_content = await extract_text_from_pdf(file_bytes, force_ocr=force_ocr)
    
    if "Error" in text_content and len(text_content) < 100:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {text_content}")

    analysis_result = await analyze_tech_gaps(text_content)
    
    # 4. Save to database
    audit = AuditRepository.create_audit(
        db=db,
        audit_type="tech_spec",
        tech_gaps=analysis_result,
        tech_spec_filename=file.filename,
        tech_spec_hash=file_hash,
        tech_spec_text=text_content[:50000],  # Limit stored text
        project_name=project_name
    )
    db.commit()
    
    # 5. Return result with audit ID
    return {
        "audit_id": audit.id,
        "risk_level": audit.risk_level,
        "composite_risk_score": audit.composite_risk_score,
        **analysis_result
    }


@app.post("/analyze/proposal")
async def analyze_proposal_endpoint(
    file: UploadFile = File(...),
    project_name: Optional[str] = Query(None),
    force_ocr: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Upload a Proposal/Contract (PDF) -> Get Leverage Score & Traps
    """
    # 1. Validate
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # 2. Extract Text
    file_bytes = await file.read()
    file_hash = compute_file_hash(file_bytes)
    text_content = await extract_text_from_pdf(file_bytes, force_ocr=force_ocr)
    
    if "Error" in text_content:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {text_content}")

    # 3. Run Engine B (The Lawyer)
    result = await analyze_proposal_leverage(text_content)
    
    # 4. Save to database
    audit = AuditRepository.create_audit(
        db=db,
        audit_type="proposal",
        proposal_risks=result,
        proposal_filename=file.filename,
        proposal_hash=file_hash,
        proposal_text=text_content[:50000],
        project_name=project_name
    )
    db.commit()
    
    return {
        "audit_id": audit.id,
        "risk_level": audit.risk_level,
        "composite_risk_score": audit.composite_risk_score,
        **result
    }


@app.post("/audit/full")
async def full_audit_endpoint(
    tech_spec: UploadFile = File(...),
    proposal: UploadFile = File(...),
    diagram: UploadFile = File(None),
    project_name: Optional[str] = Query(None),
    force_ocr: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    THE MASTER ENDPOINT:
    Upload Tech Spec + Proposal + (Optional) Diagram.
    Returns: Contradictions + Patch Pack (Jira/Email) + Full Risk Analysis.
    """
    
    # 1. Parse Texts
    tech_bytes = await tech_spec.read()
    prop_bytes = await proposal.read()
    
    tech_hash = compute_file_hash(tech_bytes)
    prop_hash = compute_file_hash(prop_bytes)
    
    tech_text = await extract_text_from_pdf(tech_bytes, force_ocr=force_ocr)
    prop_text = await extract_text_from_pdf(prop_bytes, force_ocr=force_ocr)
    
    if "Error" in tech_text:
        raise HTTPException(status_code=400, detail=f"Tech spec error: {tech_text}")
    if "Error" in prop_text:
        raise HTTPException(status_code=400, detail=f"Proposal error: {prop_text}")
    
    # 2. Parse Diagram (if uploaded)
    diagram_data = None
    if diagram:
        img_bytes = await diagram.read()
        diagram_data = encode_image_for_gemini(img_bytes, mime_type=diagram.content_type)

    # 3. Run All Engines in parallel (conceptually)
    tech_gaps = await analyze_tech_gaps(tech_text)
    proposal_risks = await analyze_proposal_leverage(prop_text)
    
    # 3.1 Run Cross-Check as the ORCHESTRATOR (Agentic Flow)
    # We pass the results of the previous agents to the final synthesizer
    cross_check_result = await run_cross_check(
        tech_text, 
        prop_text, 
        diagram_data,
        tech_report=tech_gaps,
        legal_report=proposal_risks
    )
    
    # 4. Save comprehensive audit
    audit = AuditRepository.create_audit(
        db=db,
        audit_type="full_audit",
        tech_gaps=tech_gaps,
        proposal_risks=proposal_risks,
        contradictions=cross_check_result.get("contradictions"),
        patch_pack=cross_check_result.get("patch_pack"),
        tech_spec_filename=tech_spec.filename,
        tech_spec_hash=tech_hash,
        tech_spec_text=tech_text[:50000],
        proposal_filename=proposal.filename,
        proposal_hash=prop_hash,
        proposal_text=prop_text[:50000],
        has_diagram=diagram is not None,
        project_name=project_name
    )
    db.commit()
    
    return {
        "audit_id": audit.id,
        "risk_level": audit.risk_level,
        "composite_risk_score": audit.composite_risk_score,
        "tech_analysis": tech_gaps,
        "proposal_analysis": proposal_risks,
        **cross_check_result
    }


# ============== HISTORY & RETRIEVAL ENDPOINTS ==============

@app.get("/audits")
async def list_audits(
    audit_type: Optional[str] = Query(None, description="Filter by type: tech_spec, proposal, full_audit"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: Low, Medium, High, Critical"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all audits with optional filtering.
    """
    audits = AuditRepository.get_audits(
        db=db,
        audit_type=audit_type,
        risk_level=risk_level,
        limit=limit,
        offset=offset
    )
    
    return {
        "count": len(audits),
        "audits": [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "audit_type": a.audit_type,
                "project_name": a.project_name,
                "risk_level": a.risk_level,
                "composite_risk_score": a.composite_risk_score,
                "tech_spec_filename": a.tech_spec_filename,
                "proposal_filename": a.proposal_filename
            }
            for a in audits
        ]
    }


@app.get("/audits/{audit_id}")
async def get_audit(audit_id: str, db: Session = Depends(get_db)):
    """
    Get full details of a specific audit.
    """
    audit = AuditRepository.get_audit_by_id(db, audit_id)
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Get comments
    comments = CommentRepository.get_comments(db, audit_id)
    
    return {
        "id": audit.id,
        "created_at": audit.created_at.isoformat(),
        "audit_type": audit.audit_type,
        "project_name": audit.project_name,
        "status": audit.status,
        "risk_summary": {
            "composite_risk_score": audit.composite_risk_score,
            "risk_level": audit.risk_level,
            "ambiguity_score": audit.ambiguity_score,
            "leverage_score": audit.leverage_score
        },
        "files": {
            "tech_spec": audit.tech_spec_filename,
            "proposal": audit.proposal_filename,
            "has_diagram": audit.has_diagram
        },
        "tech_gaps": audit.tech_gaps,
        "proposal_risks": audit.proposal_risks,
        "contradictions": audit.contradictions,
        "patch_pack": audit.patch_pack,
        "comments": [
            {
                "id": c.id,
                "text": c.comment_text,
                "finding_type": c.finding_type,
                "finding_index": c.finding_index,
                "resolved": c.resolved,
                "created_at": c.created_at.isoformat()
            }
            for c in comments
        ]
    }


@app.delete("/audits/{audit_id}")
async def delete_audit(audit_id: str, db: Session = Depends(get_db)):
    """
    Delete an audit record.
    """
    success = AuditRepository.delete_audit(db, audit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    db.commit()
    return {"message": "Audit deleted successfully"}


@app.get("/audits/stats/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get aggregate statistics for dashboard view.
    """
    stats = AuditRepository.get_statistics(db)
    return stats


# ============== COMMENT ENDPOINTS ==============

@app.post("/audits/{audit_id}/comments")
async def add_comment(
    audit_id: str,
    comment_text: str = Query(..., min_length=1),
    finding_type: Optional[str] = Query(None),
    finding_index: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Add a comment/note to an audit finding.
    """
    # Verify audit exists
    audit = AuditRepository.get_audit_by_id(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    comment = CommentRepository.add_comment(
        db=db,
        audit_id=audit_id,
        comment_text=comment_text,
        finding_type=finding_type,
        finding_index=finding_index
    )
    db.commit()
    
    return {"comment_id": comment.id, "message": "Comment added"}


@app.patch("/comments/{comment_id}/resolve")
async def resolve_comment(comment_id: str, db: Session = Depends(get_db)):
    """
    Mark a comment as resolved.
    """
    comment = CommentRepository.resolve_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.commit()
    return {"message": "Comment resolved"}


# ============== UTILITY ENDPOINTS ==============

@app.post("/check-duplicate")
async def check_duplicate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Check if a file has been analyzed before (by hash).
    Returns previous audit if found.
    """
    file_bytes = await file.read()
    file_hash = compute_file_hash(file_bytes)
    
    existing = AuditRepository.find_by_file_hash(db, file_hash)
    
    if existing:
        return {
            "duplicate": True,
            "existing_audit_id": existing.id,
            "analyzed_at": existing.created_at.isoformat(),
            "risk_level": existing.risk_level
        }
    
    return {"duplicate": False}