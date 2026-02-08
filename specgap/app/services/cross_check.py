"""
Cross-Check Engine - Orchestrator Agent
Synthesizes findings from Tech and Legal agents into actionable outputs.
"""

import json
import asyncio
from typing import Optional, Dict, Any, Union, List
from app.core.config import model_vision
from datetime import datetime

# -----------------------------
# Helper Functions
# -----------------------------

def chunk_text(text: str, max_len: int = 40000) -> List[str]:
    """Split large text into manageable chunks."""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

def validate_diagram(diagram: Union[str, Dict[str, Any]]) -> str:
    """Ensure diagram is a string for prompt inclusion."""
    if isinstance(diagram, dict):
        return json.dumps(diagram, indent=2)
    return str(diagram)

def extract_patch_pack(result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract jira tickets and negotiation email from Orchestrator output."""
    patch = result.get("PATCH_PACK", {})
    return {
        "jira_tickets": patch.get("jira_tickets", []),
        "negotiation_email": patch.get("negotiation_email", "")
    }

def validate_json(raw_text: str) -> Dict[str, Any]:
    """Safely parse JSON from model output."""
    try:
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw_response": raw_text}

def log_step(step: str):
    """Simple timestamped logging."""
    print(f"[{datetime.now().isoformat()}] {step}")

# -----------------------------
# Main Orchestrator Function
# -----------------------------
from typing import Dict, Any, Optional

from app.core.config import model_vision, settings
from app.core.logging import get_logger
from app.core.exceptions import AIModelError, AIResponseParseError

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
    diagram_data: Optional[Union[str, Dict[str, Any]]] = None,
    tech_report: Optional[Dict[str, Any]] = None,
    legal_report: Optional[Dict[str, Any]] = None,
    max_text_length: int = 40000,
    retries: int = 2
) -> Dict[str, Any]:
    """
    Orchestrator agent: Validates and synthesizes outputs from Tech & Legal agents.
    Supports chunking, retries, logging, and safe JSON parsing.
    """

    log_step("Preparing system instructions and input text")
    system_instruction = """
    Role: You are SpecGap, the Chief Technology & Legal Officer (The Orchestrator).

    Task: Validate and Synthesize findings from Tech Auditor & Legal Negotiator.

    Goal:
    1. VERIFY contradictions and interactions.
    2. VISUALIZE architecture via Mermaid diagram.
    3. ACTION: Generate final Patch Pack (Jira + negotiation email).

    Output strictly as JSON:
    - CONTRADICTIONS
    - STRATEGIC_SYNTHESIS
    - REALITY_DIAGRAM_MERMAID
    - PATCH_PACK
    """

    # Prepare text chunks
    tech_chunks = chunk_text(tech_text, max_text_length)
    proposal_chunks = chunk_text(proposal_text, max_text_length)
    diagram_str = validate_diagram(diagram_data) if diagram_data else None

    prompt_parts = [system_instruction]

    for i, (tech_chunk, proposal_chunk) in enumerate(zip(tech_chunks, proposal_chunks)):
        log_step(f"Adding chunk {i+1} to prompt")
        prompt_parts.append(f"\n--- TECH SPEC (chunk {i+1}) ---\n{tech_chunk}")
        prompt_parts.append(f"\n--- PROPOSAL (chunk {i+1}) ---\n{proposal_chunk}")

    if tech_report:
        prompt_parts.append(f"\n--- PRIOR TECH AUDIT ---\n{json.dumps(tech_report, indent=2)}")
    if legal_report:
        prompt_parts.append(f"\n--- PRIOR LEGAL AUDIT ---\n{json.dumps(legal_report, indent=2)}")
    if diagram_str:
        prompt_parts.append(f"\n--- ARCHITECTURE DIAGRAM ---\n{diagram_str}")

    prompt_parts.append("\nGenerate the Synthesized JSON Report now.")

    # Retry loop
    attempt = 0
    while attempt <= retries:
        try:
            log_step(f"Calling model_vision (attempt {attempt+1})")
            response = await model_vision.generate_content_async(prompt_parts)
            result = validate_json(response.text.strip())
            log_step("Cross-check successful")
            return result
        except Exception as e:
            log_step(f"Attempt {attempt+1} failed: {e}")
            attempt += 1
    return {"error": "Cross-check failed after retries"}

# -----------------------------
# Optional Convenience Function
# -----------------------------
async def run_and_extract_patch_pack(*args, **kwargs) -> Dict[str, Any]:
    """
    Run cross-check and directly return the Patch Pack (jira + email)
    """
    result = await run_cross_check(*args, **kwargs)
    return extract_patch_pack(result)
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

    # Add document context (truncated)
    max_doc_chars = settings.MAX_CONTEXT_CHARS // 2
    prompt_parts.append(f"\n--- TECH SPEC ---\n{tech_text[:max_doc_chars]}")
    prompt_parts.append(f"\n--- PROPOSAL ---\n{proposal_text[:max_doc_chars]}")

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

            cleaned = _clean_json_response(response.text)
            result = json.loads(cleaned)

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

        except json.JSONDecodeError as e:
            last_error = AIResponseParseError(agent="cross_check", raw_response=response.text if response else None)
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")

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
