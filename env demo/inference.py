from env import Environment

from agents.manager_agent import manager_act
from agents.worker_agent import worker_act
from agents.qa_agent import qa_act
from agents.client_agent import client_act


# =========================
# CONFIG
# =========================
config = {
    "num_tasks": 5,
    "max_steps": 30,
    "seed": 42,
    "task_arrival_prob": 0.2,
    "bug_injection_prob": 0.1
}


# =========================
# INIT
# =========================
env = Environment(config)
state = env.reset()


# =========================
# RUN LOOP
# =========================
for step in range(config["max_steps"]):
    print(f"\n========== STEP {step} ==========")

    actions = []

    # 🔥 Manager (IMPORTANT: returns LIST)
    manager_actions = manager_act(state)
    if isinstance(manager_actions, list):
        actions.extend(manager_actions)
    else:
        actions.append(manager_actions)

    # 👷 Workers
    actions.extend(worker_act(state))

    # 🧪 QA
    actions.append(qa_act(state))

    # 👤 Client
    actions.append(client_act(state))

    # =========================
    # DEBUG: PRINT ACTIONS
    # =========================
    print("\n[ACTIONS]")
    for a in actions:
        print(a)

    # =========================
    # STEP ENV
    # =========================
    state, reward, done, _ = env.step(actions)

    # =========================
    # DEBUG: PRINT STATE SUMMARY
    # =========================
    print(f"\n[SUMMARY]")
    print(f"Time: {state['time']}")
    print(f"Reward: {reward:.2f}")
    print(f"Client Satisfaction: {state['client']['satisfaction']:.2f}")

    print("\n[Tasks]")
    for t in state["tasks"]:
        print(
            f"Task {t['id']} | {t['status']} | prog={t['progress']:.2f} | bugs={t['bugs']} | assigned={t['assigned_to']}"
        )

    # =========================
    # END
    # =========================
    if done:
        print("\n=== SIMULATION COMPLETE ===")
        break


# =========================
# OPTIONAL: PRINT HISTORY
# =========================
print("\n=== HISTORY (last 5 steps) ===")
for h in env.history[-5:]:
    print(h)