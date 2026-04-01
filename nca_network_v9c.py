"""
nca_network_v9c.py

NCA v9c: best_fixed + AntiNode (contrarian bias correction).

One-variable experiment: identical to best_fixed except an AntiNode
(mistral:7b, weight=0.5) is added AFTER the 3-step NCA completes.
The AntiNode always argues against the current majority, then its
vote is included in a weighted 4-node aggregation.

Design:
  1. Run standard best_fixed (3 steps, fixed roles)
  2. Compute 3-node majority from final step
  3. AntiNode sees all 3 outputs + task, instructed to argue AGAINST majority
  4. Final aggregation: 3 original nodes (weight=1.0) + AntiNode (weight=0.5)

NO MetaAgent (v9a only). NO dynamic weighting (v9b only).
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
ANTI_WEIGHT = 0.5  # AntiNode contributes half the weight of a regular node


# ── AntiNode ──────────────────────────────────────────────────────────────

def _build_anti_prompt(task_input: str, node_outputs: list[dict],
                       majority_verdict: str) -> str:
    """Build prompt that instructs AntiNode to argue against the majority."""
    nodes_summary = "\n".join([
        f"Node {i} ({['Solver','Verifier','Critic'][i]}): "
        f"{o.get('decision','UNKNOWN')} "
        f"(confidence: {float(o.get('confidence', 0.5)):.2f})\n"
        f"  Reasoning: {str(o.get('reasoning',''))[:300]}"
        for i, o in enumerate(node_outputs)
    ])

    opposite = "INCORRECT" if majority_verdict == "CORRECT" else "CORRECT"

    return f"""You are the Devil's Advocate in a reasoning network.
Your job is to argue AGAINST the current consensus.

Task: {task_input}

The three agents currently believe the answer is {majority_verdict}:
{nodes_summary}

Your role: Argue that the answer should be {opposite} instead.
Look for errors, overlooked cases, or flawed reasoning in their analysis.
If you genuinely cannot find any flaws, you may agree with them, but try hard to find problems.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CORRECT" or "INCORRECT",
  "confidence": 0.0 to 1.0,
  "reasoning": "Your counter-argument or agreement in 2-3 sentences"
}}"""


def weighted_aggregate(node_outputs: list[dict], anti_output: dict) -> tuple[str, dict]:
    """
    Aggregate 3 original nodes (weight=1.0 each) + AntiNode (weight=0.5).

    Returns (verdict, details_dict).
    """
    scores = {"CORRECT": 0.0, "INCORRECT": 0.0}

    # Original 3 nodes at weight 1.0
    for output in node_outputs:
        decision = output.get("decision", "UNKNOWN")
        confidence = float(output.get("confidence", 0.5))
        if decision in scores:
            scores[decision] += 1.0 * confidence

    # AntiNode at weight 0.5
    anti_decision = anti_output.get("decision", "UNKNOWN")
    anti_confidence = float(anti_output.get("confidence", 0.5))
    if anti_decision in scores:
        scores[anti_decision] += ANTI_WEIGHT * anti_confidence

    # Tie-break to INCORRECT (same as v7 baseline)
    if scores["CORRECT"] == scores["INCORRECT"]:
        verdict = "INCORRECT"
    else:
        verdict = max(scores, key=scores.get)

    details = {
        "scores": {k: round(v, 4) for k, v in scores.items()},
        "anti_decision": anti_decision,
        "anti_confidence": round(anti_confidence, 4),
        "anti_weight": ANTI_WEIGHT,
    }
    return verdict, details


# ── Main runner ───────────────────────────────────────────────────────────

def run_v9c(task_input: str) -> dict:
    """Run best_fixed NCA + AntiNode contrarian aggregation.

    Returns full result dict with AntiNode metadata.
    """
    models = BEST_FIXED_CONFIG["models"]

    # Step 1: Run standard best_fixed NCA (3 steps)
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

    # Step 3: Compute pre-anti majority (what best_fixed alone would say)
    pre_anti_majority = aggregate_verdict(node_outputs)
    pre_anti_groupthink = classify_groupthink(node_outputs)

    # Step 4: AntiNode argues against the majority
    anti_prompt = _build_anti_prompt(task_input, node_outputs, pre_anti_majority)
    anti_output = call_llm(ANTI_MODEL, anti_prompt)

    # Normalize decision
    anti_decision = anti_output.get("decision", "UNKNOWN")
    if anti_decision not in ("CORRECT", "INCORRECT"):
        anti_output["decision"] = "UNKNOWN"

    # Did AntiNode actually argue against majority (as instructed)?
    anti_complied = (anti_decision != pre_anti_majority)

    # Step 5: Weighted 4-node aggregation
    final_verdict, agg_details = weighted_aggregate(node_outputs, anti_output)

    # Did the AntiNode change the outcome?
    anti_changed_outcome = (final_verdict != pre_anti_majority)

    # Groupthink analysis: was unanimous groupthink prevented?
    groupthink_prevented = (
        pre_anti_groupthink in ("all_correct", "all_incorrect")
        and anti_changed_outcome
    )

    return {
        **nca_result,
        "pattern_used": "best_fixed_anti",
        "final_verdict": final_verdict,
        # Pre-anti baseline
        "pre_anti_majority": pre_anti_majority,
        "pre_anti_groupthink": pre_anti_groupthink,
        # AntiNode fields
        "anti_output": anti_output,
        "anti_complied": anti_complied,
        "anti_changed_outcome": anti_changed_outcome,
        "groupthink_prevented": groupthink_prevented,
        # Aggregation details
        "aggregation_details": agg_details,
    }
