import asyncio
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from fastapi import UploadFile

# Import your existing engines (we reuse the logic!)
from app.services.parser import extract_text_from_pdf
from app.services.tech_engine import analyze_tech_gaps
from app.services.biz_engine import analyze_proposal_leverage
from app.services.cross_check import run_cross_check


class AgentState(TypedDict):
    # Inputs
    raw_files: List[UploadFile]  
    filenames: List[str]
    
    # Internal Processing
    document_map: Dict[str, str]  # filename -> extracted text
    combined_context: str         # Merged text for cross-referencing
    
    # Outputs (Reports)
    tech_report: Optional[Dict[str, Any]]
    legal_report: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    
    # Error Handling
    errors: List[str]

# 2. Define the Nodes (The Agents)

async def node_parser(state: AgentState) -> Dict:
    """Agent 1: The Librarian - OCRs and prepares text from ALL files."""
    print(f"--- [Agent: Parser] Reading {len(state['raw_files'])} Documents... ---")
    
    doc_map = {}
    combined_text = ""
    errors = []

    try:
        for file_obj in state["raw_files"]:
            print(f"Parsing: {file_obj.filename}")
            # Reset cursor just in case
            await file_obj.seek(0)
            content = await file_obj.read()
            
            text = await extract_text_from_pdf(content)
            
            if "Error" in text and len(text) < 200:
                errors.append(f"Failed to parse {file_obj.filename}: {text}")
                continue

            doc_map[file_obj.filename] = text
            
            # Add Headers so the LLM knows which file is which
            combined_text += f"\n\n{'='*40}\nSOURCE DOCUMENT: {file_obj.filename}\n{'='*40}\n{text}\n"

        return {
            "document_map": doc_map,
            "combined_context": combined_text,
            "errors": errors
        }
    except Exception as e:
        return {"errors": [f"Parser Critical Failure: {str(e)}"]}

async def node_tech_analyst(state: AgentState) -> Dict:
    """Agent 2: The Architect - Finds technical gaps across all documents."""
    print("--- [Agent: Tech Analyst] Scrutinizing Combined Context... ---")
    try:
        if not state.get("combined_context"):
             return {"errors": ["No text context available for Tech Analyst"]}
             
        # We pass the COMBINED text. 
        # The prompt in tech_engine (which we will update) handles the differentiation.
        report = await analyze_tech_gaps(state["combined_context"])
        return {"tech_report": report}
    except Exception as e:
        return {"errors": [f"Tech Analyst Error: {str(e)}"]}

async def node_legal_counsel(state: AgentState) -> Dict:
    """Agent 3: The Lawyer - Finds traps and negotiates."""
    print("--- [Agent: Legal Counsel] Reviewing Contracts & Proposals... ---")
    try:
        if not state.get("combined_context"):
             return {"errors": ["No text context available for Legal Counsel"]}

        report = await analyze_proposal_leverage(state["combined_context"])
        return {"legal_report": report}
    except Exception as e:
        return {"errors": [f"Legal Counsel Error: {str(e)}"]}

async def node_orchestrator(state: AgentState) -> Dict:
    """Agent 4: The Boss - Synthesizes insights."""
    print("--- [Agent: Orchestrator] Finalizing Multi-Doc Strategy... ---")
    try:
        # In multi-file mode, combined_context holds everything.
        # Ideally, we'd split it if we knew exactly which file was which type,
        # but passing the big context to the Orchestrator works because the LLM is smart.
        full_context = state.get("combined_context", "")
        
        # We perform a robust check
        final = await run_cross_check(
            tech_text=full_context[:60000],   # Increased Token Limit context
            proposal_text="",                 # (Included in tech_text variable efficiently)
            diagram_data=None,
            tech_report=state.get("tech_report"),
            legal_report=state.get("legal_report")
        )
        return {"final_report": final}
    except Exception as e:
        return {"errors": [f"Orchestrator Error: {str(e)}"]}

# 3. Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("parser", node_parser)
workflow.add_node("tech_analyst", node_tech_analyst)
workflow.add_node("legal_counsel", node_legal_counsel)
workflow.add_node("orchestrator", node_orchestrator)

# Define Flow
workflow.set_entry_point("parser")

# Parallel Execution
workflow.add_edge("parser", "tech_analyst")
workflow.add_edge("parser", "legal_counsel")

# Converge
workflow.add_edge("tech_analyst", "orchestrator")
workflow.add_edge("legal_counsel", "orchestrator")

workflow.add_edge("orchestrator", END)

# Compile
app_workflow = workflow.compile()