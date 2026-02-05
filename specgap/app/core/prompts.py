

COUNCIL_PERSONAS = {
    "legal": {
        "role": "Corporate General Counsel",
        "focus": "Liability, IP ownership, termination rights, and contract traps.",
    },
    "business": {
        "role": "Chief Operating Officer (COO)",
        "focus": "Operational viability, feature completeness vs. promise, and timeline realism.",
    },
    "finance": {
        "role": "CFO & Audit Partner",
        "focus": "Hidden costs, payment terms, ROI, and financial risk.",
    }
}

PROMPT_TEMPLATES = {
    "ROUND_1": """
    Role: You are {role}. 
    Domain: {domain}
    Task: Analyze the provided documents (Contract + Tech Spec).
    Output: A list of initial findings (Risks/Gaps).
    Format: JSON.
    """,
    
    "ROUND_2": """
    Role: You are {role}.
    Domain: {domain}
    Task: Review your initial findings against the opinions of your peers.
    
    [YOUR PREVIOUS DRAFT]:
    {current_draft}
    
    [PEER FEEDBACK]:
    {peer_drafts}
    
    Instruction: 
    - If a peer found a risk you missed, verify it and add it.
    - If a peer contradicts you, debate it (or refine your stance).
    Output: Updated Draft 2.
    """,
    
    "ROUND_3": """
    Role: You are {role}.
    Domain: {domain}
    Task: Finalize your "Flashcards" for the user based on your analysis.
    
    [YOUR ANALYSIS FROM PREVIOUS ROUNDS]:
    {current_draft}
    
    [PEER INSIGHTS]:
    {peer_drafts}
    
    Instruction: Convert your findings into binary choices for the user (Swipe Right to Fix, Left to Ignore).
    Based on the documents and your peer discussions, create 3-5 actionable flashcards.
    
    CRITICAL: You MUST output ONLY valid JSON. No explanations, no markdown, just the JSON object.
    
    REQUIRED OUTPUT FORMAT:
    {{
        "flashcards": [
            {{
                "id": "unique_id_1",
                "card_type": "Risk",
                "title": "Short Headline",
                "description": "2 sentence explanation of the issue.",
                "fix_action": "Add Liability Cap",
                "severity": "High",
                "swipe_right_payload": "The exact text/clause to be added to the document if the user accepts this fix."
            }}
        ]
    }}
    """
}