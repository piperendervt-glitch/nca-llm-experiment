"""
nca_network_v9d.py

NCA v9d: Game-Theory AntiNode (Veto + Level-K Selective Intervention).

Fundamental difference from v9c:
  - v9c: argues against majority on ALL tasks (random-like, weight=0.5, no effect)
  - v9d: intervenes ONLY on unanimous (3-0) decisions where the task type
    has historically high groupthink error rate (Level-K selection)

This is NOT "aggregation improvement" — it is "structural groupthink prevention."
The final verdict is always the majority (3:1 means majority wins), but
the experiment generates uncertainty flags and risk score learning data.

Design:
  1. Run standard best_fixed (3 steps, fixed roles)
  2. Check vote distribution: if NOT unanimous (3-0), skip AntiNode entirely
  3. Check task_type risk score: if below threshold (0.25), skip AntiNode
  4. If both conditions met: AntiNode argues against unanimous consensus
  5. Final verdict = majority (unchanged) but uncertainty_flagged = True
  6. Online learning: update risk scores based on correctness of unanimous decisions
"""

import json

from nca_network_v7 import (
    call_llm,
    run_nca_v7,
    format_output,
    aggregate_verdict,
    classify_groupthink,
)

# ── best_fixed configuration ──────────────────────────────────────────────

BEST_FIXED_CONFIG = {
    "models": ["qwen2.5:7b", "llama3:latest", "mistral:7b"],
    "agree": [30, 80, 80],
    "steps": 3,
    "role": "fixed",
}

ANTI_MODEL = "mistral:7b"


# ── Game-Theory AntiNode ──────────────────────────────────────────────────

class GameTheoryAntiNode:
    """
    Game-theory-based AntiNode with veto + Level-K selective intervention.

    v9c differences:
    - Only intervenes on unanimous (3-0) decisions (veto right)
    - Uses historical risk scores to select which task types to challenge
    - Weight = 1.0 when intervening (vs v9c's 0.5)
    - Final verdict stays as majority (3:1 = majority wins)
    - Generates uncertainty flags for downstream use
    """

    def __init__(self, model: str = ANTI_MODEL):
        self.model = model

        # Initialized from v7-v9c: "task types where unanimous was wrong"
        # From v9b groupthink data and per-type accuracy across versions
        self.risky_types = {
            "sequence":         0.35,
            "algebraic_expr":   0.40,
            "simultaneous_eq":  0.45,
            "polynomial":       0.40,
            "quadratic_ineq":   0.50,
            "area":             0.45,
            "world_consistency": 0.35,
        }
        self.default_risk = 0.20
        self.threshold = 0.25  # intervene if risk >= threshold

        # Tracking
        self.intervention_log = []
        self.risk_history = []

    def should_intervene(self, vote_dist: dict, task_type: str) -> tuple[bool, str]:
        """
        Decide whether to intervene.

        Returns (should_intervene, reason).
        """
        # Condition 1: Must be unanimous (3-0)
        is_unanimous = (vote_dist["CORRECT"] == 3 or vote_dist["INCORRECT"] == 3)
        if not is_unanimous:
            return False, "not_unanimous"

        # Condition 2: Task type risk must exceed threshold
        risk = self.risky_types.get(task_type, self.default_risk)
        if risk < self.threshold:
            return False, f"risk_too_low ({risk:.3f} < {self.threshold})"

        return True, f"unanimous + risky ({task_type}: {risk:.3f})"

    def propose(self, task_input: str, majority_label: str,
                node_outputs: list[dict], task_type: str) -> dict:
        """
        Propose counter-argument to unanimous decision.
        """
        anti_label = "INCORRECT" if majority_label == "CORRECT" else "CORRECT"

        majority_reasoning = "\n".join([
            f"Agent {i} ({['Solver','Verifier','Critic'][i]}): "
            f"{str(o.get('reasoning', ''))[:150]}"
            for i, o in enumerate(node_outputs)
        ])

        prompt = f"""You are a critical reviewer. All three agents unanimously agreed on {majority_label}.
Your role is to find specific reasons why they might ALL be wrong.

Task: {task_input}

All agents concluded: {majority_label}
Their reasoning:
{majority_reasoning}

Challenge this unanimous decision. Find:
1. Any overlooked edge cases
2. Any ambiguity in the problem statement
3. Any calculation or logic errors they all missed

If you find a strong reason to disagree, argue for {anti_label}.
If the unanimous decision seems correct after careful review, state {anti_label} but with low confidence.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "{anti_label}",
  "confidence": 0.0 to 1.0,
  "reasoning": "Your counter-argument in 2-3 sentences"
}}"""

        response = call_llm(self.model, prompt)
        decision = response.get("decision", "UNKNOWN")
        confidence = float(response.get("confidence", 0.5))
        reasoning = response.get("reasoning", str(response))

        # Did the AntiNode actually argue against majority?
        complied = (decision != majority_label)

        return {
            "anti_label": decision,
            "anti_confidence": confidence,
            "anti_reasoning": str(reasoning)[:500],
            "anti_complied": complied,
            "intervened": True,
            "task_type": task_type,
        }

    def aggregate_with_veto(self, node_outputs: list[dict],
                            anti_output: dict) -> dict:
        """
        Veto aggregation: AntiNode at weight=1.0 joins 4-node vote.

        With 3 unanimous nodes + 1 AntiNode:
          Majority: 3 * confidence (weight 1.0 each)
          Anti: 1 * confidence (weight 1.0)
          → Majority always wins (3:1)

        The value is NOT in changing the verdict but in:
          1. Recording uncertainty flags
          2. Measuring AntiNode's counter-argument quality
          3. Identifying tasks where unanimous consensus was fragile
        """
        scores = {"CORRECT": 0.0, "INCORRECT": 0.0}

        # Original 3 nodes at weight 1.0
        for output in node_outputs:
            decision = output.get("decision", "UNKNOWN")
            confidence = float(output.get("confidence", 0.5))
            if decision in scores:
                scores[decision] += confidence

        # AntiNode at weight 1.0
        anti_decision = anti_output.get("anti_label", "UNKNOWN")
        anti_confidence = anti_output.get("anti_confidence", 0.5)
        if anti_decision in scores:
            scores[anti_decision] += anti_confidence

        # Verdict (majority always wins with 3:1)
        if scores["CORRECT"] == scores["INCORRECT"]:
            verdict = "INCORRECT"
        else:
            verdict = max(scores, key=scores.get)

        return {
            "final_label": verdict,
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "uncertainty_flagged": True,
            "anti_confidence": anti_confidence,
        }

    def update_risk(self, task_type: str, was_unanimous: bool,
                    was_correct: bool):
        """
        Online learning: update risk scores via EMA (alpha=0.1).
        Only updates on unanimous decisions.
        """
        if not was_unanimous:
            return

        alpha = 0.1
        current = self.risky_types.get(task_type, self.default_risk)
        if not was_correct:
            updated = (1 - alpha) * current + alpha * 1.0
        else:
            updated = (1 - alpha) * current + alpha * 0.0
        self.risky_types[task_type] = round(updated, 4)

    def get_risk_scores(self) -> dict:
        return {k: round(v, 4) for k, v in sorted(self.risky_types.items())}


# ── Module-level instance ─────────────────────────────────────────────────

_anti_node = GameTheoryAntiNode()


def get_anti_node() -> GameTheoryAntiNode:
    return _anti_node


def run_v9d(task_input: str, task_type: str) -> dict:
    """Run best_fixed NCA + game-theory AntiNode.

    Note: task_type is required for Level-K risk assessment.
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

    # Pre-anti baseline
    pre_anti_majority = aggregate_verdict(node_outputs)
    pre_anti_groupthink = classify_groupthink(node_outputs)

    # Vote distribution
    votes = [o.get("decision", "UNKNOWN") for o in node_outputs]
    vote_dist = {
        "CORRECT": votes.count("CORRECT"),
        "INCORRECT": votes.count("INCORRECT"),
    }

    # Step 3: Check intervention conditions
    should_intervene, reason = _anti_node.should_intervene(vote_dist, task_type)

    if should_intervene:
        # Step 4: AntiNode proposes counter-argument
        anti_output = _anti_node.propose(
            task_input, pre_anti_majority, node_outputs, task_type
        )

        # Step 5: Veto aggregation
        veto_result = _anti_node.aggregate_with_veto(node_outputs, anti_output)
        final_verdict = veto_result["final_label"]
        anti_changed = (final_verdict != pre_anti_majority)

        return {
            **nca_result,
            "pattern_used": "best_fixed_veto",
            "final_verdict": final_verdict,
            "pre_anti_majority": pre_anti_majority,
            "pre_anti_groupthink": pre_anti_groupthink,
            "vote_distribution": vote_dist,
            # AntiNode fields
            "anti_intervened": True,
            "anti_reason": reason,
            "anti_label": anti_output.get("anti_label", "UNKNOWN"),
            "anti_confidence": anti_output.get("anti_confidence", 0.5),
            "anti_reasoning": anti_output.get("anti_reasoning", ""),
            "anti_complied": anti_output.get("anti_complied", False),
            "anti_changed_outcome": anti_changed,
            "uncertainty_flagged": True,
            # Aggregation
            "aggregation_scores": veto_result.get("scores", {}),
        }
    else:
        # No intervention — pass through best_fixed result
        return {
            **nca_result,
            "pattern_used": "best_fixed_veto",
            "final_verdict": pre_anti_majority,
            "pre_anti_majority": pre_anti_majority,
            "pre_anti_groupthink": pre_anti_groupthink,
            "vote_distribution": vote_dist,
            # AntiNode fields
            "anti_intervened": False,
            "anti_reason": reason,
            "anti_label": "",
            "anti_confidence": 0.0,
            "anti_reasoning": "",
            "anti_complied": False,
            "anti_changed_outcome": False,
            "uncertainty_flagged": False,
            "aggregation_scores": {},
        }
