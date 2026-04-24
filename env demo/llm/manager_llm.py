"""
LLM-based manager decision making with fallback to rule-based logic.
"""

from llm.prompts import build_manager_prompt
from llm.parser import parse_manager_output


def llm_manager_act(state, llm_call_fn):
    """
    Use LLM to make manager decisions.
    
    Args:
        state: Current environment state
        llm_call_fn: Function that takes prompt and returns LLM response
        
    Returns:
        (actions, explanation) tuple
        - actions: list of assignment actions or None if parsing fails
        - explanation: string explanation or empty string
    """
    
    try:
        # Step 1: Build prompt
        prompt = build_manager_prompt(state)
        
        # Step 2: Call LLM
        response = llm_call_fn(prompt)
        
        # Debug logging
        print("\n[LLM RAW OUTPUT]")
        print(response[:200] + "..." if len(response) > 200 else response)
        
        # Step 3: Parse output
        assignments, explanation = parse_manager_output(response)
        
        if assignments is None:
            print("[LLM PARSING FAILED] Returning None for fallback")
            return None, None
        
        # Step 4: Convert assignments to actions
        actions = []
        for assignment in assignments:
            task_id = assignment["task_id"]
            worker_id = assignment["worker_id"]
            
            # Validate that task and worker exist
            task = next((t for t in state["tasks"] if t["id"] == task_id), None)
            worker = state["agents"]["workers"].get(worker_id)
            
            if not task or not worker:
                continue
            
            # Skip if task not available
            if task["status"] != "todo":
                continue
            
            # Skip if worker is busy
            if worker["is_busy"]:
                continue
            
            actions.append({
                "agent": "manager",
                "type": "assign_task",
                "params": {
                    "task_id": task_id,
                    "worker_id": worker_id
                }
            })
        
        if not actions:
            return None, None
        
        return actions, explanation
        
    except Exception as e:
        print(f"[LLM ERROR] {str(e)}")
        return None, None
