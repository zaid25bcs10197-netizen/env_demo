def handle_qa_action(state, action):
    if action["type"] != "test":
        return

    task_id = action["params"]["task_id"]

    # ✅ FIX: correct task lookup
    task = next((t for t in state["tasks"] if t["id"] == task_id), None)

    if not task or task["status"] != "in_review":
        return

    bugs = task["bugs"]
    rejections = task["rejection_count"]
    complexity = task["complexity"]

    allowed_bugs = 2 if complexity <= 1.5 else 3

    if rejections >= 1:
        allowed_bugs += 1

    if bugs <= allowed_bugs:
        task["qa_status"] = "approved"
        task["status"] = "done"
        task["outcome"] = "success"

        state["metrics"]["completed_tasks"] += 1
    else:
        task["qa_status"] = "rejected"
        
        # Clear worker state so task can be reassigned
        worker_id = task["assigned_to"]
        if worker_id:
            worker = state["agents"]["workers"].get(worker_id)
            if worker:
                worker["current_task"] = None
                worker["is_busy"] = False
        
        task["assigned_to"] = None
        task["status"] = "todo"

        # reduce progress to allow rework
        task["progress"] = max(0.5, task["progress"] - 0.2)
        task["rejection_count"] += 1

        if task["bugs"] > 0:
            worker_id = task["assigned_to"]
            if worker_id:
                worker = state["agents"]["workers"].get(worker_id)
                if worker:
                    bugs_fixed = max(1, int(worker["skills"][task["type"]] * 2))
                    task["bugs"] = max(0, task["bugs"] - bugs_fixed)
                else:
                    task["bugs"] = max(0, task["bugs"] - 1)
            else:
                task["bugs"] = max(0, task["bugs"] - 1)