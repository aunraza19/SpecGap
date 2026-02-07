"""
Business/Legal Engine - Corporate Lawyer Agent
Analyzes proposals and contracts for leverage, traps, and negotiation opportunities.
"""

import json
import asyncio
from typing import Dict, Any

from app.core.config import model_text, settings
from app.core.logging import get_logger
from app.core.exceptions import AIModelError, AIResponseParseError

logger = get_logger("biz_engine")


LEGAL_SYSTEM_PROMPT = """
Role: You are SpecGap, a cynical and ruthless Corporate Lawyer (The 'Auto-Negotiator').
Task: Audit the attached documents (Proposals, Contracts, Requirements).

NOTE: The input may contain MULTIPLE documents separated by '=== SOURCE DOCUMENT: [Name] ==='.

Analysis Goals:
1. CROSS-CHECK: Does the Proposal (File B) actually meet the Requirements (File A)?
2. LEVERAGE SCORE: Calculate a score from 0 to 100.
   - 0 = Completely favors Client (buyer)
   - 50 = Balanced/Neutral
   - 100 = Completely favors Vendor (seller)
3. TRAP DETECTION: Find clauses that look standard but are dangerous:
   - Auto-renewal with penalty
   - Unlimited liability for client
   - Vague deliverables
   - IP assignment traps
   - Termination penalties
4. AGENTIC REDLINING: For every major risk, generate the ACTUAL legal text to fix it.

Output Format (JSON ONLY - no markdown, no explanations):
{
    "leverage_score": 0-100,
    "favor_direction": "Vendor" or "Client" or "Neutral",
    "trap_clauses": [
        {
            "clause_snippet": "Quote the exact text (identify source file)",
            "risk_explanation": "Why this is dangerous for the client",
            "severity": "High/Medium/Low/Critical",
            "redline_suggestion": {
                "original_text": "The problematic clause",
                "proposed_text": "Your suggested replacement",
                "negotiation_argument": "What to say to the vendor"
            }
        }
    ],
    "negotiation_tips": ["Tip 1", "Tip 2", "..."]
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


async def analyze_proposal_leverage(
    proposal_text: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Analyze proposals/contracts for legal risks and negotiation leverage.

    Args:
        proposal_text: Combined document text
        max_retries: Number of retry attempts

    Returns:
        Dictionary with leverage_score, trap_clauses, and negotiation_tips
    """
    logger.info(f"Starting legal leverage analysis ({len(proposal_text):,} chars)")

    max_chars = settings.MAX_CONTEXT_CHARS
    if len(proposal_text) > max_chars:
        logger.warning(f"Truncating input from {len(proposal_text):,} to {max_chars:,} chars")
        proposal_text = proposal_text[:max_chars] + "\n\n[...content truncated...]"

    full_prompt = f"{LEGAL_SYSTEM_PROMPT}\n\n--- BUSINESS PROPOSAL TEXT ---\n{proposal_text}"

    last_error = None
    for attempt in range(max_retries):
        try:
            delay = settings.AI_REQUEST_DELAY * (attempt + 1)
            logger.debug(f"Legal analysis attempt {attempt + 1}, delay {delay}s")
            await asyncio.sleep(delay)

            response = await model_text.generate_content_async(full_prompt)

            if not response or not response.text:
                raise AIModelError(
                    model=settings.GEMINI_MODEL_TEXT,
                    details="Empty response"
                )

            cleaned = _clean_json_response(response.text)
            result = json.loads(cleaned)

            # Validate and set defaults
            if "leverage_score" not in result:
                result["leverage_score"] = 50
            if "favor_direction" not in result:
                result["favor_direction"] = "Neutral"
            if "trap_clauses" not in result:
                result["trap_clauses"] = []
            if "negotiation_tips" not in result:
                result["negotiation_tips"] = []

            trap_count = len(result.get("trap_clauses", []))
            logger.info(
                f"Legal analysis complete: leverage={result['leverage_score']}, "
                f"direction={result['favor_direction']}, {trap_count} traps found"
            )

            return result

        except json.JSONDecodeError as e:
            last_error = AIResponseParseError(agent="biz_engine", raw_response=response.text if response else None)
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")

        except Exception as e:
            last_error = e
            logger.warning(f"Legal analysis attempt {attempt + 1} failed: {e}")

            if "quota" in str(e).lower() or "rate" in str(e).lower():
                await asyncio.sleep(30)

    logger.error(f"Legal analysis failed after {max_retries} attempts")
    return {
        "error": "Failed to analyze proposal",
        "details": str(last_error),
        "leverage_score": None,
        "favor_direction": None,
        "trap_clauses": [],
        "negotiation_tips": []
    }
