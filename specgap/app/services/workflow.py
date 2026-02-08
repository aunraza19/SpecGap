# app/services/workflow.py
"""
Council Workflow - 3-Loop Recursive Consensus System
Uses LangGraph for orchestrating multi-agent deliberation.

Rate Limit Strategy (Multi-API Key):
- Gemini Free Tier: 5 RPM per project/API key
- We have 9 total calls (3 agents × 3 rounds)
- Solution: Use 3 different API keys (one per round)
- Each round makes 3 PARALLEL calls, staying under 5 RPM per key
- Result: Full council session in ~30-40 seconds!

IMPORTANT: genai.configure() is GLOBAL, so we must configure the API key
immediately before each API call, not at model creation time.
"""

from typing import TypedDict, Dict, Any, Optional, List
import asyncio
import json
import time
from langgraph.graph import StateGraph, END

from app.core.config import create_model_for_round, settings
from app.core.prompts import COUNCIL_PERSONAS, PROMPT_TEMPLATES
from app.core.logging import get_logger
from app.core.exceptions import AIModelError, AIResponseParseError, CouncilError

logger = get_logger("workflow")



# --- STATE MANAGEMENT ---
class CouncilState(TypedDict):
    """State object passed through the workflow graph"""
    combined_context: str
    domain: str
    
    # Internal Memory
    round_1_drafts: Dict[str, str]  # { "legal": "...", "finance": "..." }
    round_2_drafts: Dict[str, str]
    round_3_final: Dict[str, Any]
    
    # Final Output
    patch_pack: Dict[str, Any]

    # Error tracking
    errors: Dict[str, str]


async def run_agent_round(
    agent_name: str, 
    context: str, 
    round_type: str,
    model,  # Pre-configured model passed from round node
    prev_draft: str = "",
    peer_drafts: str = "",
    domain: str = "Software Engineering",
    max_retries: int = 3
) -> str:
    """
    Execute a single agent's analysis round with retry logic.
    Model is pre-configured with the correct API key by the calling round node.

    Args:
        agent_name: Name of the agent (legal, business, finance)
        context: Combined document text
        round_type: ROUND_1, ROUND_2, or ROUND_3
        model: Pre-configured Gemini model with round-specific API key
        prev_draft: Agent's previous draft (for rounds 2-3)
        peer_drafts: Other agents' drafts (for rounds 2-3)
        domain: Business domain context
        max_retries: Number of retry attempts

    Returns:
        Agent's analysis text
    """
    persona = COUNCIL_PERSONAS.get(agent_name)
    if not persona:
        raise ValueError(f"Unknown agent: {agent_name}")

    # Build prompt
    base_prompt = PROMPT_TEMPLATES[round_type].format(
        role=persona['role'],
        current_draft=prev_draft,
        peer_drafts=peer_drafts,
        domain=domain
    )
    
    # Only include document context in Round 1
    # Rounds 2-3 focus on peer analysis, not re-reading the document
    if round_type == "ROUND_1":
        # Truncate context to avoid token limits
        max_context = settings.MAX_CONTEXT_CHARS
        truncated_context = context[:max_context]
        if len(context) > max_context:
            truncated_context += f"\n\n[...truncated {len(context) - max_context:,} characters...]"
        full_prompt = f"{base_prompt}\n\n=== DOCUMENTS ===\n{truncated_context}"
    else:
        # Round 2 & 3: Focus on cross-checking peer analyses, not re-analyzing document
        full_prompt = base_prompt

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            # Small delay only on retries
            if attempt > 0:
                retry_delay = 15 * (attempt + 1)  # 30s, 45s for retries
                logger.info(f"[{agent_name}] Retry {attempt + 1}, waiting {retry_delay}s")
                await asyncio.sleep(retry_delay)

            response = await model.generate_content_async(full_prompt)

            if not response or not response.text:
                raise AIModelError(
                    model=settings.GEMINI_MODEL_TEXT,
                    details="Empty response from model"
                )

            logger.info(
                f"[{agent_name}] {round_type} completed - {len(response.text)} chars",
                extra={"agent": agent_name}
            )
            return response.text.strip()

        except Exception as e:
            last_error = e
            logger.warning(
                f"[{agent_name}] {round_type} attempt {attempt + 1} failed: {str(e)}",
                extra={"agent": agent_name}
            )

            # For rate limit errors, wait longer before retry
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                wait_time = 60  # Wait full minute for rate limits
                logger.info(f"[{agent_name}] Rate limited, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)

            if attempt == max_retries - 1:
                logger.error(f"[{agent_name}] All retries exhausted", extra={"agent": agent_name})

    return f"Error: {str(last_error)}"


async def node_round_1_blind(state: CouncilState) -> dict:
    """Round 1: Independent Analysis - Each agent analyzes without seeing others"""
    logger.info("--- Council Round 1: Blind Draft (using API Key 1) ---")

    domain = state.get("domain", "Software Engineering")

    # Create model with Round 1's API key BEFORE parallel execution
    model = create_model_for_round("ROUND_1")

    # Run all agents in PARALLEL - safe because we configured the API key above
    tasks = [
        run_agent_round(agent, state["combined_context"], "ROUND_1", model, domain=domain)
        for agent in ["legal", "business", "finance"]
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    drafts = {}
    errors = {}

    for agent, result in zip(["legal", "business", "finance"], results):
        if isinstance(result, Exception):
            logger.error(f"[Round 1] {agent} failed: {result}")
            drafts[agent] = f"Error: {str(result)}"
            errors[agent] = str(result)
        else:
            drafts[agent] = result
            logger.info(f"[Round 1] {agent} completed: {len(result)} chars")

    return {
        "round_1_drafts": drafts,
        "errors": errors
    }

async def node_round_2_crosscheck(state: CouncilState) -> dict:
    """Round 2: Cross-Check - Each agent reviews peers' drafts and refines"""
    logger.info("--- Council Round 2: Cross-Check (using API Key 2) ---")

    drafts = state["round_1_drafts"]
    domain = state.get("domain", "Software Engineering")

    # Build peer context for each agent
    peer_contexts = {
        "legal": f"Business Analysis:\n{drafts['business']}\n\nFinance Analysis:\n{drafts['finance']}",
        "business": f"Legal Analysis:\n{drafts['legal']}\n\nFinance Analysis:\n{drafts['finance']}",
        "finance": f"Legal Analysis:\n{drafts['legal']}\n\nBusiness Analysis:\n{drafts['business']}"
    }

    # Create model with Round 2's API key BEFORE parallel execution
    model = create_model_for_round("ROUND_2")

    # Run all agents in PARALLEL - safe because we configured the API key above
    tasks = [
        run_agent_round(
            agent,
            state["combined_context"],
            "ROUND_2",
            model,
            prev_draft=drafts[agent],
            peer_drafts=peer_contexts[agent],
            domain=domain
        )
        for agent in ["legal", "business", "finance"]
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    updated_drafts = {}
    for agent, result in zip(["legal", "business", "finance"], results):
        if isinstance(result, Exception):
            logger.error(f"[Round 2] {agent} failed: {result}")
            updated_drafts[agent] = drafts[agent]  # Keep Round 1 draft
        else:
            updated_drafts[agent] = result
            logger.info(f"[Round 2] {agent} refined: {len(result)} chars")

    return {"round_2_drafts": updated_drafts}

def _parse_flashcard_json(raw_result: str, agent: str) -> dict:
    """
    Parse and validate flashcard JSON from agent response.
    Handles various formats and cleanup.
    """
    if not raw_result or raw_result.startswith("Error:"):
        logger.warning(f"[{agent}] Empty or error response")
        return {"flashcards": [], "error": "Empty response", "raw": raw_result[:200] if raw_result else ""}

    # Clean JSON markers
    clean_json = raw_result.strip()

    # Remove markdown code blocks
    if clean_json.startswith("```json"):
        clean_json = clean_json[7:]
    elif clean_json.startswith("```"):
        clean_json = clean_json[3:]
    if clean_json.endswith("```"):
        clean_json = clean_json[:-3]
    clean_json = clean_json.strip()

    # Find JSON object start
    if not clean_json.startswith("{"):
        start_idx = clean_json.find("{")
        if start_idx != -1:
            clean_json = clean_json[start_idx:]

    # Find JSON object end
    if not clean_json.endswith("}"):
        end_idx = clean_json.rfind("}")
        if end_idx != -1:
            clean_json = clean_json[:end_idx + 1]

    try:
        parsed = json.loads(clean_json)
        flashcards = parsed.get("flashcards", [])
        logger.info(f"[{agent}] Parsed {len(flashcards)} flashcards")
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"[{agent}] JSON parse error: {e}")
        return {
            "flashcards": [],
            "error": f"JSON parse error: {str(e)}",
            "raw": raw_result[:500]
        }


async def node_round_3_verdict(state: CouncilState) -> dict:
    """Round 3: Final Verdict - Generate actionable flashcards"""
    logger.info("--- Council Round 3: Final Verdict (using API Key 3) ---")

    drafts = state["round_2_drafts"]
    domain = state.get("domain", "Software Engineering")

    # Build peer context for each agent
    peer_contexts = {
        "legal": f"Business Analysis:\n{drafts['business']}\n\nFinance Analysis:\n{drafts['finance']}",
        "business": f"Legal Analysis:\n{drafts['legal']}\n\nFinance Analysis:\n{drafts['finance']}",
        "finance": f"Legal Analysis:\n{drafts['legal']}\n\nBusiness Analysis:\n{drafts['business']}"
    }

    # Create model with Round 3's API key BEFORE parallel execution
    model = create_model_for_round("ROUND_3")

    # Run all agents in PARALLEL - safe because we configured the API key above
    tasks = [
        run_agent_round(
            agent,
            state["combined_context"],
            "ROUND_3",
            model,
            prev_draft=drafts[agent],
            peer_drafts=peer_contexts[agent],
            domain=domain
        )
        for agent in ["legal", "business", "finance"]
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final_output = {}
    for agent, result in zip(["legal", "business", "finance"], results):
        if isinstance(result, Exception):
            logger.error(f"[Round 3] {agent} failed: {result}")
            final_output[agent] = {"flashcards": [], "error": str(result)}
        else:
            final_output[agent] = _parse_flashcard_json(result, agent)

    return {"round_3_final": final_output}


async def node_generate_patch_pack(state: CouncilState) -> dict:
    """Aggregator: Consolidates flashcards from all agents into deliverables"""
    logger.info("--- Generating Patch Pack ---")

    all_cards = []
    agent_stats = {}

    for agent, data in state["round_3_final"].items():
        cards = data.get("flashcards", [])
        agent_stats[agent] = len(cards)

        for card in cards:
            # Ensure card has required fields with defaults
            enriched_card = {
                "id": card.get("id", f"{agent}_{len(all_cards)}"),
                "card_type": card.get("card_type", "Risk"),
                "title": card.get("title", "Untitled"),
                "description": card.get("description", ""),
                "fix_action": card.get("fix_action", ""),
                "severity": card.get("severity", "Medium"),
                "swipe_right_payload": card.get("swipe_right_payload", card.get("fix_action", "")),
                "source_agent": agent
            }
            all_cards.append(enriched_card)

    logger.info(f"Patch Pack generated: {len(all_cards)} total cards - {agent_stats}")

    return {
        "patch_pack": {
            "flashcards": all_cards,
            "summary": {
                "total_cards": len(all_cards),
                "by_agent": agent_stats
            }
        }
    }


def build_council_workflow() -> StateGraph:
    """
    Builds the LangGraph workflow for the 3-round council deliberation.

    Flow:
        round_1 (blind) -> round_2 (cross-check) -> round_3 (verdict) -> pack_generator -> END
    """
    logger.info("Building Council Workflow Graph")

    workflow = StateGraph(CouncilState)
    
    # Add nodes
    workflow.add_node("round_1", node_round_1_blind)
    workflow.add_node("round_2", node_round_2_crosscheck)
    workflow.add_node("round_3", node_round_3_verdict)
    workflow.add_node("pack_generator", node_generate_patch_pack)
    
    # Set entry point
    workflow.set_entry_point("round_1")
    
    # Define edges (linear flow)
    workflow.add_edge("round_1", "round_2")
    workflow.add_edge("round_2", "round_3")
    workflow.add_edge("round_3", "pack_generator")
    workflow.add_edge("pack_generator", END)
    
    logger.info("Council Workflow Graph compiled successfully")
    return workflow.compile()


# Compile the workflow on module load
council_app = build_council_workflow()