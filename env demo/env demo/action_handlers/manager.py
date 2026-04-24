def handle_manager_action(state, action):
    typ = action["type"]

    if typ not in ["assign_task", "reassign_task"]:
        return

    task_id = action["params"]["task_id"]
    worker_id = action["params"].get("worker_id")

    # ✅ FIX: correct task lookup
    task = next((t for t in state["tasks"] if t["id"] == task_id), None)
    worker = state["agents"]["workers"].get(worker_id)

    if not task or not worker:
        return

    if typ == "assign_task":
        if task["assigned_to"] is not None or worker["is_busy"]:
            return

        task["assigned_to"] = worker_id
        task["status"] = "in_progress"

        worker["current_task"] = task_id
        worker["is_busy"] = True

    elif typ == "reassign_task":
        if worker["is_busy"]:
            return

        old_worker_id = task["assigned_to"]

        if old_worker_id:
            old_worker = state["agents"]["workers"][old_worker_id]
            old_worker["current_task"] = None
            old_worker["is_busy"] = False

        task["assigned_to"] = worker_id

        worker["current_task"] = task_id
        worker["is_busy"] = True