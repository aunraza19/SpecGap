import json
from datetime import datetime
from typing import List, Dict, Any
from app.core.config import model_text

# -----------------------------
# Helper Functions
# -----------------------------

def chunk_text(text: str, max_len: int = 40000) -> List[str]:
    """Split large text into manageable chunks."""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

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
# Main Function
# -----------------------------

async def analyze_tech_gaps(
    spec_text: str,
    max_text_length: int = 40000,
    retries: int = 2
) -> Dict[str, Any]:
    """
    Tech Gap Analysis Agent:
    Detects missing components, consistency errors, and ambiguity in technical specifications.
    Supports chunking, retries, and safe JSON parsing.
    """

    log_step("Preparing system prompt for Tech Gap Analysis")
    system_prompt = """
    Role: You are SpecGap, a Senior Principal Software Architect.
    Task: Perform 'ABSENCE DETECTION' and 'CONSISTENCY CHECK' on the provided documents.

    NOTE: The input may contain MULTIPLE documents (e.g., Requirements and Proposals),
    separated by '=== SOURCE DOCUMENT: [Name] ==='.

    Instructions:
    1. CROSS-REFERENCE: If File A (Requirements) asks for a feature, check if File B (Proposal) implements it.
    2. Analyze the text for mentioned features that lack defined logic.
       (e.g., If 'Auth' is mentioned but no 'Token Expiry' or 'OAuth provider' is defined, flag it).
    3. Look for 'Happy Path Bias' (where only success scenarios are described, but error states are missing).

    CRITICAL INSTRUCTION: CITATIONS REQUIRED
    For every gap found, provide a "source_reference".
    - Quote the exact text from the document.
    - Mention which SOURCE FILE the text comes from.

    Output Format:
    Return ONLY valid JSON.
    {
        "project_name": "String",
        "critical_gaps": [
            {
                "feature": "Name",
                "missing_component": "What is missing",
                "risk_level": "High/Medium/Low",
                "recommendation": "Advice",
                "source_reference": "In 'Proposal.pdf', section 4 mentions X but 'Requirements.pdf' demanded Y."
            }
        ],
        "ambiguity_score": Integer (0-100)
    }
    """

    # 1. Chunk the spec_text if too long
    chunks = chunk_text(spec_text, max_text_length)

    full_prompt = []
    for i, chunk in enumerate(chunks):
        log_step(f"Adding chunk {i+1} to prompt")
        full_prompt.append(f"{system_prompt}\n--- TECHNICAL SPEC (chunk {i+1}) ---\n{chunk}")

    # Retry mechanism
    attempt = 0
    while attempt <= retries:
        try:
            log_step(f"Calling model_text.generate_content_async (attempt {attempt+1})")
            # If multiple chunks, join into one prompt
            combined_prompt = "\n".join(full_prompt) if len(full_prompt) > 1 else full_prompt[0]
            response = await model_text.generate_content_async(combined_prompt)

            log_step("Cleaning and validating JSON output")
            result = validate_json(response.text.strip())
            log_step("Tech Gap Analysis successful")
            return result

        except Exception as e:
            log_step(f"Attempt {attempt+1} failed: {e}")
            attempt += 1

    return {"error": "Tech Gap Analysis failed after retries"}
