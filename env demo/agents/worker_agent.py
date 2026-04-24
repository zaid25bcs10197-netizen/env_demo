def worker_act(state):
    actions = []

    for worker_id, worker in state["agents"]["workers"].items():
        if worker["current_task"] is not None:
            actions.append({
                "agent": worker_id,
                "type": "work",
                "params": {"task_id": worker["current_task"]}
            })
        else:
            actions.append({
                "agent": worker_id,
                "type": "do_nothing",
                "params": {}
            })

    return actions