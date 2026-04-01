"""
nca_network_v9b.py

NCA v9b: best_fixed + Dynamic Confidence-Weighted Aggregation.

One-variable experiment: identical to best_fixed except the aggregation
replaces simple majority voting with per-model trust weights that are:
  1. Initialized from historical accuracy (v7/v7.5/v7.6 best_fixed)
  2. Updated online after each task (exponential moving average, alpha=0.1)

NO MetaAgent (v9a only).
"""

import json
from pathlib import Path

from nca_network_v7 import (
    call_llm,
    run_nca_v7,
    format_output,
    classify_groupthink,
)

# ── best_fixed configuration (identical to v8 medium / v9a) ───────────────

BEST_FIXED_CONFIG = {
    "models": ["qwen2.5:7b", "llama3:latest", "mistral:7b"],
    "agree": [30, 80, 80],
    "steps": 3,
    "role": "fixed",
}

# ── Historical per-model accuracy from v7/v7.5/v7.6 best_fixed ───────────
# Computed from final-step individual node decisions vs ground truth:
#   qwen2.5:7b (solver):  185/250 = 0.740
#   llama3:latest (verifier): 192/250 = 0.768
#   mistral:7b (critic):  199/250 = 0.796

INITIAL_WEIGHTS = {
    "qwen2.5:7b": 0.740,
    "llama3:latest": 0.768,
    "mistral:7b": 0.796,
}

LEARNING_RATE = 0.1  # alpha for EMA updates


# ── Dynamic Weighted Aggregator ───────────────────────────────────────────

class DynamicWeightedAggregator:
    """
    Replaces simple majority voting with per-model trust-weighted
    confidence aggregation. Weights evolve online via EMA.
    """

    def __init__(self, initial_weights: dict[str, float] = None,
                 alpha: float = LEARNING_RATE):
        self.alpha = alpha
        self.weights = dict(initial_weights or INITIAL_WEIGHTS)
        self.history: list[dict] = []  # track weight evolution

    def aggregate(self, node_outputs: list[dict],
                  models: list[str]) -> tuple[str, dict]:
        """
        Weighted confidence aggregation.

        Each model's vote contributes: trust_weight * reported_confidence.

        Returns (verdict, details_dict).
        """
        scores = {"CORRECT": 0.0, "INCORRECT": 0.0}
        node_details = []

        for i, (output, model) in enumerate(zip(node_outputs, models)):
            decision = output.get("decision", "UNKNOWN")
            confidence = float(output.get("confidence", 0.5))
            trust = self.weights.get(model, 0.5)
            weighted_score = trust * confidence

            node_details.append({
                "node": i,
                "model": model,
                "decision": decision,
                "confidence": confidence,
                "trust_weight": round(trust, 4),
                "weighted_score": round(weighted_score, 4),
            })

            if decision in scores:
                scores[decision] += weighted_score

        # Tie-break: INCORRECT (same as v7 baseline)
        if scores["CORRECT"] == scores["INCORRECT"]:
            verdict = "INCORRECT"
        else:
            verdict = max(scores, key=scores.get)

        details = {
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "node_details": node_details,
            "current_weights": {m: round(w, 4) for m, w in self.weights.items()},
        }
        return verdict, details

    def update(self, node_outputs: list[dict], models: list[str],
               ground_truth: bool) -> dict:
        """
        Online learning: update trust weights based on ground truth.

        For each model, check if its final-step vote was correct.
        Update weight via EMA: w = (1-alpha)*w + alpha*reward
        where reward = 1.0 if correct, 0.0 if incorrect.

        Returns dict of weight changes for logging.
        """
        changes = {}
        for output, model in zip(node_outputs, models):
            decision = output.get("decision", "UNKNOWN")
            # Was this model's individual vote correct?
            if ground_truth is True:
                correct = (decision == "CORRECT")
            else:
                correct = (decision == "INCORRECT")

            reward = 1.0 if correct else 0.0
            old_w = self.weights.get(model, 0.5)
            new_w = (1 - self.alpha) * old_w + self.alpha * reward
            self.weights[model] = new_w

            changes[model] = {
                "old": round(old_w, 4),
                "new": round(new_w, 4),
                "delta": round(new_w - old_w, 4),
                "vote_correct": correct,
            }

        # Record snapshot
        self.history.append({
            "weights": {m: round(w, 4) for m, w in self.weights.items()},
        })

        return changes

    def get_weights(self) -> dict[str, float]:
        return {m: round(w, 4) for m, w in self.weights.items()}


# ── Module-level aggregator instance ──────────────────────────────────────

_aggregator = DynamicWeightedAggregator()


def get_aggregator() -> DynamicWeightedAggregator:
    """Access the module-level aggregator (for weight logging)."""
    return _aggregator


def run_v9b(task_input: str) -> dict:
    """Run best_fixed NCA + dynamic weighted aggregation.

    Returns full result dict with aggregation metadata.
    """
    models = BEST_FIXED_CONFIG["models"]

    # Step 1: Run standard best_fixed NCA
    nca_result = run_nca_v7(
        task_input,
        models,
        BEST_FIXED_CONFIG["agree"],
        BEST_FIXED_CONFIG["steps"],
        BEST_FIXED_CONFIG["role"],
    )

    # Step 2: Extract last step's node outputs
    last_step = nca_result["steps"][-1]
    node_outputs = [
        last_step["solver"]["output"],
        last_step["verifier"]["output"],
        last_step["critic"]["output"],
    ]

    # Step 3: Dynamic weighted aggregation (replaces simple majority)
    verdict, agg_details = _aggregator.aggregate(node_outputs, models)

    # Step 4: Also compute what simple majority would have said
    from nca_network_v7 import aggregate_verdict
    simple_majority = aggregate_verdict(node_outputs)

    groupthink = classify_groupthink(node_outputs)

    return {
        **nca_result,
        "pattern_used": "best_fixed_weighted",
        "final_verdict": verdict,
        "simple_majority": simple_majority,
        "aggregation_details": agg_details,
        "groupthink": groupthink,
    }
