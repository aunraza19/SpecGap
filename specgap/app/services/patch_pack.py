from typing import List, Dict, Any
from app.core.config import model_text


def _collect_payloads(cards: List[Dict[str, Any]], agent: str) -> List[str]:
    payloads: List[str] = []
    for card in cards:
        if card.get("source_agent") != agent:
            continue
        payload = card.get("swipe_right_payload") or card.get("fix_action") or card.get("title")
        if payload:
            payloads.append(str(payload).strip())
    return payloads


def _format_contract_addendum(payloads: List[str]) -> str:
    if not payloads:
        return "No legal fixes were selected."
    clauses = [f"Clause {i + 1}: {p}" for i, p in enumerate(payloads)]
    return "\n\n".join(clauses)


def _format_spec_update(payloads: List[str]) -> str:
    if not payloads:
        return "# Spec Updates\n\nNo business requirements were selected."
    lines = [f"- {p}" for p in payloads]
    return "# Spec Updates\n\n" + "\n".join(lines)


async def _generate_negotiation_email(
    domain: str,
    legal_payloads: List[str],
    business_payloads: List[str],
    finance_payloads: List[str]
) -> str:
    summary_points = []
    if legal_payloads:
        summary_points.append("Legal redlines:\n" + "\n".join([f"- {p}" for p in legal_payloads]))
    if business_payloads:
        summary_points.append("Business gaps:\n" + "\n".join([f"- {p}" for p in business_payloads]))
    if finance_payloads:
        summary_points.append("Financial risks:\n" + "\n".join([f"- {p}" for p in finance_payloads]))

    if not summary_points:
        return (
            "Subject: Contract Review Follow-up\n\n"
            "Hi,\n\n"
            "We reviewed the documents but did not select any specific fixes. "
            "Please confirm if you want us to proceed or revise the scope.\n\n"
            "Best,\n"
        )

    prompt = (
        "Role: You are a pragmatic negotiation lead.\n"
        f"Domain: {domain}\n"
        "Task: Draft a concise, professional negotiation email to the vendor.\n"
        "Include a short intro, a bulleted list of requested changes, and a clear next step.\n"
        "Keep it under 220 words.\n\n"
        "Selected Fixes:\n"
        + "\n\n".join(summary_points)
    )

    try:
        response = await model_text.generate_content_async(prompt)
        return response.text.strip()
    except Exception:
        return (
            "Subject: Contract Review Follow-up\n\n"
            "Hi,\n\n"
            "We reviewed the documents and identified a few updates we need before proceeding. "
            "Please see the requested changes below and confirm if you can incorporate them.\n\n"
            + "\n".join([f"- {p}" for p in (legal_payloads + business_payloads + finance_payloads)])
            + "\n\nBest,\n"
        )


async def build_patch_pack_files(
    selected_cards: List[Dict[str, Any]],
    domain: str = "Software Engineering"
) -> Dict[str, str]:
    legal_payloads = _collect_payloads(selected_cards, "legal")
    business_payloads = _collect_payloads(selected_cards, "business")
    finance_payloads = _collect_payloads(selected_cards, "finance")

    contract_addendum = _format_contract_addendum(legal_payloads)
    spec_update = _format_spec_update(business_payloads)
    negotiation_email = await _generate_negotiation_email(
        domain=domain,
        legal_payloads=legal_payloads,
        business_payloads=business_payloads,
        finance_payloads=finance_payloads
    )

    return {
        "Contract_Addendum.txt": contract_addendum,
        "Spec_Update.md": spec_update,
        "Negotiation_Email.txt": negotiation_email
    }
