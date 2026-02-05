# app/services/workflow.py
from typing import TypedDict, List, Dict, Any
import asyncio
import json
from langgraph.graph import StateGraph, END
from app.core.config import model_text
from app.core.prompts import COUNCIL_PERSONAS, PROMPT_TEMPLATES

# --- STATE MANAGEMENT ---
class CouncilState(TypedDict):
    combined_context: str
    domain: str
    
    # Internal Memory
    round_1_drafts: Dict[str, str]  # { "legal": "...", "finance": "..." }
    round_2_drafts: Dict[str, str]
    round_3_final: Dict[str, Any]
    
    # Final Output
    patch_pack: Dict[str, Any]

async def run_agent_round(
    agent_name: str, 
    context: str, 
    round_type: str, 
    prev_draft: str = "", 
    peer_drafts: str = "",
    domain: str = "Software Engineering"
):
    persona = COUNCIL_PERSONAS.get(agent_name)
    
    # Select Template based on Round
    base_prompt = PROMPT_TEMPLATES[round_type].format(
        role=persona['role'],
        current_draft=prev_draft,
        peer_drafts=peer_drafts,
        domain=domain
    )
    
    full_prompt = f"{base_prompt}\n\n=== DOCUMENTS ===\n{context[:30000]}"
    

    await asyncio.sleep(5) 
    
    try:
        response = await model_text.generate_content_async(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"


async def node_round_1_blind(state: CouncilState) -> dict:
    """Round 1: Independent Analysis"""
    print("--- Council Round 1: Blind Draft ---")
    
    tasks = [
        run_agent_round(agent, state["combined_context"], "ROUND_1", domain=state.get("domain", "Software Engineering")) 
        for agent in ["legal", "business", "finance"]
    ]
    results = await asyncio.gather(*tasks)
    
    return {
        "round_1_drafts": {
            "legal": results[0],
            "business": results[1],
            "finance": results[2]
        }
    }

async def node_round_2_crosscheck(state: CouncilState) -> dict:
    """Round 2: Read Peers & Critique"""
    print("--- Council Round 2: Cross-Check ---")
    drafts = state["round_1_drafts"]
  
    tasks = []
    
    # Legal Task
    tasks.append(run_agent_round(
        "legal", state["combined_context"], "ROUND_2", 
        prev_draft=drafts["legal"], 
        peer_drafts=f"Business Said: {drafts['business']}\nFinance Said: {drafts['finance']}",
        domain=state.get("domain", "Software Engineering")
    ))
    
    # Business Task
    tasks.append(run_agent_round(
        "business", state["combined_context"], "ROUND_2", 
        prev_draft=drafts["business"], 
        peer_drafts=f"Legal Said: {drafts['legal']}\nFinance Said: {drafts['finance']}",
        domain=state.get("domain", "Software Engineering")
    ))
    
    # Finance Task
    tasks.append(run_agent_round(
        "finance", state["combined_context"], "ROUND_2", 
        prev_draft=drafts["finance"], 
        peer_drafts=f"Legal Said: {drafts['legal']}\nBusiness Said: {drafts['business']}",
        domain=state.get("domain", "Software Engineering")
    ))
    
    results = await asyncio.gather(*tasks)
    
    return {
        "round_2_drafts": {
            "legal": results[0],
            "business": results[1],
            "finance": results[2]
        }
    }

async def node_round_3_verdict(state: CouncilState) -> dict:
    """Round 3: Generate Flashcards"""
    print("--- Council Round 3: Final Verdict ---")
    drafts = state["round_2_drafts"]
    
    peer_map = {
        "legal": f"Business Said: {drafts['business']}\nFinance Said: {drafts['finance']}",
        "business": f"Legal Said: {drafts['legal']}\nFinance Said: {drafts['finance']}",
        "finance": f"Legal Said: {drafts['legal']}\nBusiness Said: {drafts['business']}"
    }
    
    tasks = [
        run_agent_round(
            agent, state["combined_context"], "ROUND_3", 
            prev_draft=drafts[agent], 
            peer_drafts=peer_map[agent],
            domain=state.get("domain", "Software Engineering")
        )
        for agent in ["legal", "business", "finance"]
    ]
    results = await asyncio.gather(*tasks)
    
    final_output = {}
    for i, agent in enumerate(["legal", "business", "finance"]):
        raw_result = results[i]
        try:
            print(f"[{agent}] Raw response length: {len(raw_result)} chars")
            
            if not raw_result or raw_result.startswith("Error:"):
                print(f"[{agent}] Empty or error response: {raw_result[:100]}")
                final_output[agent] = {"flashcards": [], "error": "Empty response", "raw": raw_result}
                continue
            
            clean_json = raw_result.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()
            
            if not clean_json.startswith("{"):
                start_idx = clean_json.find("{")
                if start_idx != -1:
                    clean_json = clean_json[start_idx:]
            
            final_output[agent] = json.loads(clean_json)
            print(f"[{agent}] Parsed {len(final_output[agent].get('flashcards', []))} flashcards")
            
        except Exception as e:
            print(f"JSON Parse Error for {agent}: {e}")
            print(f"[{agent}] Raw content preview: {raw_result[:200] if raw_result else 'EMPTY'}")
            final_output[agent] = {"flashcards": [], "error": f"Failed to parse JSON: {e}", "raw": raw_result[:500] if raw_result else ""}

    return {"round_3_final": final_output}

async def node_generate_patch_pack(state: CouncilState) -> dict:
    """Aggregator: Consolidates Flashcards into Deliverables"""
    all_cards = []
    for agent, data in state["round_3_final"].items():
        if "flashcards" in data:
            for card in data["flashcards"]:
                card["source_agent"] = agent # Tag the source
                all_cards.append(card)
                
    return {"patch_pack": {"flashcards": all_cards}}


def build_council_workflow() -> StateGraph:
    workflow = StateGraph(CouncilState)
    
    workflow.add_node("round_1", node_round_1_blind)
    workflow.add_node("round_2", node_round_2_crosscheck)
    workflow.add_node("round_3", node_round_3_verdict)
    workflow.add_node("pack_generator", node_generate_patch_pack)
    
    workflow.set_entry_point("round_1")
    
    workflow.add_edge("round_1", "round_2")
    workflow.add_edge("round_2", "round_3")
    workflow.add_edge("round_3", "pack_generator")
    workflow.add_edge("pack_generator", END)
    
    return workflow.compile()

council_app = build_council_workflow()