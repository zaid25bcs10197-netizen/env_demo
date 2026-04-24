def mock_llm_call(prompt):
    """
    Mock LLM call function. Replace with real LLM later (HuggingFace/OpenAI).
    """
    import json
    
    # Simple mock: assign first available worker to first available task
    return json.dumps({
        "assignments": [
            {"task_id": 0, "worker_id": "worker_1"}
        ],
        "reasoning": "Assigned task 0 to worker_1 based on availability and skill"
    })


def compute_score(state, task, worker):
    skill = worker["skills"][task["type"]]
    fatigue = worker["fatigue"]
    time_left = task["deadline"] - state["time"]
    priority = task["priority"]
    bugs = task["bugs"]
    rejections = task["rejection_count"]

    score = 3 * skill
    score += 1.5 * priority
    score -= 2 * fatigue
    score -= 0.5 * bugs
    score += 1.5 * rejections

    if time_left <= 2:
        score += 3
    elif time_left <= 5:
        score += 1.5

    return score


def explain_decision(state, task, worker_id, score):
    worker = state["agents"]["workers"][worker_id]
    time_left = task["deadline"] - state["time"]

    return (
        f"Task {task['id']} -> {worker_id}\n"
        f"  - skill: {worker['skills'][task['type']]:.2f}\n"
        f"  - priority: {task['priority']}\n"
        f"  - deadline in: {time_left}\n"
        f"  - fatigue: {worker['fatigue']:.2f}\n"
        f"  - score: {score:.2f}"
    )


def rule_based_manager_act(state):
    """
    Original rule-based manager logic. Used as fallback when LLM fails.
    """
    actions = []

    tasks = state["tasks"]
    workers = state["agents"]["workers"]

    # Prevent hopeless tasks (bugs >= 5)
    for task in tasks:
        if task["status"] == "in_progress":
            if task["bugs"] >= 5:
                task["status"] = "failed"
                task["outcome"] = "failed"
                state["metrics"]["failed_tasks"] += 1
                task["assigned_to"] = None

    used_tasks = set()  # 🔥 prevents duplicate assignment

    for worker_id, worker in workers.items():
        if worker["is_busy"]:
            continue

        best_task = None
        best_score = float("-inf")

        for task in tasks:
            if task["status"] != "todo":
                continue

            if task["id"] in used_tasks:
                continue

            score = compute_score(state, task, worker)

            if score > best_score:
                best_score = score
                best_task = task

        if best_task:
            actions.append({
                "agent": "manager",
                "type": "assign_task",
                "params": {
                    "task_id": best_task["id"],
                    "worker_id": worker_id
                }
            })

            used_tasks.add(best_task["id"])

            print("\n[RULE-BASED MANAGER DECISION]")
            print(explain_decision(state, best_task, worker_id, best_score))

    return actions


def manager_act(state):
    """
    Manager decision making with LLM support and rule-based fallback.
    
    1. Try LLM-based decisions first
    2. Fall back to rule-based logic if LLM fails
    3. Print explanations for both
    """
    
    # Prevent hopeless tasks (bugs >= 5) - always do this first
    tasks = state["tasks"]
    for task in tasks:
        if task["status"] == "in_progress":
            if task["bugs"] >= 5:
                task["status"] = "failed"
                task["outcome"] = "failed"
                state["metrics"]["failed_tasks"] += 1
                task["assigned_to"] = None
    
    # Try LLM-based manager first
    try:
        from llm.manager_llm import llm_manager_act
        
        actions, explanation = llm_manager_act(state, mock_llm_call)
        
        if actions is not None:
            # LLM succeeded
            if explanation:
                print("\n[LLM MANAGER EXPLANATION]")
                print(explanation)
            return actions
        
    except Exception as e:
        print(f"[LLM IMPORT ERROR] {str(e)}")
    
    # Fallback to rule-based manager
    print("\n[FALLBACK TO RULE-BASED MANAGER]")
    return rule_based_manager_act(state)