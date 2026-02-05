import json
from app.core.config import model_vision

async def run_cross_check(
    tech_text: str, 
    proposal_text: str, 
    diagram_data: dict = None,
    tech_report: dict = None,
    legal_report: dict = None
):
   
    
    system_instruction = """
    Role: You are SpecGap, the Chief Technology & Legal Officer (The Orchestrator).
    
    Task: Validate and Synthesize the findings from your sub-agents (Tech Auditor & Legal Negotiator).
    
    Inputs:
    1. Technical Spec (The Reality).
    2. Business Proposal (The Promise).
    3. Tech Auditor Report (Gaps found by engineering).
    4. Legal Negotiator Report (Risks found by legal).
    
    Goal:
    1. VERIFY: Do the Legal Risks exacerbate the Tech Gaps? (e.g. "Missing SLA" + "No Refund Clause" = Critical Failure).
    2. VISUALIZE: Compare the text to the diagram.
    3. ACTION: Generate the final "Patch Pack".
    
    Output Requirements (JSON):
    1. CONTRADICTIONS: List where documents disagree.
    2. STRATEGIC_SYNTHESIS: A high-level summary of why this deal is good/bad based on the COMBINED Tech+Legal view.
    3. REALITY_DIAGRAM_MERMAID: Generate strictly valid Mermaid.js code (graph TD).
    4. PATCH_PACK: 
       - "jira_tickets": List of tickets to fix tech gaps.
       - "negotiation_email": A pre-written email to the vendor incorporating the Legal Redlines and Tech Gaps.
    """
    prompt_parts = [system_instruction]
    
    prompt_parts.append(f"\n--- TECH SPEC ---\n{tech_text[:40000]}") 
    prompt_parts.append(f"\n--- PROPOSAL ---\n{proposal_text[:40000]}")
    
    if tech_report:
        prompt_parts.append(f"\n--- PRIOR AGENT FINDINGS: TECH AUDIT ---\n{json.dumps(tech_report)}")
    if legal_report:
        prompt_parts.append(f"\n--- PRIOR AGENT FINDINGS: LEGAL AUDIT ---\n{json.dumps(legal_report)}")
    
    if diagram_data:
        prompt_parts.append("--- ARCHITECTURE DIAGRAM (See Attached Image) ---")
        prompt_parts.append(diagram_data) 
        
    prompt_parts.append("\nGenerate the Synthesized JSON Report now.")

    try:
        response = await model_vision.generate_content_async(prompt_parts)
        
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return json.loads(cleaned_text)

    except Exception as e:
        return {"error": "Cross-check failed", "details": str(e)}