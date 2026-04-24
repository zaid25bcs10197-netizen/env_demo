"""
LLM prompts for manager decision making.
"""


def build_manager_prompt(state):
    """
    Build a structured prompt for LLM to make manager decisions.
    
    Returns a prompt that asks for JSON assignments.
    """
    
    current_time = state["time"]
    tasks = state["tasks"]
    workers = state["agents"]["workers"]
    
    # Format tasks info
    tasks_info = []
    for task in tasks:
        if task["status"] == "todo":
            tasks_info.append({
                "id": task["id"],
                "type": task["type"],
                "status": task["status"],
                "progress": round(task["progress"], 2),
                "bugs": task["bugs"],
                "priority": task["priority"],
                "deadline": task["deadline"],
                "time_left": task["deadline"] - current_time,
                "complexity": task["complexity"],
                "assigned_to": task["assigned_to"]
            })
    
    # Format workers info
    workers_info = []
    for worker_id, worker in workers.items():
        workers_info.append({
            "id": worker_id,
            "is_busy": worker["is_busy"],
            "fatigue": round(worker["fatigue"], 2),
            "efficiency": round(worker["efficiency"], 2),
            "skills": {k: round(v, 2) for k, v in worker["skills"].items()}
        })
    
    prompt = f"""
You are a manager AI in a multi-agent task scheduling system.

CURRENT STATE:
- Time: {current_time}
- Available tasks: {len(tasks_info)}
- Available workers: {len(workers_info)}

TASKS TO ASSIGN (status=todo):
{format_tasks(tasks_info)}

AVAILABLE WORKERS (not busy):
{format_workers(workers_info)}

YOUR DECISION CRITERIA:
1. Prefer workers with HIGH SKILL for the task type
2. Avoid assigning to FATIGUED workers (fatigue > 0.7)
3. Prioritize tasks with:
   - LOW time_left (urgent)
   - HIGH priority
   - HIGH bugs (fix critical issues first)
4. NEVER assign a task already assigned
5. NEVER assign to busy workers

RETURN STRICTLY VALID JSON (no extra text):
{{
  "assignments": [
    {{"task_id": int, "worker_id": "worker_id"}},
    ...
  ],
  "reasoning": "Brief explanation of your assignments"
}}

Respond ONLY with the JSON. No markdown, no extra text.
""".strip()
    
    return prompt


def format_tasks(tasks_info):
    """Format task information for prompt."""
    if not tasks_info:
        return "  (No tasks available)"
    
    lines = []
    for task in tasks_info:
        lines.append(
            f"  Task {task['id']}: {task['type']}, "
            f"priority={task['priority']}, "
            f"bugs={task['bugs']}, "
            f"deadline_in={task['time_left']}, "
            f"complexity={task['complexity']}"
        )
    return "\n".join(lines)


def format_workers(workers_info):
    """Format worker information for prompt."""
    lines = []
    for worker in workers_info:
        if not worker["is_busy"]:
            skills_str = ", ".join(
                f"{k}={v}" for k, v in worker["skills"].items()
            )
            lines.append(
                f"  {worker['id']}: fatigue={worker['fatigue']}, "
                f"efficiency={worker['efficiency']}, "
                f"skills=[{skills_str}]"
            )
    
    if not lines:
        return "  (All workers busy)"
    return "\n".join(lines)
