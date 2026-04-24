import copy
import random

from action_handlers.manager import handle_manager_action
from action_handlers.worker import handle_worker_action
from action_handlers.qa import handle_qa_action
from action_handlers.client import handle_client_action

from validators import is_valid_action


class Environment:
    def __init__(self, config):
        self.config = config
        self.state = None
        self.rng = random.Random(config.get("seed", 42))
        self.history = []
        self.task_map = {}

    # =========================
    # RESET
    # =========================
    def reset(self):
        self.state = {"time": 0}  # Initialize time first
        tasks = self._init_tasks()
        agents = self._init_agents()
        self.state = {
            "time": 0,
            "tasks": tasks,
            "agents": agents,
            "client": {
                "satisfaction": 1.0,
                "pending_change": False
            },
            "metrics": {
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_bugs": 0
            },
            "cost": 0.0
        }
        self.task_map = {t["id"]: t for t in self.state["tasks"]}
        return copy.deepcopy(self.state)

    # =========================
    # STEP
    # =========================
    def step(self, actions):
        # Track deltas for reward calculation
        prev_completed = self.state["metrics"]["completed_tasks"]
        prev_failed = self.state["metrics"]["failed_tasks"]
        prev_progress = sum(t["progress"] for t in self.state["tasks"])

        reward = 0

        # 1. Apply actions
        for action in actions:
            if not is_valid_action(self.state, action):
                continue

            agent = action["agent"]

            if agent == "manager":
                handle_manager_action(self.state, action)

            elif "worker" in agent:
                handle_worker_action(self.state, action)

            elif agent == "qa":
                handle_qa_action(self.state, action)

            elif agent == "client":
                handle_client_action(self.state, action)

        # 2. Worker fatigue
        self._update_fatigue()

        # 3. Random dynamics
        self._random_bug_injection()
        self._maybe_add_random_task()

        # 4. Deadlines (update state, not reward)
        self._update_deadlines()

        # 5. Client satisfaction (update state, not reward)
        self._update_client_satisfaction()

        # 6. Penalize ignoring client (update state)
        self._penalize_ignored_changes()

        # 7. Cost (update state)
        self._update_cost()

        # 8. Time
        self.state["time"] += 1

        # =========================
        # REWARD CALCULATION
        # =========================
        
        # Calculate deltas
        completed_delta = self.state["metrics"]["completed_tasks"] - prev_completed
        failed_delta = self.state["metrics"]["failed_tasks"] - prev_failed
        progress_delta = sum(t["progress"] for t in self.state["tasks"]) - prev_progress

        # Reset reward for new calculation
        reward = 0.0

        # Completion reward
        reward += 5.0 * completed_delta

        # Failure penalty
        reward -= 2.0 * failed_delta

        # Time cost (light)
        num_workers = len(self.state["agents"]["workers"])
        reward -= 0.05 * num_workers

        # Bug penalty (very light)
        total_bugs = sum(t["bugs"] for t in self.state["tasks"])
        reward -= 0.02 * total_bugs

        # Progress reward (smooth)
        reward += 1.0 * progress_delta

        # 9. Logging
        self.history.append({
            "time": self.state["time"],
            "reward": reward,
            "completed": self.state["metrics"]["completed_tasks"],
            "failed": self.state["metrics"]["failed_tasks"],
            "bugs": self.state["metrics"]["total_bugs"],
            "satisfaction": self.state["client"]["satisfaction"]
        })

        done = self._check_done()

        return copy.deepcopy(self.state), reward, done, {}

    # =========================
    # FATIGUE
    # =========================
    def _update_fatigue(self):
        for worker in self.state["agents"]["workers"].values():
            if worker["is_busy"]:
                worker["fatigue"] += 0.05
            else:
                worker["fatigue"] -= 0.03

            worker["fatigue"] = max(0, min(1, worker["fatigue"]))

    # =========================
    # DYNAMIC TASK ARRIVAL
    # =========================
    def _maybe_add_random_task(self):
        base_prob = self.config.get("task_arrival_prob", 0.2)

        if self.state["client"]["pending_change"]:
            prob = min(1.0, base_prob * 2)
        else:
            prob = base_prob

        if self.rng.random() < prob:
            new_id = len(self.state["tasks"])
            task = self._generate_task(new_id)
            self.state["tasks"].append(task)
            self.task_map[new_id] = task

            # resolve client request
            self.state["client"]["pending_change"] = False

    # =========================
    # RANDOM BUG INJECTION
    # =========================
    def _random_bug_injection(self):
        for task in self.state["tasks"]:
            if task["status"] == "in_progress":
                if self.rng.random() < self.config.get("bug_injection_prob", 0.1):
                    task["bugs"] += 1
                    self.state["metrics"]["total_bugs"] += 1

    # =========================
    # DEADLINES
    # =========================
    def _update_deadlines(self):
        reward = 0
        t = self.state["time"]

        for task in self.state["tasks"]:
            if (
                task["status"] != "done"
                and task["outcome"] is None
                and t > task["deadline"]
            ):
                task["outcome"] = "failed"
                self.state["metrics"]["failed_tasks"] += 1
                reward -= 5

        return reward

    # =========================
    # CLIENT SATISFACTION
    # =========================
    def _update_client_satisfaction(self):
        client = self.state["client"]

        prev = client["satisfaction"]

        completed = self.state["metrics"]["completed_tasks"]
        failed = self.state["metrics"]["failed_tasks"]

        client["satisfaction"] += 0.02 * completed
        client["satisfaction"] -= 0.01 * failed

        client["satisfaction"] = max(0, min(1, client["satisfaction"]))

        # return delta (NOT absolute value)
        return client["satisfaction"] - prev

    # =========================
    # PENALIZE IGNORED CLIENT
    # =========================
    def _penalize_ignored_changes(self):
        penalty = 0

        if self.state["client"]["pending_change"]:
            penalty -= 0.1
            self.state["client"]["satisfaction"] -= 0.02

        return penalty

    # =========================
    # COST
    # =========================
    def _update_cost(self):
        step_cost = 0

        for worker in self.state["agents"]["workers"].values():
            if worker["is_busy"]:
                step_cost += 1

        self.state["cost"] += step_cost
        return 0.1 * step_cost

    # =========================
    # DONE
    # =========================
    def _check_done(self):
        return self.state["time"] >= self.config["max_steps"]

    # =========================
    # INIT
    # =========================
    def _init_tasks(self):
        return [self._generate_task(i) for i in range(self.config["num_tasks"])]

    def _generate_task(self, t):
        return {
            "id": t,
            "type": self.rng.choice(["feature", "bugfix"]),
            "status": "todo",
            "assigned_to": None,
            "progress": 0.0,
            "bugs": 0,
            "deadline": self.state["time"] + self.rng.randint(5, 10),
            "priority": self.rng.randint(1, 3),
            "complexity": self.rng.uniform(0.5, 2.0),
            "created_at": self.state["time"],
            "outcome": None,
            "qa_status": "pending",
            "rejection_count": 0
        }

    def _init_agents(self):
        return {
            "manager": {},
            "workers": {
                "worker_1": self._create_worker(),
                "worker_2": self._create_worker()
            },
            "qa": {
                "current_task": None
            }
        }

    def _create_worker(self):
        return {
            "current_task": None,
            "efficiency": self.rng.uniform(0.5, 1.0),
            "is_busy": False,
            "fatigue": 0.0,
            "skills": {
                "feature": self.rng.uniform(0.3, 1.0),
                "bugfix": self.rng.uniform(0.3, 1.0)
            }
        }