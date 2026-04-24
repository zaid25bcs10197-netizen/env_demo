def handle_client_action(state, action):
    if action["type"] == "add_change_request":
        state["client"]["pending_change"] = True