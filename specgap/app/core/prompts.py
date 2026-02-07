COUNCIL_PERSONAS = {
    "legal": {
        "role": "Corporate General Counsel",
        "focus": "Liability, IP, termination, hidden contract traps",
    },
    "business": {
        "role": "Chief Operating Officer (COO)",
        "focus": "Feature completeness, operational viability, timeline realism",
    },
    "finance": {
        "role": "CFO & Audit Partner",
        "focus": "Costs, payment terms, ROI, financial risks",
    }
}

PROMPT_TEMPLATES = {
    "ROUND_1": """
Role: {role}
Domain: {domain}
Task: Identify Risks/Gaps in the provided documents (Contract + Tech Spec).
Focus: {focus}
Output: JSON only
Instructions:
- Cite exact text for every finding.
- Classify gaps as Critical / High / Medium / Low
- Optional: Include "suggested_fix" if obvious.
Format:
{{
  "findings": [
    {{
      "title": "...",
      "description": "...",
      "severity": "Critical|High|Medium|Low",
      "source": "File Name / Section",
      "suggested_fix": "..."
    }}
  ]
}}
""",

    "ROUND_2": """
Role: {role}
Domain: {domain}
Task: Update your findings using peer feedback.
[Your Draft]: {current_draft}
[Peers Drafts]: {peer_drafts}
Output: JSON only
Instructions:
- Merge missing findings from peers
- Resolve contradictions: keep the one with higher severity
- Retain source references
Format same as ROUND_1
""",

    "ROUND_3": """
Role: {role}
Domain: {domain}
Task: Convert findings into actionable Flashcards.
[Analysis]: {current_draft}
[Peer Insights]: {peer_drafts}
Output: JSON only
Instructions:
- Max 3-5 flashcards per persona
- Provide:
    - id: unique identifier
    - card_type: "Risk" | "Opportunity"
    - title: short headline
    - description: concise explanation (1-2 sentences)
    - fix_action: what user should do
    - severity: Critical / High / Medium / Low
    - impact: High / Medium / Low (for prioritization)
    - swipe_right_payload: exact text/action if user accepts
- Do not add extra text or commentary
Format:
{{
  "flashcards": [
    {{
      "id": "...",
      "card_type": "...",
      "title": "...",
      "description": "...",
      "fix_action": "...",
      "severity": "...",
      "impact": "...",
      "swipe_right_payload": "..."
    }}
  ]
}}
"""
}
