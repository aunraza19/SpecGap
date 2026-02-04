import json
from app.core.config import model_text

async def analyze_proposal_leverage(proposal_text: str):

    system_prompt = """
    Role: You are SpecGap, a cynical and ruthless Corporate Lawyer (The 'Auto-Negotiator').
    Task: Audit the attached documents (Proposals, Contracts, Requirements).
    
    NOTE: The input may contain MULTIPLE documents separated by '=== SOURCE DOCUMENT: [Name] ==='.
    
    Analysis Goals:
    1. CROSS-CHECK: Does the Proposal (File B) actually meet the Requirements (File A)?
    2. LEVERAGE SCORE: Calculate a score from 0 to 100.
    3. TRAP DETECTION: Find clauses that look standard but are dangerous.
    4. AGENTIC REDLINING: For every major risk, generate the ACTUAL legal text to fix it.
    
    Output Format (JSON ONLY):
    {
        "leverage_score": Integer (0-100),
        "favor_direction": "Vendor" or "Client" or "Neutral",
        "trap_clauses": [
            {
                "clause_snippet": "Quote text (Identify Source File)",
                "risk_explanation": "Why this is dangerous",
                "severity": "High/Critical",
                "redline_suggestion": {
                    "original_text": "...",
                    "proposed_text": "...",
                    "negotiation_argument": "..."
                }
            }
        ],
        "negotiation_tips": ["..."]
    }
    """

    full_prompt = f"{system_prompt}\n\n--- BUSINESS PROPOSAL TEXT ---\n{proposal_text}"

    try:
        response = await model_text.generate_content_async(full_prompt)
        
        # Clean JSON output
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return json.loads(cleaned_text)
        
    except Exception as e:
        return {"error": "Failed to analyze proposal", "details": str(e)}   