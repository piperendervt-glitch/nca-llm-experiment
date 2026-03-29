"""
nca_network_h1.py

Hypothesis 1: v5's best combo (qwen2.5:7b + llama3.2:3b + mistral:7b)
with confidence-weighted voting and 5 NCA update steps.

Same NCA logic as v5 but with 5 steps instead of 3.
"""

import json
from concurrent.futures import ThreadPoolExecutor

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
NUM_NODES = 3
NUM_STEPS = 5
MODELS = ["qwen2.5:7b", "llama3.2:3b", "mistral:7b"]

_client = httpx.Client(timeout=120.0)


def call_llm(model: str, prompt: str) -> dict:
    response = _client.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
    )
    response.raise_for_status()
    raw = response.json()["response"].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"decision": "UNKNOWN", "confidence": 0.5, "reasoning": raw}


def initial_response(node_id: int, model: str, task_input: str) -> dict:
    prompt = f"""You are Node {node_id} in a 3-node reasoning network.
Task: Detect any logical contradiction in the following statements.
{task_input}

Evaluate the statements on their own merits. Only conclude CONTRADICTION if there is a clear logical impossibility between the world rule and the statement. Conclude CONSISTENT if the statement logically follows from or does not contradict the world rule.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CONSISTENT" or "CONTRADICTION",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences of logical justification"
}}"""
    return call_llm(model, prompt)


def format_neighbor(label: str, output: dict) -> str:
    decision = output.get("decision", "UNKNOWN")
    confidence = output.get("confidence", 0.5)
    reasoning = output.get("reasoning", "")
    return f"{label} neighbor: {decision} (confidence: {confidence}) - {reasoning}"


def nca_update(node_id: int, model: str, task_input: str, neighbor_outputs: list[dict]) -> dict:
    left = neighbor_outputs[0]
    right = neighbor_outputs[1]

    left_decision = left.get("decision", "UNKNOWN")
    right_decision = right.get("decision", "UNKNOWN")

    left_info = format_neighbor("Left", left)
    right_info = format_neighbor("Right", right)

    neighbors_agree = (left_decision == right_decision and left_decision in ("CONSISTENT", "CONTRADICTION"))

    if neighbors_agree:
        agreed_decision = left_decision
        prompt = f"""You are Node {node_id} in a 3-node reasoning network.
Task: Detect any logical contradiction in the following statements.
{task_input}

Your neighbors' previous states:
- {left_info}
- {right_info}

Your neighbors both agreed on {agreed_decision}. Before you decide, consider:
- What evidence would support the OPPOSITE conclusion?
- Is the agreement based on strong reasoning or just convergence?
After considering both sides, give your final judgment.

Important: Give more weight to neighbors with higher confidence. A neighbor with low confidence should have less influence on your decision.
Evaluate the statements on their own merits. Do NOT follow groupthink. Independent reasoning is required.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CONSISTENT" or "CONTRADICTION",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences explaining your judgment, including whether you agree/disagree with neighbors"
}}"""
    else:
        prompt = f"""You are Node {node_id} in a 3-node reasoning network.
Task: Detect any logical contradiction in the following statements.
{task_input}

Your neighbors' previous states:
- {left_info}
- {right_info}

Your neighbors disagree. Carefully evaluate both perspectives:
- Give more weight to the neighbor with higher confidence. A neighbor with low confidence should have less influence on your decision.
- Respect your own previous judgment. Do NOT change your answer unless a neighbor provides clearly new evidence or reasoning.
- Critically evaluate your neighbors' reasoning. Clearly state why you agree or disagree.
- Evaluate the statements on their own merits.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CONSISTENT" or "CONTRADICTION",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences explaining your judgment, including whether you agree/disagree with neighbors"
}}"""
    return call_llm(model, prompt)


def get_neighbors(node_id: int) -> tuple[int, int]:
    left = (node_id - 1) % NUM_NODES
    right = (node_id + 1) % NUM_NODES
    return left, right


def aggregate_verdict(outputs: list[dict]) -> str:
    scores = {"CONSISTENT": 0.0, "CONTRADICTION": 0.0}
    for output in outputs:
        decision = output.get("decision", "UNKNOWN")
        confidence = float(output.get("confidence", 0.5))
        if decision in scores:
            scores[decision] += confidence
    if scores["CONSISTENT"] == scores["CONTRADICTION"]:
        return "CONTRADICTION"
    return max(scores, key=scores.get)


def run_nca_h1(task_input: str) -> dict:
    """Run hypothesis 1: v5 best combo with 5 NCA steps + confidence-weighted voting."""
    # Step 0: initial responses (parallel)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(initial_response, i, MODELS[i], task_input) for i in range(NUM_NODES)]
        current_outputs = [f.result() for f in futures]
    steps = [{"step": 0, "outputs": list(current_outputs)}]

    # NCA update loop (parallel per step)
    for step in range(1, NUM_STEPS + 1):
        prev_outputs = list(current_outputs)

        def _update(node_id):
            left, right = get_neighbors(node_id)
            return nca_update(node_id, MODELS[node_id], task_input, [prev_outputs[left], prev_outputs[right]])

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(_update, nid) for nid in range(NUM_NODES)]
            current_outputs = [f.result() for f in futures]
        steps.append({"step": step, "outputs": list(current_outputs)})

    final_verdict = aggregate_verdict(current_outputs)

    return {
        "task_input": task_input,
        "models": MODELS,
        "steps": steps,
        "final_verdict": final_verdict,
        "num_steps": NUM_STEPS,
    }
