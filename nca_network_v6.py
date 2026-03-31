"""
nca_network_v6.py

NCA v6: Random sampling over model combos, agreement intensity, and step count.
Each node has its own agreement_pct controlling how much it follows neighbor consensus.
"""

import json
from concurrent.futures import ThreadPoolExecutor

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
NUM_NODES = 3

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


def agreement_instruction(agreement_pct: int) -> str:
    if agreement_pct >= 50:
        return (
            f"You should agree with your neighbors' answers approximately {agreement_pct}% of the time.\n"
            f"If your neighbors strongly agree on an answer, consider following their consensus."
        )
    else:
        return (
            f"You should agree with your neighbors' answers approximately {agreement_pct}% of the time.\n"
            f"If your neighbors strongly agree on an answer, consider maintaining your independent judgment."
        )


def nca_update(node_id: int, model: str, task_input: str,
               neighbor_outputs: list[dict], agreement_pct: int) -> dict:
    left = neighbor_outputs[0]
    right = neighbor_outputs[1]

    left_info = format_neighbor("Left", left)
    right_info = format_neighbor("Right", right)
    agree_instr = agreement_instruction(agreement_pct)

    prompt = f"""You are Node {node_id} in a 3-node reasoning network.
Task: Detect any logical contradiction in the following statements.
{task_input}

Your neighbors' previous states:
- {left_info}
- {right_info}

{agree_instr}

Give more weight to neighbors with higher confidence. Evaluate the statements on their own merits.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CONSISTENT" or "CONTRADICTION",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences explaining your judgment"
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


def classify_groupthink(outputs: list[dict]) -> str:
    verdicts = [o.get("decision", "UNKNOWN") if isinstance(o, dict) else "UNKNOWN" for o in outputs]
    if all(v == "CONTRADICTION" for v in verdicts):
        return "all_contradiction"
    elif all(v == "CONSISTENT" for v in verdicts):
        return "all_consistent"
    return "split"


def run_nca_v6(
    task_input: str,
    model_a: str,
    model_b: str,
    model_c: str,
    agreement_pct: list[int],
    num_steps: int,
) -> dict:
    models = [model_a, model_b, model_c]

    # Step 0: initial responses (parallel)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(initial_response, i, models[i], task_input) for i in range(NUM_NODES)]
        current_outputs = [f.result() for f in futures]
    steps = [{"step": 0, "outputs": list(current_outputs)}]

    # NCA update loop
    for step in range(1, num_steps + 1):
        prev_outputs = list(current_outputs)

        def _update(node_id):
            left, right = get_neighbors(node_id)
            return nca_update(
                node_id, models[node_id], task_input,
                [prev_outputs[left], prev_outputs[right]],
                agreement_pct[node_id],
            )

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(_update, nid) for nid in range(NUM_NODES)]
            current_outputs = [f.result() for f in futures]
        steps.append({"step": step, "outputs": list(current_outputs)})

    final_verdict = aggregate_verdict(current_outputs)
    groupthink = classify_groupthink(current_outputs)

    return {
        "task_input": task_input,
        "models": models,
        "agreement_pct": agreement_pct,
        "num_steps": num_steps,
        "steps": steps,
        "final_verdict": final_verdict,
        "groupthink": groupthink,
    }
