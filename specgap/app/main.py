from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import init_db, get_db, get_db_session, AuditRepository, AuditRecord
from app.services.parser import extract_text_from_file
# We only import the new Council App. Old engines are removed.
from app.services.workflow import council_app 
from app.services.patch_pack import build_patch_pack_files
from app.services.tech_engine import analyze_tech_gaps
from app.services.biz_engine import analyze_proposal_leverage
from app.services.cross_check import run_cross_check

import logging
import sys

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api")

app = FastAPI(title=settings.PROJECT_NAME)

# CORS middleware - allow frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up SpecGap Backend Service")
    init_db()

@app.get("/")
async def health_check():
    return {
        "status": "active", 
        "system": "SpecGap Council (MVP)", 
        "architecture": "3-Loop Recursive Consensus"
    }


class PatchPackRequest(BaseModel):
    selected_cards: List[Dict[str, Any]]
    domain: str = "Software Engineering"


# ============== AUDIT HISTORY ENDPOINTS ==============

@app.get("/audits")
async def list_audits(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all past audits from database."""
    logger.info(f"Fetching audit history (limit={limit})")
    audits = AuditRepository.get_audits(db, limit=limit)
    return {
        "audits": [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "project_name": a.project_name,
                "audit_type": a.audit_type,
                "tech_spec_filename": a.tech_spec_filename,
                "risk_level": a.risk_level,
                "composite_risk_score": a.composite_risk_score,
                "status": a.status
            }
            for a in audits
        ]
    }


@app.get("/audits/{audit_id}")
async def get_audit(
    audit_id: str,
    db: Session = Depends(get_db)
):
    """Get full details of a specific audit."""
    logger.info(f"Fetching audit details: {audit_id}")
    audit = AuditRepository.get_audit_by_id(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {
        "id": audit.id,
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
        "project_name": audit.project_name,
        "audit_type": audit.audit_type,
        "tech_spec_filename": audit.tech_spec_filename,
        "risk_level": audit.risk_level,
        "composite_risk_score": audit.composite_risk_score,
        "status": audit.status,
        "patch_pack": audit.patch_pack,
        "tech_gaps": audit.tech_gaps,
        "proposal_risks": audit.proposal_risks,
        "contradictions": audit.contradictions
    }


@app.post("/audit/council-session")
async def run_council_session(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering", description="Domain context for the council prompts")
):
 
    combined_text = ""
    file_names = []
    
    for f in files:
        await f.seek(0) 
        text, _ = await extract_text_from_file(f)
        combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
        file_names.append(f.filename)
        
    print(f"--- Starting Council Session for: {file_names} ---")
        
    initial_state = {
        "combined_context": combined_text,
        "domain": domain,
        "round_1_drafts": {},
        "round_2_drafts": {},
        "round_3_final": {},
        "patch_pack": {}
    }
    
    try:
        logger.info("Invoking Council Workflow...")
        result = await council_app.ainvoke(initial_state)
        
        # Save to database
        flashcard_count = len(result.get("patch_pack", {}).get("flashcards", []))
        logger.info(f"Council Session Complete. Flashcards generated: {flashcard_count}")
        
        try:
            with get_db_session() as db:
                AuditRepository.create_audit(
                    db,
                    audit_type="council_session",
                    patch_pack=result.get("patch_pack"),
                    tech_spec_filename=",".join(file_names),
                    project_name=file_names[0] if file_names else "Untitled"
                )
                logger.info("Audit saved to database")
        except Exception as db_error:
            logger.warning(f"Failed to save audit to DB: {db_error}")
        
        return {
            "status": "success",
            "files_analyzed": file_names,
            "domain": domain,
            "council_verdict": result["patch_pack"]
        }
        
    except Exception as e:
        logger.error(f"Council Runtime Error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "The Council failed to reach a verdict.",
            "details": str(e)
        }


@app.post("/audit/patch-pack")
async def generate_patch_pack(request: PatchPackRequest):
    
    try:
        files = await build_patch_pack_files(request.selected_cards, request.domain)
        return {
            "status": "success",
            "files": files
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to generate Patch Pack.",
            "details": str(e)
        }



@app.post("/audit/deep-analysis")
async def run_deep_analysis(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering", description="Domain context")
):
    """
    Deep Audit Mode: Executive-grade analysis with:
    - Tech Gap Detection (Architect Agent)
    - Legal Leverage Score & Trap Detection (Lawyer Agent)
    - Cross-Check Synthesis with Mermaid Diagram
    - Auto-generated JIRA Tickets
    - Pre-written Negotiation Email
    
    Use this for detailed reports. Use /audit/council-session for quick flashcards.
    """
    
    # 1. Parse all files into combined context
    combined_text = ""
    file_names = []
    
    for f in files:
        await f.seek(0)
        text, _ = await extract_text_from_file(f)
        combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
        file_names.append(f.filename)
    
    print(f"--- Deep Analysis for: {file_names} ---")
    
    try:
        # 2. Run Tech Engine (Architect Agent)
        print("[Deep Audit] Running Tech Gap Analysis...")
        tech_report = await analyze_tech_gaps(combined_text)
        
        # 3. Run Biz Engine (Legal/Negotiator Agent)
        print("[Deep Audit] Running Legal Leverage Analysis...")
        legal_report = await analyze_proposal_leverage(combined_text)
        
        # 4. Run Cross-Check (Orchestrator Agent)
        print("[Deep Audit] Running Cross-Check Synthesis...")
        synthesis = await run_cross_check(
            tech_text=combined_text,
            proposal_text=combined_text,  # Same docs, different lens
            tech_report=tech_report,
            legal_report=legal_report
        )
        
        # 5. Build response
        return {
            "status": "success",
            "mode": "deep_analysis",
            "files_analyzed": file_names,
            "domain": domain,
            "tech_audit": tech_report,
            "legal_audit": legal_report,
            "executive_synthesis": synthesis
        }
        
    except Exception as e:
        print(f"Deep Analysis Error: {e}")
        return {
            "status": "error",
            "message": "Deep analysis failed.",
            "details": str(e)
        }



@app.post("/audit/full-spectrum")
async def run_full_spectrum_analysis(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering", description="Domain context")
):
 
    import asyncio
    
    combined_text = ""
    file_names = []
    file_bytes_cache = {}  # Cache for re-reading
    
    for f in files:
        await f.seek(0)
        content = await f.read()
        file_bytes_cache[f.filename] = content
        await f.seek(0)
        text, _ = await extract_text_from_file(f)
        combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
        file_names.append(f.filename)
    
    print(f"--- Full Spectrum Analysis for: {file_names} ---")
    
    council_state = {
        "combined_context": combined_text,
        "domain": domain,
        "round_1_drafts": {},
        "round_2_drafts": {},
        "round_3_final": {},
        "patch_pack": {}
    }
    
    try:
        print("[Full Spectrum] Running Council Session...")
        council_result = await council_app.ainvoke(council_state)
        
        print("[Full Spectrum] Running Deep Analysis...")
        tech_report = await analyze_tech_gaps(combined_text)
        legal_report = await analyze_proposal_leverage(combined_text)
        synthesis = await run_cross_check(
            tech_text=combined_text,
            proposal_text=combined_text,
            tech_report=tech_report,
            legal_report=legal_report
        )
        
        return {
            "status": "success",
            "mode": "full_spectrum",
            "files_analyzed": file_names,
            "domain": domain,
            "council_verdict": council_result["patch_pack"],
            "deep_analysis": {
                "tech_audit": tech_report,
                "legal_audit": legal_report,
                "executive_synthesis": synthesis
            }
        }
        
    except Exception as e:
        print(f"Full Spectrum Error: {e}")
        return {
            "status": "error",
            "message": "Full spectrum analysis failed.",
            "details": str(e)
        }