"""
Cross-Check Engine - Orchestrator Agent
Synthesizes findings from Tech and Legal agents into actionable outputs.
"""

import json
import asyncio
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
