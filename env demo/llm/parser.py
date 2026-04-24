"""
Safe JSON parsing for LLM manager output.
"""

import json
import re


def parse_manager_output(llm_output):
    """
    Safely parse LLM output to extract assignments and reasoning.
    
    Args:
        llm_output: Raw string from LLM
        
    Returns:
        (assignments, explanation) tuple
        - assignments: list of {"task_id": int, "worker_id": str}
        - explanation: string reasoning
        
        Returns (None, None) if parsing fails
    """
    
    if not llm_output or not isinstance(llm_output, str):
        return None, None
    
    try:
        # Try direct JSON parsing first
        parsed = json.loads(llm_output)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        try:
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', llm_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
            else:
                # Try to find JSON object in raw text
                json_match = re.search(r'\{[\s\S]*\}', llm_output)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                else:
                    return None, None
        except (json.JSONDecodeError, AttributeError):
            return None, None
    
    # Validate structure
    if not isinstance(parsed, dict):
        return None, None
    
    if "assignments" not in parsed:
        return None, None
    
    assignments = parsed.get("assignments", [])
    explanation = parsed.get("reasoning", "")
    
    # Validate assignments list
    if not isinstance(assignments, list):
        return None, None
    
    validated_assignments = []
    for assignment in assignments:
        if not isinstance(assignment, dict):
            continue
        
        task_id = assignment.get("task_id")
        worker_id = assignment.get("worker_id")
        
        # Validate types
        if not isinstance(task_id, int) or not isinstance(worker_id, str):
            continue
        
        if task_id < 0 or not worker_id:
            continue
        
        validated_assignments.append({
            "task_id": task_id,
            "worker_id": worker_id
        })
    
    if not validated_assignments:
        return None, None
    
    return validated_assignments, str(explanation) if explanation else ""
