"""
SpecGap API - AI-Powered Specification Gap & Contract Risk Analyzer
Main FastAPI application with middleware, versioning, and organized routes.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import json

from app.core.config import settings
from app.core.database import init_db, get_db, get_db_session, AuditRepository
from app.core.logging import setup_logging, get_logger
from app.core.middleware import (
    RequestTrackingMiddleware,
    ErrorHandlingMiddleware,
    AIRateLimitMiddleware,
)
from app.schemas import (
    HealthResponse,
    PatchPackRequest,
)
from app.services.parser import extract_text_from_file, compute_file_hash
from app.services.workflow import council_app
from app.services.patch_pack import build_patch_pack_files
from app.services.tech_engine import analyze_tech_gaps
from app.services.biz_engine import analyze_proposal_leverage
from app.services.cross_check import run_cross_check


# ============== LOGGING SETUP ==============

setup_logging(
    level=settings.LOG_LEVEL,
    json_format=settings.LOG_FORMAT_JSON,
    log_file=settings.LOG_FILE
)
logger = get_logger("main")


# ============== LIFESPAN ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    init_db()
    logger.info("Database initialized")

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down SpecGap")


# ============== APP INITIALIZATION ==============

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ============== MIDDLEWARE ==============

# CORS (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (order matters - last added = first executed)
app.add_middleware(AIRateLimitMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestTrackingMiddleware)


# ============== HEALTH & INFO ENDPOINTS ==============

@app.get("/", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="active",
        system="SpecGap Council (MVP)",
        architecture="3-Loop Recursive Consensus",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc)
    )


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def api_health():
    """API v1 health check"""
    return await health_check()


# ============== COUNCIL SESSION ENDPOINT ==============

@app.post("/api/v1/audit/council-session", tags=["Audit"])
async def run_council_session(
    files: List[UploadFile] = File(..., description="Documents to analyze (PDF, DOCX, TXT)"),
    domain: str = Query("Software Engineering", description="Domain context for analysis")
):
    """
    Quick Analysis Mode: 3-Round Council Deliberation

    Three AI agents (Legal, Business, Finance) analyze your documents through:
    1. **Round 1**: Independent analysis (blind draft)
    2. **Round 2**: Cross-check each other's findings
    3. **Round 3**: Generate actionable flashcards

    Returns Tinder-style flashcards for quick decision making.
    """
    combined_text = ""
    file_names = []
    
    for f in files:
        await f.seek(0)
        text, metadata = await extract_text_from_file(f)
        combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
        file_names.append(f.filename)

    logger.info(f"Council session started for: {file_names}")

    initial_state = {
        "combined_context": combined_text,
        "domain": domain,
        "round_1_drafts": {},
        "round_2_drafts": {},
        "round_3_final": {},
        "patch_pack": {},
        "errors": {}
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
        logger.error(f"Council session failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "The Council failed to reach a verdict.",
                "details": str(e)
            }
        )


# ============== STREAMING COUNCIL SESSION (SSE) ==============

@app.post("/api/v1/audit/council-session/stream", tags=["Audit"])
async def stream_council_session(
    files: List[UploadFile] = File(..., description="Documents to analyze"),
    domain: str = Query("Software Engineering", description="Domain context")
):
    """
    Stream the Council Session progress via Server-Sent Events (SSE).

    Events sent:
    - `stage`: Current processing stage (council, round1, round2, round3, synthesis)
    - `complete`: Final result with all flashcards
    - `error`: Error message if something fails
    """
    # Pre-process files (non-streaming part)
    combined_text = ""
    file_names = []

    try:
        for f in files:
            await f.seek(0)
            text, _ = await extract_text_from_file(f)
            combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
            file_names.append(f.filename)
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read files: {str(e)}")

    logger.info(f"Stream session started for: {file_names}")

    initial_state = {
        "combined_context": combined_text,
        "domain": domain,
        "round_1_drafts": {},
        "round_2_drafts": {},
        "round_3_final": {},
        "patch_pack": {},
        "errors": {}
    }

    async def event_generator():
        try:
            # Yield initial event
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'council'})}\n\n"

            # Start workflow stream
            # stream_mode="updates" yields the output of each node as it completes
            async for chunk in council_app.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    logger.info(f"Node completed: {node_name}")

                    if node_name == "round_1":
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'round1'})}\n\n"
                    elif node_name == "round_2":
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'round2'})}\n\n"
                    elif node_name == "round_3":
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'round3'})}\n\n"
                    elif node_name == "pack_generator":
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'synthesis'})}\n\n"
                        # Also yield the final result
                        final_payload = {
                            "status": "success",
                            "files_analyzed": file_names,
                            "domain": domain,
                            "council_verdict": node_output.get("patch_pack", {})
                        }
                        yield f"data: {json.dumps({'type': 'complete', 'result': final_payload})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Legacy endpoint (deprecated, use /api/v1/audit/council-session)
@app.post("/audit/council-session", tags=["Audit (Legacy)"], deprecated=True)
async def run_council_session_legacy(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering")
):
    """Legacy endpoint - use /api/v1/audit/council-session instead"""
    return await run_council_session(files, domain)


# ============== PATCH PACK ENDPOINT ==============

@app.post("/api/v1/audit/patch-pack", tags=["Audit"])
async def generate_patch_pack(request: PatchPackRequest):
    """
    Generate Patch Pack from selected flashcards

    After reviewing flashcards from council-session, send the ones you
    "swiped right" on to generate:
    - Contract Addendum (legal fixes)
    - Spec Update (business requirements)
    - Negotiation Email (pre-written vendor communication)
    """
    try:
        logger.info(f"Generating patch pack from {len(request.selected_cards)} cards")

        files = await build_patch_pack_files(request.selected_cards, request.domain)

        return {
            "status": "success",
            "files": files
        }
    except Exception as e:
        logger.error(f"Patch pack generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to generate Patch Pack.",
                "details": str(e)
            }
        )


@app.post("/audit/patch-pack", tags=["Audit (Legacy)"], deprecated=True)
async def generate_patch_pack_legacy(request: PatchPackRequest):
    """Legacy endpoint - use /api/v1/audit/patch-pack instead"""
    return await generate_patch_pack(request)


# ============== DEEP ANALYSIS ENDPOINT ==============

@app.post("/api/v1/audit/deep-analysis", tags=["Audit"])
async def run_deep_analysis(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering", description="Domain context")
):
    """
    Deep Audit Mode: Executive-grade analysis

    Comprehensive analysis including:
    - **Tech Gap Detection** (Architect Agent)
    - **Legal Leverage Score** & Trap Detection (Lawyer Agent)
    - **Cross-Check Synthesis** with Mermaid Diagram
    - **Auto-generated JIRA Tickets**
    - **Pre-written Negotiation Email**

    Use this for detailed reports. Use /council-session for quick flashcards.
    """
    combined_text = ""
    file_names = []
    
    for f in files:
        await f.seek(0)
        text, _ = await extract_text_from_file(f)
        combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
        file_names.append(f.filename)
    
    logger.info(f"Deep analysis started for: {file_names}")

    try:
        # Run Tech Engine
        logger.info("[Deep Audit] Running Tech Gap Analysis...")
        tech_report = await analyze_tech_gaps(combined_text)
        
        # Run Biz Engine
        logger.info("[Deep Audit] Running Legal Leverage Analysis...")
        legal_report = await analyze_proposal_leverage(combined_text)
        
        # Run Cross-Check
        logger.info("[Deep Audit] Running Cross-Check Synthesis...")
        synthesis = await run_cross_check(
            tech_text=combined_text,
            proposal_text=combined_text,
            tech_report=tech_report,
            legal_report=legal_report
        )
        
        logger.info("Deep analysis completed successfully")

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
        logger.error(f"Deep analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Deep analysis failed.",
                "details": str(e)
            }
        )


@app.post("/audit/deep-analysis", tags=["Audit (Legacy)"], deprecated=True)
async def run_deep_analysis_legacy(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering")
):
    """Legacy endpoint - use /api/v1/audit/deep-analysis instead"""
    return await run_deep_analysis(files, domain)


# ============== FULL SPECTRUM ENDPOINT ==============

@app.post("/api/v1/audit/full-spectrum", tags=["Audit"])
async def run_full_spectrum_analysis(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering", description="Domain context")
):
    """
    Full Spectrum Mode: Council + Deep Analysis combined

    The most comprehensive analysis combining:
    - Council Session (flashcards for quick decisions)
    - Deep Analysis (detailed reports)

    Best for critical contracts and major technical decisions.
    """
    combined_text = ""
    file_names = []

    for f in files:
        await f.seek(0)
        text, _ = await extract_text_from_file(f)
        combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
        file_names.append(f.filename)
    
    logger.info(f"Full spectrum analysis started for: {file_names}")

    council_state = {
        "combined_context": combined_text,
        "domain": domain,
        "round_1_drafts": {},
        "round_2_drafts": {},
        "round_3_final": {},
        "patch_pack": {},
        "errors": {}
    }
    
    try:
        # Council Session
        logger.info("[Full Spectrum] Running Council Session...")
        council_result = await council_app.ainvoke(council_state)
        
        # Deep Analysis
        logger.info("[Full Spectrum] Running Deep Analysis...")
        tech_report = await analyze_tech_gaps(combined_text)
        legal_report = await analyze_proposal_leverage(combined_text)
        synthesis = await run_cross_check(
            tech_text=combined_text,
            proposal_text=combined_text,
            tech_report=tech_report,
            legal_report=legal_report
        )
        
        logger.info("Full spectrum analysis completed successfully")

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
        logger.error(f"Full spectrum analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Full spectrum analysis failed.",
                "details": str(e)
            }
        )


# ============== STREAMING FULL SPECTRUM (SSE) ==============

@app.post("/api/v1/audit/full-spectrum/stream", tags=["Audit"])
async def stream_full_spectrum(
    files: List[UploadFile] = File(..., description="Documents to analyze"),
    domain: str = Query("Software Engineering", description="Domain context")
):
    """
    Stream the Full Spectrum analysis (Council + Deep) via Server-Sent Events (SSE).

    Events sent:
    - `stage`: Current processing stage (council, round1, round2, round3, tech_audit, legal_audit, synthesis)
    - `complete`: Final combined result
    - `error`: Error message if something fails
    """
    # Pre-process files
    combined_text = ""
    file_names = []

    try:
        for f in files:
            await f.seek(0)
            text, _ = await extract_text_from_file(f)
            combined_text += f"\n=== SOURCE DOCUMENT: {f.filename} ===\n{text}"
            file_names.append(f.filename)
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read files: {str(e)}")

    logger.info(f"Stream full-spectrum started for: {file_names}")

    council_state = {
        "combined_context": combined_text,
        "domain": domain,
        "round_1_drafts": {},
        "round_2_drafts": {},
        "round_3_final": {},
        "patch_pack": {},
        "errors": {}
    }

    async def event_generator():
        try:
            # --- PART 1: COUNCIL SESSION ---
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'council'})}\n\n"

            council_result = None

            # Stream Council Steps
            async for chunk in council_app.astream(council_state, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    if node_name == "round_1":
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'round1'})}\n\n"
                    elif node_name == "round_2":
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'round2'})}\n\n"
                    elif node_name == "round_3":
                        yield f"data: {json.dumps({'type': 'stage', 'stage': 'round3'})}\n\n"
                    elif node_name == "pack_generator":
                        # Council is done
                        council_result = node_output.get("patch_pack", {})

            # --- PART 2: DEEP ANALYSIS ---

            # Tech Audit
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'tech_audit'})}\n\n"
            logger.info("[Stream] Starting Tech Audit...")
            tech_report = await analyze_tech_gaps(combined_text)

            # Legal Audit
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'legal_audit'})}\n\n"
            logger.info("[Stream] Starting Legal Audit...")
            legal_report = await analyze_proposal_leverage(combined_text)

            # Synthesis
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'synthesis'})}\n\n"
            logger.info("[Stream] Starting Synthesis...")
            synthesis = await run_cross_check(
                tech_text=combined_text,
                proposal_text=combined_text,
                tech_report=tech_report,
                legal_report=legal_report
            )

            # --- FINAL COMPLETE ---
            final_payload = {
                "status": "success",
                "mode": "full_spectrum",
                "files_analyzed": file_names,
                "domain": domain,
                "council_verdict": council_result,
                "deep_analysis": {
                    "tech_audit": tech_report,
                    "legal_audit": legal_report,
                    "executive_synthesis": synthesis
                }
            }
            yield f"data: {json.dumps({'type': 'complete', 'result': final_payload})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/audit/full-spectrum", tags=["Audit (Legacy)"], deprecated=True)
async def run_full_spectrum_legacy(
    files: List[UploadFile] = File(...),
    domain: str = Query("Software Engineering")
):
    """Legacy endpoint - use /api/v1/audit/full-spectrum instead"""
    return await run_full_spectrum_analysis(files, domain)


# ============== DOCUMENT UTILITIES ==============

@app.post("/api/v1/documents/extract", tags=["Documents"])
async def extract_document_text(
    file: UploadFile = File(..., description="Document to extract text from")
):
    """
    Extract text from a document without analysis.

    Useful for previewing what the AI will see.
    """
    await file.seek(0)
    content = await file.read()
    file_hash = compute_file_hash(content)

    await file.seek(0)
    text, metadata = await extract_text_from_file(file)

    return {
        "status": "success",
        "filename": file.filename,
        "hash": file_hash,
        "metadata": metadata,
        "text_preview": text[:2000] + ("..." if len(text) > 2000 else ""),
        "total_chars": len(text)
    }


# ============== AUDIT HISTORY ==============

@app.get("/api/v1/audits", tags=["History"])
async def list_audits(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    audit_type: str = Query(None, description="Filter by audit type"),
    risk_level: str = Query(None, description="Filter by risk level")
):
    """
    List saved audit records with optional filtering.
    """
    with get_db_session() as db:
        audits = AuditRepository.get_audits(
            db,
            audit_type=audit_type,
            risk_level=risk_level,
            limit=limit,
            offset=offset
        )

        return {
            "status": "success",
            "audits": [
                {
                    "id": a.id,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "audit_type": a.audit_type,
                    "project_name": a.project_name,
                    "risk_level": a.risk_level,
                    "composite_risk_score": a.composite_risk_score
                }
                for a in audits
            ],
            "total": len(audits),
            "limit": limit,
            "offset": offset
        }


# Legacy audit list endpoint (for frontend compatibility)
@app.get("/audits", tags=["History (Legacy)"], deprecated=True)
async def list_audits_legacy(
    limit: int = Query(20, ge=1, le=100)
):
    """Legacy endpoint - use /api/v1/audits instead"""
    with get_db_session() as db:
        audits = AuditRepository.get_audits(db, limit=limit)
        return {
            "audits": [
                {
                    "id": a.id,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "project_name": a.project_name,
                    "audit_type": a.audit_type,
                    "tech_spec_filename": getattr(a, 'tech_spec_filename', None),
                    "risk_level": a.risk_level,
                    "composite_risk_score": a.composite_risk_score,
                    "status": getattr(a, 'status', 'completed')
                }
                for a in audits
            ]
        }


@app.get("/api/v1/audits/statistics", tags=["History"])
async def get_audit_statistics():
    """
    Get aggregate statistics for dashboard.
    """
    with get_db_session() as db:
        stats = AuditRepository.get_statistics(db)

        return {
            "status": "success",
            "statistics": stats
        }


@app.get("/api/v1/audits/{audit_id}", tags=["History"])
async def get_audit_detail(audit_id: str):
    """
    Get detailed audit record by ID.
    """
    with get_db_session() as db:
        audit = AuditRepository.get_audit_by_id(db, audit_id)

        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")

        return {
            "status": "success",
            "audit": {
                "id": audit.id,
                "created_at": audit.created_at.isoformat() if audit.created_at else None,
                "audit_type": audit.audit_type,
                "project_name": audit.project_name,
                "tech_gaps": audit.tech_gaps,
                "proposal_risks": audit.proposal_risks,
                "contradictions": audit.contradictions,
                "patch_pack": audit.patch_pack,
                "ambiguity_score": audit.ambiguity_score,
                "leverage_score": audit.leverage_score,
                "composite_risk_score": audit.composite_risk_score,
                "risk_level": audit.risk_level
            }
        }


# Legacy audit detail endpoint (for frontend compatibility)
@app.get("/audits/{audit_id}", tags=["History (Legacy)"], deprecated=True)
async def get_audit_legacy(audit_id: str):
    """Legacy endpoint - use /api/v1/audits/{audit_id} instead"""
    with get_db_session() as db:
        audit = AuditRepository.get_audit_by_id(db, audit_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")
        return {
            "id": audit.id,
            "created_at": audit.created_at.isoformat() if audit.created_at else None,
            "project_name": audit.project_name,
            "audit_type": audit.audit_type,
            "tech_spec_filename": getattr(audit, 'tech_spec_filename', None),
            "risk_level": audit.risk_level,
            "composite_risk_score": audit.composite_risk_score,
            "status": getattr(audit, 'status', 'completed'),
            "patch_pack": audit.patch_pack,
            "tech_gaps": audit.tech_gaps,
            "proposal_risks": audit.proposal_risks,
            "contradictions": audit.contradictions
        }

