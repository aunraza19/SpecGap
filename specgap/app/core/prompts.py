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
"""
Council Prompts for SpecGap
Defines personas and prompt templates for the 3-round deliberation.
"""

COUNCIL_PERSONAS = {
    "legal": {
        "role": "Corporate General Counsel",
        "focus": "Liability, IP ownership, termination rights, indemnification, and contract traps.",
        "perspective": "Risk-averse, protecting the client from legal exposure"
    },
    "business": {
        "role": "Chief Operating Officer (COO)",
        "focus": "Operational viability, feature completeness vs. promise, timeline realism, and deliverable clarity.",
        "perspective": "Execution-focused, ensuring promises can be kept"
    },
    "finance": {
        "role": "CFO & Audit Partner",
        "focus": "Hidden costs, payment terms, ROI projections, financial risk, and budget overruns.",
        "perspective": "Cost-conscious, maximizing value and minimizing financial exposure"
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
You are acting as: {role}
Domain Context: {domain}

TASK: Perform an initial independent analysis of the provided documents.
Focus on your area of expertise and identify ALL potential issues.

ANALYSIS REQUIREMENTS:
1. Identify specific risks/gaps related to your role
2. For EACH finding, provide:
   - Clear description of the issue
   - Severity (Critical/High/Medium/Low)
   - Source reference (quote the exact text)
   - Why this matters
3. Be thorough - assume other agents may miss things you catch

OUTPUT FORMAT (JSON):
{{
    "agent": "{role}",
    "findings": [
        {{
            "issue": "Description of the problem",
            "severity": "High",
            "source_quote": "Exact text from document",
            "impact": "Why this is a problem",
            "category": "liability/cost/timeline/etc"
        }}
    ],
    "overall_assessment": "Brief summary of document quality from your perspective"
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
You are acting as: {role}
Domain Context: {domain}

TASK: Review your initial findings against your peers' analyses.
Cross-validate, challenge assumptions, and refine your assessment.

YOUR PREVIOUS ANALYSIS:
{current_draft}

PEER ANALYSES:
{peer_drafts}

INSTRUCTIONS:
1. VALIDATE: Did peers find issues you missed? Verify and adopt if legitimate.
2. CHALLENGE: Do you disagree with any peer findings? Explain why.
3. SYNTHESIZE: How do findings from different perspectives compound risk?
4. REFINE: Update your assessment based on the combined view.

OUTPUT FORMAT (JSON):
{{
    "agent": "{role}",
    "validated_from_peers": [
        {{
            "finding": "Issue adopted from peer",
            "peer_source": "legal/business/finance",
            "your_perspective": "Why you agree"
        }}
    ],
    "disputed_findings": [
        {{
            "finding": "Issue you disagree with",
            "peer_source": "legal/business/finance", 
            "your_counterargument": "Why you disagree"
        }}
    ],
    "compounded_risks": [
        {{
            "combined_issue": "Risk that spans multiple domains",
            "contributing_factors": ["factor1", "factor2"],
            "combined_severity": "Critical"
        }}
    ],
    "refined_assessment": "Updated overall view"
}}
""",

    "ROUND_3": """
You are acting as: {role}
Domain Context: {domain}

TASK: Generate ACTIONABLE FLASHCARDS for the end user.
Convert your refined analysis into binary decisions (Accept Fix / Ignore).

YOUR REFINED ANALYSIS:
{current_draft}

PEER FINAL INSIGHTS:
{peer_drafts}

FLASHCARD REQUIREMENTS:
1. Each flashcard = ONE specific, actionable fix
2. Title must be scannable (5-8 words max)
3. Description explains the risk in plain English (2 sentences)
4. fix_action is what the user is agreeing to do
5. swipe_right_payload is the EXACT text/clause to add if accepted

SEVERITY GUIDE:
- Critical: Deal-breaker, must fix before signing
- High: Significant risk, strongly recommend fixing
- Medium: Notable issue, should consider fixing
- Low: Minor improvement, nice to have

CRITICAL: Output ONLY valid JSON. No markdown, no explanations.

REQUIRED OUTPUT FORMAT:
{{
    "flashcards": [
        {{
            "id": "{role}_1",
            "card_type": "Risk",
            "title": "Short Headline (5-8 words)",
            "description": "2 sentence explanation of the issue and its impact.",
            "fix_action": "What accepting this fix means (e.g., 'Add Liability Cap')",
            "severity": "High",
            "swipe_right_payload": "The exact contractual/technical text to be added if user accepts. Be specific and actionable."
        }},
        {{
            "id": "{role}_2",
            "card_type": "Gap",
            "title": "Another Clear Headline",
            "description": "Explanation of what's missing and why it matters.",
            "fix_action": "Specific action to take",
            "severity": "Medium",
            "swipe_right_payload": "Exact specification text or requirement to add."
        }}
    ]
}}

Generate 3-5 flashcards based on your most important findings.
"""
}


# Additional prompt templates for specific use cases

DOCUMENT_COMPARISON_PROMPT = """
Compare the following two documents and identify:
1. Requirements in Document A not addressed in Document B
2. Promises in Document B that exceed Document A's scope
3. Contradictions between the documents
4. Ambiguous terms that could be interpreted differently

Document A (Requirements/Spec):
{doc_a}

Document B (Proposal/Contract):
{doc_b}

Output as JSON with categories: missing_requirements, scope_creep, contradictions, ambiguities
"""

EXECUTIVE_SUMMARY_PROMPT = """
Generate an executive summary for a C-level audience based on these findings:

Tech Gaps: {tech_summary}
Legal Risks: {legal_summary}  
Financial Concerns: {finance_summary}

Requirements:
1. Maximum 3 paragraphs
2. Lead with the most critical issue
3. Include a clear recommendation (proceed/negotiate/reject)
4. Quantify risk where possible (e.g., "3 critical gaps", "$X exposure")
"""
