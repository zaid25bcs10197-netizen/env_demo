def qa_act(state):
    for task in state["tasks"]:
        if task["status"] == "in_review":
            return {
                "agent": "qa",
                "type": "test",
                "params": {"task_id": task["id"]}
            }

    return {"agent": "qa", "type": "do_nothing", "params": {}}