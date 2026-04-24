import random

def client_act(state):
    # 20% chance of change request
    if random.random() < 0.2:
        return {
            "agent": "client",
            "type": "add_change_request",
            "params": {}
        }

    return {
        "agent": "client",
        "type": "do_nothing",
        "params": {}
    }