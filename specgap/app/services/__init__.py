"""
SpecGap Services Module
Contains all AI agents and processing logic.
"""

from .workflow import council_app, CouncilState
from .tech_engine import analyze_tech_gaps
from .biz_engine import analyze_proposal_leverage
from .cross_check import run_cross_check
from .patch_pack import build_patch_pack_files
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
    "build_patch_pack_files",

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
