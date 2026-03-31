"""
nca_network_v8.py

NCA v8: Adaptive model selection based on difficulty classification.
Routes tasks to optimal patterns based on v7-v7.6 findings:
  Easy   -> single_agent (qwen2.5:7b)
  Medium -> best_fixed (qwen2.5:7b + llama3 + mistral, fixed roles)
  Hard   -> balanced_rotating (mistral + llama3 + llama3.1:8b, rotating roles)
"""

from nca_network_v7 import run_nca_v7, run_single_agent
from embedding_classifier import classify_difficulty

# ── Routing configurations ───────────────────────────────────────────────────

ROUTING = {
    "easy": {
        "pattern": "single_agent",
        "models": ["qwen2.5:7b"],
        "agree": [100],
        "steps": 1,
        "role": "none",
    },
    "medium": {
        "pattern": "best_fixed",
        "models": ["qwen2.5:7b", "llama3:latest", "mistral:7b"],
        "agree": [30, 80, 80],
        "steps": 3,
        "role": "fixed",
    },
    "hard": {
        "pattern": "balanced_rotating",
        "models": ["mistral:7b", "llama3:latest", "llama3.1:8b"],
        "agree": [80, 70, 10],
        "steps": 2,
        "role": "rotating",
    },
}


def run_adaptive(task_input: str, anchor_vecs: dict,
                 task_type: str = None, task_set: str = None) -> dict:
    """Run adaptive NCA: classify difficulty, route to optimal pattern, execute.

    Returns full result dict with routing metadata.
    """
    difficulty, classification_meta = classify_difficulty(
        task_input, anchor_vecs,
        task_type=task_type, task_set=task_set,
    )

    config = ROUTING[difficulty]

    if config["role"] == "none":
        result = run_single_agent(task_input, config["models"][0])
    else:
        result = run_nca_v7(
            task_input,
            config["models"],
            config["agree"],
            config["steps"],
            config["role"],
        )

    return {
        **result,
        "difficulty": difficulty,
        "pattern_used": config["pattern"],
        "classification_meta": classification_meta,
    }
