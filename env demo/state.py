state = {
    "time": int,

    "tasks": [
        {
            "id": int,

            # ✅ TASK TYPE (fixed set)
            "type": str,  
            # ["feature", "bugfix"]

            "status": str,  
            # ["todo", "in_progress", "in_review", "done"]

            "assigned_to": str | None,

            "progress": float,  # 0.0 → 1.0

            "bugs": int,

            "deadline": int,

            "priority": int,  # 1 → 3

            "created_at": int,

            "outcome": str | None,  
            # ["success", "failed", None]

            # ✅ QA SYSTEM
            "qa_status": str,  
            # ["pending", "approved", "rejected"]

            "rejection_count": int
        }
    ],

    "agents": {
        "manager": {},

        "workers": {
            "worker_1": {
                "current_task": int | None,
                "efficiency": float,
                "is_busy": bool,

                # ✅ SKILLS (task-specific)
                "skills": {
                    "feature": float,   # 0 → 1
                    "bugfix": float
                }
            },
            "worker_2": {
                "current_task": int | None,
                "efficiency": float,
                "is_busy": bool,
                "skills": {
                    "feature": float,
                    "bugfix": float
                }
            }
        },

        "qa": {
            "current_task": int | None
        }
    },

    "client": {
        "satisfaction": float,  # 0 → 1
        "pending_change": bool
    },

    "metrics": {
        "completed_tasks": int,
        "failed_tasks": int,
        "total_bugs": int
    }
}