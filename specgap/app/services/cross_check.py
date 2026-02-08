"""
Cross-Check Engine - Orchestrator Agent
Synthesizes findings from Tech and Legal agents into actionable outputs.
"""

import json
import asyncio
from typing import Dict, Any, Optional

from app.core.config import model_vision, model_text, settings
from app.core.logging import get_logger
from app.core.exceptions import AIModelError, AIResponseParseError
from app.services.safe_parse import safe_parse_llm_response
from app.services.sanitizer import wrap_as_document_context

logger = get_logger("cross_check")


ORCHESTRATOR_PROMPT = """
Role: You are SpecGap, the Chief Technology & Legal Officer (The Orchestrator).

Task: Validate and Synthesize the findings from your sub-agents (Tech Auditor & Legal Negotiator).

Inputs:
1. Technical Spec (The Reality) - What the system should do
2. Business Proposal (The Promise) - What the vendor is offering
3. Tech Auditor Report - Gaps found by engineering
4. Legal Negotiator Report - Risks found by legal

Goals:
1. VERIFY: Do the Legal Risks exacerbate the Tech Gaps?
   - Example: "Missing SLA" (legal) + "No Monitoring" (tech) = Critical Failure
2. CONTRADICTIONS: Find where documents disagree
3. STRATEGIC SYNTHESIS: Executive summary of deal quality
4. ACTION ITEMS: Generate JIRA tickets and negotiation email

Output Requirements (JSON ONLY - no markdown):
{
    "contradictions": [
        {
            "topic": "Subject of contradiction",
            "document_a_says": "What first document states",
            "document_b_says": "What second document states",
            "impact": "Business impact of this contradiction"
        }
    ],
    "strategic_synthesis": "Executive summary (2-3 paragraphs) explaining overall deal quality",
    "reality_diagram_mermaid": "graph TD\\n    A[Start] --> B[Process]\\n    B --> C[End]",
    "patch_pack": {
        "jira_tickets": [
            {
                "title": "Ticket title",
                "description": "What needs to be done",
                "priority": "High/Medium/Low",
                "labels": ["tech-gap", "legal-risk"],
                "acceptance_criteria": "Definition of done"
            }
        ],
        "negotiation_email": "Pre-written email to vendor incorporating all findings"
    }
}
"""


def _clean_json_response(text: str) -> str:
    """Clean AI response to extract valid JSON"""
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1

    if start != -1 and end > start:
        cleaned = cleaned[start:end]

    return cleaned


async def run_cross_check(
    tech_text: str,
    proposal_text: str,
    diagram_data: Optional[dict] = None,
    tech_report: Optional[dict] = None,
    legal_report: Optional[dict] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Cross-check and synthesize all analysis results.

    Args:
        tech_text: Technical specification text
        proposal_text: Business proposal text
        diagram_data: Optional architecture diagram for vision analysis
        tech_report: Results from tech_engine
        legal_report: Results from biz_engine
        max_retries: Number of retry attempts

    Returns:
        Synthesized report with contradictions, synthesis, and action items
    """
    logger.info("Starting cross-check synthesis")

    # Build prompt parts
    prompt_parts = [ORCHESTRATOR_PROMPT]

    max_doc_chars = settings.MAX_CONTEXT_CHARS // 2
    prompt_parts.append(wrap_as_document_context(tech_text[:max_doc_chars], label="TECH SPEC"))
    prompt_parts.append(wrap_as_document_context(proposal_text[:max_doc_chars], label="PROPOSAL"))

    # Add prior agent findings
    if tech_report:
        tech_summary = json.dumps(tech_report, indent=2)[:10000]
        prompt_parts.append(f"\n--- PRIOR AGENT FINDINGS: TECH AUDIT ---\n{tech_summary}")
        logger.debug(f"Added tech report ({len(tech_summary)} chars)")

    if legal_report:
        legal_summary = json.dumps(legal_report, indent=2)[:10000]
        prompt_parts.append(f"\n--- PRIOR AGENT FINDINGS: LEGAL AUDIT ---\n{legal_summary}")
        logger.debug(f"Added legal report ({len(legal_summary)} chars)")

    # Add diagram if present (for vision model)
    if diagram_data:
        prompt_parts.append("--- ARCHITECTURE DIAGRAM (See Attached Image) ---")
        prompt_parts.append(diagram_data)
        logger.debug("Added architecture diagram")

    prompt_parts.append("\nGenerate the Synthesized JSON Report now.")

    last_error = None
    for attempt in range(max_retries):
        try:
            delay = settings.AI_REQUEST_DELAY * (attempt + 1)
            logger.debug(f"Cross-check attempt {attempt + 1}, delay {delay}s")
            await asyncio.sleep(delay)

            response = await model_vision.generate_content_async(prompt_parts)

            if not response or not response.text:
                raise AIModelError(
                    model=settings.GEMINI_MODEL_VISION,
                    details="Empty response"
                )

            result = safe_parse_llm_response(
                response.text,
                expected_keys=["contradictions", "strategic_synthesis"]
            )

            if result.get("parse_error"):
                last_error = AIResponseParseError(agent="cross_check", raw_response=response.text)
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {result.get('error_message')}")
                continue  # Retry with next attempt

            # Validate and set defaults
            if "contradictions" not in result:
                result["contradictions"] = []
            if "strategic_synthesis" not in result:
                result["strategic_synthesis"] = "Analysis synthesis unavailable"
            if "patch_pack" not in result:
                result["patch_pack"] = {"jira_tickets": [], "negotiation_email": ""}

            contradiction_count = len(result.get("contradictions", []))
            ticket_count = len(result.get("patch_pack", {}).get("jira_tickets", []))

            logger.info(
                f"Cross-check complete: {contradiction_count} contradictions, "
                f"{ticket_count} JIRA tickets generated"
            )

            return result

        except Exception as e:
            last_error = e
            logger.warning(f"Cross-check attempt {attempt + 1} failed: {e}")

            if "quota" in str(e).lower() or "rate" in str(e).lower():
                await asyncio.sleep(30)

    logger.error(f"Cross-check failed after {max_retries} attempts")
    return {
        "error": "Cross-check failed",
        "details": str(last_error),
        "contradictions": [],
        "strategic_synthesis": "Analysis failed - please retry",
        "patch_pack": {"jira_tickets": [], "negotiation_email": ""}
    }



SINGLE_DOC_PROMPT = """
Role: You are SpecGap, the Chief Technology & Legal Officer (The Orchestrator).

IMPORTANT: Only ONE document was provided. Perform a SELF-CONSISTENCY AUDIT
instead of a cross-document comparison.

Analyze this single document for:
1. **Internal contradictions** — places where the document says conflicting things
2. **Ambiguous terms** — vague language that could be interpreted multiple ways
3. **Missing sections** — expected sections for a {doc_type}: {expected_sections}
4. **Unrealistic commitments** — promises that seem infeasible
5. **Undefined references** — terms, systems, or acronyms mentioned but never defined

For EACH finding, provide a source reference (quote exact text).

Output Requirements (JSON ONLY - no markdown):
{{
    "analysis_mode": "single_document",
    "contradictions": [
        {{
            "topic": "Subject of the internal contradiction",
            "document_a_says": "First conflicting statement (exact quote)",
            "document_b_says": "Second conflicting statement (exact quote)",
            "impact": "Business impact of this contradiction"
        }}
    ],
    "ambiguous_terms": [
        {{
            "term": "The ambiguous term or phrase",
            "context": "Where it appears",
            "risk": "How it could be misinterpreted"
        }}
    ],
    "missing_sections": ["Section name 1", "Section name 2"],
    "unrealistic_commitments": [
        {{
            "claim": "The unrealistic promise",
            "why_unrealistic": "Why this is infeasible"
        }}
    ],
    "completeness_score": 0-100,
    "strategic_synthesis": "Executive summary (2-3 paragraphs) of document quality",
    "patch_pack": {{
        "jira_tickets": [
            {{
                "title": "Ticket title",
                "description": "What needs to be done",
                "priority": "High/Medium/Low",
                "labels": ["self-audit"],
                "acceptance_criteria": "Definition of done"
            }}
        ],
        "negotiation_email": "Pre-written email incorporating all findings"
    }}
}}
"""

EXPECTED_SECTIONS = {
    "tech_spec": "requirements, architecture, security, performance, testing, error handling, monitoring",
    "proposal": "scope, pricing, timeline, SLA, deliverables, assumptions, exclusions",
    "contract": "definitions, obligations, payment terms, IP rights, termination, dispute resolution, liability, indemnification",
    "unknown": "scope, requirements, timeline, responsibilities, deliverables, acceptance criteria",
}


async def run_single_doc_audit(
    document_text: str,
    document_type: str = "unknown",
    tech_report: Optional[dict] = None,
    legal_report: Optional[dict] = None,
    max_retries: int = 3
) -> Dict[str, Any]:

    logger.info(f"Starting single-document audit (type={document_type}, {len(document_text):,} chars)")

    expected = EXPECTED_SECTIONS.get(document_type, EXPECTED_SECTIONS["unknown"])
    prompt = SINGLE_DOC_PROMPT.format(doc_type=document_type, expected_sections=expected)

    prompt_parts = [prompt]

    # Add prior agent findings for richer context
    if tech_report and not tech_report.get("error"):
        tech_summary = json.dumps(tech_report, indent=2)[:5000]
        prompt_parts.append(f"\n--- PRIOR FINDINGS: TECH AUDIT ---\n{tech_summary}")

    if legal_report and not legal_report.get("error"):
        legal_summary = json.dumps(legal_report, indent=2)[:5000]
        prompt_parts.append(f"\n--- PRIOR FINDINGS: LEGAL AUDIT ---\n{legal_summary}")

    # Add document with sanitizer wrapping
    max_doc_chars = settings.MAX_CONTEXT_CHARS
    prompt_parts.append(wrap_as_document_context(
        document_text[:max_doc_chars], label="DOCUMENT UNDER REVIEW"
    ))

    prompt_parts.append("\nGenerate the Self-Consistency Audit JSON Report now.")

    last_error = None
    for attempt in range(max_retries):
        try:
            delay = settings.AI_REQUEST_DELAY * (attempt + 1)
            logger.debug(f"Single doc audit attempt {attempt + 1}, delay {delay}s")
            await asyncio.sleep(delay)

            response = await model_text.generate_content_async(prompt_parts)

            if not response or not response.text:
                raise AIModelError(
                    model=settings.GEMINI_MODEL_TEXT,
                    details="Empty response"
                )

            result = safe_parse_llm_response(
                response.text,
                expected_keys=["contradictions", "strategic_synthesis"]
            )

            if result.get("parse_error"):
                last_error = AIResponseParseError(agent="single_doc_audit", raw_response=response.text)
                logger.warning(f"Single doc audit parse error on attempt {attempt + 1}")
                continue

            # Ensure consistent output shape
            result["analysis_mode"] = "single_document"
            result.setdefault("contradictions", [])
            result.setdefault("strategic_synthesis", "Single document analysis completed")
            result.setdefault("patch_pack", {"jira_tickets": [], "negotiation_email": ""})
            result.setdefault("completeness_score", None)

            contradiction_count = len(result.get("contradictions", []))
            missing_count = len(result.get("missing_sections", []))
            logger.info(
                f"Single doc audit complete: {contradiction_count} contradictions, "
                f"{missing_count} missing sections"
            )
            return result

        except Exception as e:
            last_error = e
            logger.warning(f"Single doc audit attempt {attempt + 1} failed: {e}")
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                await asyncio.sleep(30)

    logger.error(f"Single doc audit failed after {max_retries} attempts")
    return {
        "error": "Single document audit failed",
        "details": str(last_error),
        "analysis_mode": "single_document",
        "contradictions": [],
        "strategic_synthesis": "Analysis failed - please retry",
        "patch_pack": {"jira_tickets": [], "negotiation_email": ""}
    }



def _classify_by_filename(filename: str) -> str:
    """Simple filename-based document type classification."""
    fname = filename.lower()
    if any(k in fname for k in ["contract", "agreement", "license", "msa", "nda"]):
        return "contract"
    elif any(k in fname for k in ["proposal", "sow", "statement", "bid", "quote"]):
        return "proposal"
    elif any(k in fname for k in ["spec", "tech", "requirement", "architecture", "design"]):
        return "tech_spec"
    return "unknown"


async def run_smart_comparison(
    file_texts: Dict[str, str],
    tech_report: Optional[dict] = None,
    legal_report: Optional[dict] = None,
    diagram_data: Optional[dict] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
   
    if not file_texts:
        logger.warning("No documents provided for comparison")
        return {
            "error": "No documents provided",
            "analysis_mode": "none",
            "contradictions": [],
            "strategic_synthesis": "No documents were provided for analysis.",
            "patch_pack": {"jira_tickets": [], "negotiation_email": ""}
        }

    # === SINGLE FILE: Self-consistency audit ===
    if len(file_texts) == 1:
        filename = list(file_texts.keys())[0]
        text = list(file_texts.values())[0]
        doc_type = _classify_by_filename(filename)

        logger.info(f"Single file detected ({filename}), running self-audit (type={doc_type})")
        return await run_single_doc_audit(
            document_text=text,
            document_type=doc_type,
            tech_report=tech_report,
            legal_report=legal_report,
            max_retries=max_retries
        )

    # === MULTIPLE FILES: Real cross-document comparison ===
    logger.info(f"{len(file_texts)} files detected, running cross-document comparison")

    filenames = list(file_texts.keys())
    texts = list(file_texts.values())

    # Default: first file = tech spec, second = proposal
    tech_text = texts[0]
    proposal_text = texts[1]

    # Try to classify which is which based on filename
    for fname, text in file_texts.items():
        doc_type = _classify_by_filename(fname)
        if doc_type == "tech_spec":
            tech_text = text
        elif doc_type in ("proposal", "contract"):
            proposal_text = text

    return await run_cross_check(
        tech_text=tech_text,
        proposal_text=proposal_text,
        diagram_data=diagram_data,
        tech_report=tech_report,
        legal_report=legal_report,
        max_retries=max_retries
    )
