"""
Tech Engine - Senior Architect Agent
Performs absence detection and consistency checking on technical specifications.
"""

import json
import asyncio
from typing import Dict, Any

from app.core.config import model_text, settings
from app.core.logging import get_logger
from app.core.exceptions import AIModelError, AIResponseParseError

logger = get_logger("tech_engine")


TECH_SYSTEM_PROMPT = """
Role: You are SpecGap, a Senior Principal Software Architect.
Task: Perform 'ABSENCE DETECTION' and 'CONSISTENCY CHECK' on the provided documents.

NOTE: The input may contain MULTIPLE documents (e.g., Requirements and Proposals), 
separated by '=== SOURCE DOCUMENT: [Name] ==='.

Instructions:
1. CROSS-REFERENCE: If File A (Requirements) asks for a feature, check if File B (Proposal) implements it.
2. Analyze the text for mentioned features that lack defined logic.
   (e.g., If 'Auth' is mentioned but no 'Token Expiry' or 'OAuth provider' is defined, flag it).
3. Look for 'Happy Path Bias' (where only success scenarios are described, but error states are missing).
4. Check for missing non-functional requirements (scalability, security, performance, monitoring).

CRITICAL INSTRUCTION: CITATIONS REQUIRED
For every gap found, you MUST provide a "source_reference".
- Quote the exact text from the document.
- Mention which SOURCE FILE the text comes from.

Output Format:
Return ONLY valid JSON. No markdown, no explanations.
{
    "project_name": "String - extracted from documents or 'Unknown'",
    "critical_gaps": [
        {
            "feature": "Name of the feature/component",
            "missing_component": "What is specifically missing",
            "risk_level": "High/Medium/Low",
            "recommendation": "Actionable advice to fix",
            "source_reference": "In 'Proposal.pdf', section X mentions Y but 'Requirements.pdf' demanded Z."
        }
    ],
    "ambiguity_score": 0-100 (0=crystal clear, 100=completely ambiguous)
}
"""


def _clean_json_response(text: str) -> str:
    """Clean AI response to extract valid JSON"""
    cleaned = text.strip()

    # Remove markdown code blocks
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    # Find JSON boundaries
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1

    if start != -1 and end > start:
        cleaned = cleaned[start:end]

    return cleaned


async def analyze_tech_gaps(
    spec_text: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Analyze technical specifications for gaps and ambiguities.

    Args:
        spec_text: Combined document text
        max_retries: Number of retry attempts

    Returns:
        Dictionary with project_name, critical_gaps, and ambiguity_score
    """
    logger.info(f"Starting tech gap analysis ({len(spec_text):,} chars)")

    # Truncate if needed
    max_chars = settings.MAX_CONTEXT_CHARS
    if len(spec_text) > max_chars:
        logger.warning(f"Truncating input from {len(spec_text):,} to {max_chars:,} chars")
        spec_text = spec_text[:max_chars] + "\n\n[...content truncated...]"

    full_prompt = f"{TECH_SYSTEM_PROMPT}\n\n--- TECHNICAL SPECIFICATION ---\n{spec_text}"

    last_error = None
    for attempt in range(max_retries):
        try:
            delay = settings.AI_REQUEST_DELAY * (attempt + 1)
            logger.debug(f"Tech analysis attempt {attempt + 1}, delay {delay}s")
            await asyncio.sleep(delay)

            response = await model_text.generate_content_async(full_prompt)

            if not response or not response.text:
                raise AIModelError(
                    model=settings.GEMINI_MODEL_TEXT,
                    details="Empty response"
                )

            cleaned = _clean_json_response(response.text)
            result = json.loads(cleaned)

            # Validate required fields
            if "critical_gaps" not in result:
                result["critical_gaps"] = []
            if "ambiguity_score" not in result:
                result["ambiguity_score"] = 50

            gap_count = len(result.get("critical_gaps", []))
            logger.info(f"Tech analysis complete: {gap_count} gaps found, ambiguity={result.get('ambiguity_score')}")

            return result

        except json.JSONDecodeError as e:
            last_error = AIResponseParseError(agent="tech_engine", raw_response=response.text if response else None)
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")

        except Exception as e:
            last_error = e
            logger.warning(f"Tech analysis attempt {attempt + 1} failed: {e}")

            if "quota" in str(e).lower() or "rate" in str(e).lower():
                await asyncio.sleep(30)

    logger.error(f"Tech analysis failed after {max_retries} attempts")
    return {
        "error": "Failed to analyze tech spec",
        "details": str(last_error),
        "critical_gaps": [],
        "ambiguity_score": None
    }
