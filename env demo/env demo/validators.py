def is_valid_action(state, action):
    # Basic structure check
    if not isinstance(action, dict):
        return False

    if "agent" not in action or "type" not in action:
        return False

    agent = action["agent"]
    action_type = action["type"]
    params = action.get("params", {})

    # =========================
    # MANAGER ACTIONS
    # =========================
    if agent == "manager":
        if action_type not in ["assign_task", "reassign_task", "do_nothing"]:
            return False

        if action_type in ["assign_task", "reassign_task"]:
            if "task_id" not in params or "worker_id" not in params:
                return False

    # =========================
    # WORKER ACTIONS
    # =========================
    elif "worker" in agent:
        if action_type not in ["work", "do_nothing"]:
            return False

        if action_type == "work":
            if "task_id" not in params:
                return False

    # =========================
    # QA ACTIONS
    # =========================
    elif agent == "qa":
        if action_type not in ["test", "do_nothing"]:
            return False

        if action_type == "test":
            if "task_id" not in params:
                return False

    # =========================
    # CLIENT ACTIONS
    # =========================
    elif agent == "client":
        if action_type not in ["add_change_request", "do_nothing"]:
            return False

    else:
        return False

    return True