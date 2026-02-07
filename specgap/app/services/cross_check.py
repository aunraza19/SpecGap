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
