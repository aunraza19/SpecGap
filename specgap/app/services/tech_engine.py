import json
from app.core.config import model_text

async def analyze_tech_gaps(spec_text: str):
 
    # 1. The System Prompt (The "Senior Engineer" Persona)
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
    For every gap found, you MUST provide a "source_reference".
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

    # 2. The Interaction
    # We combine the prompt + the user's PDF text
    full_prompt = f"{system_prompt}\n\n--- TECHNICAL SPECIFICATION ---\n{spec_text}"

    try:
        response = await model_text.generate_content_async(full_prompt)
        
        # 3. Cleaning the Output (Gemini sometimes adds ```json markers)
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return json.loads(cleaned_text)
        
    except Exception as e:
        return {"error": "Failed to analyze tech spec", "details": str(e)}