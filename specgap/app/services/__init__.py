"""
SpecGap Services Module
Contains all AI agents and processing logic.
"""

from .workflow import council_app, CouncilState
from .tech_engine import analyze_tech_gaps
from .biz_engine import analyze_proposal_leverage
from .cross_check import run_cross_check, run_smart_comparison, run_single_doc_audit
from .patch_pack import build_patch_pack_files
from .safe_parse import safe_parse_llm_response, extract_json
from .sanitizer import sanitize_document_text, wrap_as_document_context
from .chunker import chunk_document, condense_large_document
from .parser import (
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_docx,
    classify_document,
    compute_file_hash,
    smart_chunk_text,
    validate_file,
    encode_image_for_gemini,
)

__all__ = [
    # Workflow
    "council_app",
    "CouncilState",

    # Engines
    "analyze_tech_gaps",
    "analyze_proposal_leverage",
    "run_cross_check",
    "run_smart_comparison",
    "run_single_doc_audit",
    "build_patch_pack_files",

    # Utilities (Test Case fixes)
    "safe_parse_llm_response",
    "extract_json",
    "sanitize_document_text",
    "wrap_as_document_context",
    "chunk_document",
    "condense_large_document",

    # Parser
    "extract_text_from_file",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "classify_document",
    "compute_file_hash",
    "smart_chunk_text",
    "validate_file",
    "encode_image_for_gemini",
]
