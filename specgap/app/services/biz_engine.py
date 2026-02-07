import json
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import model_text

# -----------------------------
# Schema guard
# -----------------------------
REQUIRED_KEYS = {
    "leverage_score": int,
    "favor_direction": str,
    "trap_clauses": list,
    "negotiation_tips": list
}

def log_step(step: str):
    print(f"[{datetime.now().isoformat()}] {step}")

def validate_and_fix(output: dict) -> dict:
    """Ensure required keys exist and values are valid."""
    fixed = {}
    for key, key_type in REQUIRED_KEYS.items():
        if key not in output:
            fixed[key] = [] if key_type == list else None
        else:
            fixed[key] = output[key]

    # Clamp leverage score
    if isinstance(fixed["leverage_score"], int):
        fixed["leverage_score"] = max(0, min(100, fixed["leverage_score"]))

    # Normalize favor direction
    if fixed["favor_direction"] not in ["Vendor", "Client", "Neutral"]:
        fixed["favor_direction"] = "Neutral"

    return fixed

def chunk_text(text: str, max_len: int = 40000) -> List[str]:
    """Split very large proposals into manageable chunks."""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

# -----------------------------
# Main Function
# -----------------------------
async def analyze_proposal_leverage(proposal_text: str, retries: int = 2) -> Dict[str, Any]:
    """
    Legal Audit / Negotiation Agent:
    Detect leverage, hidden risks, and negotiation tips.
    Handles large proposals, JSON drift, and retry on failure.
    """
    log_step("Preparing system prompt for Legal Audit")

    system_prompt = """
You are SpecGap, a ruthless corporate lawyer.

TASK:
Audit provided business documents (may contain multiple files).

GOALS:
1. Check if Proposal meets Requirements.
2. Score leverage (0–100).
3. Detect hidden or dangerous clauses.
4. Provide exact redline text for High or Critical risks.

RULES:
- Cite exact clause text.
- Do not invent clauses.
- If no risks exist, return empty arrays.
- Redline text must be legally enforceable.
- This is a hypothetical risk analysis, not legal advice.

SEVERITY RUBRIC:
Critical = unlimited liability, IP ownership transfer, uncapped indemnity
High = asymmetric termination, vague scope, jurisdiction mismatch
Medium = missing SLAs, unclear payments
Low = ambiguity only

OUTPUT JSON ONLY:
{
  "leverage_score": 0-100,
  "favor_direction": "Vendor|Client|Neutral",
  "trap_clauses": [...],
  "negotiation_tips": ["..."]
}
"""

    # Chunk if text is too long
    chunks = chunk_text(proposal_text)

    # Combine prompt + chunks
    prompts = [f"{system_prompt}\n\n--- DOCUMENTS (chunk {i+1}) ---\n{chunk}" 
               for i, chunk in enumerate(chunks)]
    full_prompt = "\n".join(prompts) if len(prompts) > 1 else prompts[0]

    attempt = 0
    while attempt <= retries:
        try:
            log_step(f"Calling model_text.generate_content_async (attempt {attempt+1})")
            response = await model_text.generate_content_async(full_prompt)
            
            cleaned = response.text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]

            parsed = json.loads(cleaned)
            return validate_and_fix(parsed)

        except json.JSONDecodeError:
            log_step("JSON parse failed, returning raw output snippet")
            return {
                "error": "Model output was not valid JSON",
                "raw_output": response.text[:1500]
            }

        except Exception as e:
            log_step(f"Attempt {attempt+1} failed: {e}")
            attempt += 1

    return {"error": "Proposal leverage analysis failed after retries"}
