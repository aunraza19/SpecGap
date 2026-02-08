"""
Robust JSON Extraction from LLM Responses (Test Case 2)
Handles markdown fences, partial JSON, and common LLM formatting quirks.

Problem: Gemini sometimes returns JSON wrapped in ```json blocks, with trailing
commas, preamble text, or malformed structures. A single json.loads() call fails
and the entire analysis is lost.

Solution: Multi-strategy extraction with repair attempts, always returning a
consistent dict shape so downstream code never crashes.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union

from app.core.logging import get_logger

logger = get_logger("safe_parse")


def extract_json(raw: str) -> Optional[Union[Dict, List]]:
    """
    Extract JSON from an LLM response using multiple strategies.

    Strategies (in order):
    1. Direct json.loads()
    2. Extract from ```json ... ``` markdown fences
    3. Find outermost { } or [ ] boundaries
    4. Repair common issues (trailing commas, single quotes) and retry

    Args:
        raw: Raw LLM response text

    Returns:
        Parsed JSON as dict or list, or None if all strategies fail
    """
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code fences
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    matches = re.findall(fence_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Strategy 3: Find outermost JSON boundaries
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx:end_idx + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Strategy 4: Repair and retry
                fixed = _repair_json(candidate)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    continue

    return None


def _repair_json(text: str) -> str:
    """
    Attempt to fix common JSON issues from LLMs:
    - Trailing commas before } or ]
    - Single quotes instead of double quotes
    - Unescaped newlines inside string values
    """
    # Remove trailing commas before closing brackets
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Fix single-quoted keys/values only if double quotes are absent
    if '"' not in text and "'" in text:
        text = text.replace("'", '"')

    # Remove control characters inside strings (common in OCR'd docs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    return text


def safe_parse_llm_response(
    raw: str,
    fallback_key: str = "raw_response",
    expected_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Parse an LLM response into a dict with guaranteed consistent shape.

    If parsing fails, returns a dict with 'parse_error': True so downstream
    code can detect the failure and retry or handle gracefully.

    Args:
        raw: Raw LLM response text
        fallback_key: Key name for storing unparseable text
        expected_keys: If provided, warns about missing keys in parsed result

    Returns:
        Always returns a dict. Check 'parse_error' key to detect failures.
        On success: the parsed JSON dict
        On failure: {"parse_error": True, "error_message": "...", fallback_key: "raw text"}
    """
    if not raw:
        return {
            "parse_error": True,
            "error_message": "Empty LLM response",
            fallback_key: "",
        }

    parsed = extract_json(raw)

    if parsed is None:
        logger.warning(f"Failed to extract JSON from response ({len(raw)} chars)")
        return {
            "parse_error": True,
            "error_message": "Failed to extract valid JSON from LLM response",
            fallback_key: raw[:2000],  # Truncate to prevent huge payloads
        }

    # If the result is a list, wrap it in a dict for consistent shape
    if isinstance(parsed, list):
        return {"items": parsed}

    # Validate expected keys exist
    if expected_keys and isinstance(parsed, dict):
        missing = [k for k in expected_keys if k not in parsed]
        if missing:
            parsed["parse_warning"] = f"Missing expected keys: {missing}"
            logger.warning(f"Parsed JSON missing keys: {missing}")

    return parsed
