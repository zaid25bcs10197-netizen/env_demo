import random


def handle_worker_action(state, action):
    if action["type"] != "work":
        return

    worker_id = action["agent"]
    task_id = action["params"]["task_id"]

    worker = state["agents"]["workers"].get(worker_id)

    # ✅ FIX: correct task lookup
    task = next((t for t in state["tasks"] if t["id"] == task_id), None)

    if not worker or not task:
        return

    if worker["current_task"] != task_id:
        worker["fatigue"] = min(1.0, worker["fatigue"] + 0.02)
        return

    skill = worker["skills"][task["type"]]
    fatigue = worker["fatigue"]
    efficiency = worker["efficiency"]
    complexity = task["complexity"]
    rejections = task["rejection_count"]
    bugs = task["bugs"]

    effective_efficiency = efficiency * (1 - fatigue)

    time_left = task["deadline"] - state["time"]
    urgency_multiplier = 1 + max(0, (3 - time_left)) * 0.1

    base_progress = (
        effective_efficiency
        * skill
        * (0.3 + 0.7 * (1 - task["progress"]))
    ) / (complexity + 0.5)

    bug_penalty = 1 / (1 + bugs * 0.3)
    rework_penalty = 1 / (1 + rejections * 0.2)

    progress_gain = base_progress * urgency_multiplier * bug_penalty * rework_penalty

    if progress_gain < 0.01:
        progress_gain *= 0.5

    # Ensure tasks can finish (avoid 0.8–0.9 stall)
    if task["progress"] > 0.8:
        progress_gain = max(progress_gain, 0.03)

    task["progress"] = min(1.0, task["progress"] + progress_gain)

    # BUGS
    base_bug = (1 - skill) * 0.6
    fatigue_impact = 0.15 * fatigue
    rejection_impact = 0.05 * rejections

    bug_chance = min(0.9, max(0.05, base_bug + fatigue_impact + rejection_impact))

    if random.random() < bug_chance:
        new_bugs = 1 if random.random() < 0.8 else 2
        task["bugs"] = min(5, task["bugs"] + new_bugs)
        state["metrics"]["total_bugs"] += new_bugs

    # SKILL LEARNING
    worker["skills"][task["type"]] = min(
        1.0,
        worker["skills"][task["type"]] + 0.005 * progress_gain
    )

    # Force completion if almost done and no bugs
    if task["progress"] >= 0.9 and task["bugs"] == 0:
        task["progress"] = 1.0

    # DONE → REVIEW
    if task["progress"] >= 1.0:
        task["status"] = "in_review"
        task["qa_status"] = "pending"

        worker["current_task"] = None
        worker["is_busy"] = False