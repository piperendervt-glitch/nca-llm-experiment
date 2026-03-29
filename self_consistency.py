"""
self_consistency.py

Baseline: Same 3 models as hypothesis 1, but each answers independently.
No NCA updates, no neighbor influence, no iteration.
Simple majority vote on the 3 independent answers.
"""

import json
from concurrent.futures import ThreadPoolExecutor

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
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


def independent_response(model: str, task_input: str) -> dict:
    prompt = f"""Task: Detect any logical contradiction in the following statements.
{task_input}

Evaluate the statements on their own merits. Only conclude CONTRADICTION if there is a clear logical impossibility between the world rule and the statement. Conclude CONSISTENT if the statement logically follows from or does not contradict the world rule.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CONSISTENT" or "CONTRADICTION",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences of logical justification"
}}"""
    return call_llm(model, prompt)


def aggregate_majority(outputs: list[dict]) -> str:
    counts = {"CONSISTENT": 0, "CONTRADICTION": 0}
    for output in outputs:
        decision = output.get("decision", "UNKNOWN")
        if decision in counts:
            counts[decision] += 1
    if counts["CONSISTENT"] > counts["CONTRADICTION"]:
        return "CONSISTENT"
    elif counts["CONTRADICTION"] > counts["CONSISTENT"]:
        return "CONTRADICTION"
    return "CONTRADICTION"  # tie-break


def run_self_consistency(task_input: str) -> dict:
    """Run all 3 models independently in parallel, majority vote."""
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(independent_response, model, task_input) for model in MODELS]
        outputs = [f.result() for f in futures]

    final_verdict = aggregate_majority(outputs)

    return {
        "task_input": task_input,
        "models": MODELS,
        "outputs": outputs,
        "final_verdict": final_verdict,
    }
