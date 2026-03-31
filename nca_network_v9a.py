"""
nca_network_v9a.py

NCA v9a: best_fixed + MetaAgent (split-only intervention).

One-variable experiment: identical to best_fixed except MetaAgent
aggregates the final verdict when nodes disagree (split decisions).
Unanimous decisions pass through without MetaAgent intervention.
"""

import json

from nca_network_v7 import (
    call_llm,
    run_nca_v7,
    format_output,
    aggregate_verdict,
)

# ── best_fixed configuration (identical to v8 medium) ───────────────────────

BEST_FIXED_CONFIG = {
    "models": ["qwen2.5:7b", "llama3:latest", "mistral:7b"],
    "agree": [30, 80, 80],
    "steps": 3,
    "role": "fixed",
}

META_MODEL = "qwen2.5:7b"


# ── MetaAgent ───────────────────────────────────────────────────────────────

class MetaAgent:
    """
    Aggregation agent that reviews 3 nodes' outputs on split decisions.
    Unanimous decisions bypass the MetaAgent entirely.
    """

    def __init__(self, model: str = META_MODEL):
        self.model = model

    def aggregate(
        self,
        task_input: str,
        node_outputs: list[dict],
    ) -> dict:
        """
        Parameters
        ----------
        task_input : str
            The original task text.
        node_outputs : list[dict]
            Three dicts with keys: decision, confidence, reasoning.

        Returns
        -------
        dict with: final_label, meta_intervened, meta_reasoning,
                   vote_distribution
        """
        votes = [o.get("decision", "UNKNOWN") for o in node_outputs]
        vote_dist = {
            "CORRECT": votes.count("CORRECT"),
            "INCORRECT": votes.count("INCORRECT"),
        }

        # Unanimous -> no intervention
        if vote_dist["CORRECT"] == 3 or vote_dist["INCORRECT"] == 3:
            return {
                "final_label": votes[0],
                "meta_intervened": False,
                "meta_reasoning": "unanimous",
                "vote_distribution": vote_dist,
            }

        # Split -> MetaAgent decides
        prompt = self._build_prompt(task_input, node_outputs, vote_dist)
        response = call_llm(self.model, prompt)
        final_label = response.get("decision", "UNKNOWN")
        # Normalize
        if final_label not in ("CORRECT", "INCORRECT"):
            # Fallback to majority
            final_label = max(vote_dist, key=vote_dist.get)

        return {
            "final_label": final_label,
            "meta_intervened": True,
            "meta_reasoning": response.get("reasoning", str(response)),
            "vote_distribution": vote_dist,
        }

    def _build_prompt(self, task_input: str, node_outputs: list[dict],
                      vote_dist: dict) -> str:
        nodes_summary = "\n".join([
            f"Node {i} ({['Solver','Verifier','Critic'][i]}): "
            f"{o.get('decision','UNKNOWN')} "
            f"(confidence: {float(o.get('confidence', 0.5)):.2f})\n"
            f"  Reasoning: {str(o.get('reasoning',''))[:300]}"
            for i, o in enumerate(node_outputs)
        ])
        return f"""You are a meta-judge reviewing three agents' responses to a task.

Task: {task_input}

Agent responses:
{nodes_summary}

Vote distribution: {vote_dist['CORRECT']} CORRECT, {vote_dist['INCORRECT']} INCORRECT

The agents disagree. Review their reasoning carefully.
Choose the answer with the strongest logical justification.
Do NOT simply follow the majority - evaluate the reasoning quality.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CORRECT" or "INCORRECT",
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief justification for your choice"
}}"""


# ── Main runner ─────────────────────────────────────────────────────────────

_meta_agent = MetaAgent()


def run_v9a(task_input: str) -> dict:
    """Run best_fixed NCA + MetaAgent aggregation.

    Returns full result dict with MetaAgent metadata.
    """
    # Step 1: Run standard best_fixed
    nca_result = run_nca_v7(
        task_input,
        BEST_FIXED_CONFIG["models"],
        BEST_FIXED_CONFIG["agree"],
        BEST_FIXED_CONFIG["steps"],
        BEST_FIXED_CONFIG["role"],
    )

    # Step 2: Extract last step's node outputs (final opinions)
    last_step = nca_result["steps"][-1]
    node_outputs = [
        last_step["solver"]["output"],
        last_step["verifier"]["output"],
        last_step["critic"]["output"],
    ]

    # Step 3: MetaAgent aggregation (intervenes only on split)
    meta_result = _meta_agent.aggregate(task_input, node_outputs)

    # Step 4: Compute pre-meta majority for comparison
    pre_meta_majority = aggregate_verdict(node_outputs)

    return {
        **nca_result,
        "pattern_used": "best_fixed_meta",
        # MetaAgent fields
        "final_verdict": meta_result["final_label"],
        "meta_intervened": meta_result["meta_intervened"],
        "meta_reasoning": meta_result["meta_reasoning"],
        "vote_distribution": meta_result["vote_distribution"],
        "pre_meta_majority": pre_meta_majority,
    }
