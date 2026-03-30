"""
nca_network_v7.py

NCA v7: Role-division NCA for math tasks.
Three roles: Solver, Verifier, Critic.
Supports fixed roles and rotating roles across steps.
"""

import json
from concurrent.futures import ThreadPoolExecutor

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
NUM_NODES = 3

_client = httpx.Client(timeout=120.0)

ROLES = ["solver", "verifier", "critic"]


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


def format_output(output: dict) -> str:
    decision = output.get("decision", "UNKNOWN")
    confidence = output.get("confidence", 0.5)
    reasoning = output.get("reasoning", "")
    return f"{decision} (confidence: {confidence}) - {reasoning}"


def agreement_instruction(agreement_pct: int) -> str:
    if agreement_pct >= 50:
        return (
            f"You should agree with your teammates approximately {agreement_pct}% of the time.\n"
            f"If they strongly agree, consider following their consensus."
        )
    return (
        f"You should agree with your teammates approximately {agreement_pct}% of the time.\n"
        f"If they strongly agree, consider maintaining your independent judgment."
    )


# ── Role-specific prompts ────────────────────────────────────────────────────

def solver_prompt(task_input: str, agreement_pct: int) -> str:
    agree = agreement_instruction(agreement_pct)
    return f"""You are the Solver in a 3-node reasoning network.
Task: {task_input}

Solve this step by step. Show your work clearly.
Determine if the statement is CORRECT or INCORRECT.
{agree}

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CORRECT" or "INCORRECT",
  "confidence": 0.0 to 1.0,
  "reasoning": "Step-by-step solution in 2-3 sentences"
}}"""


def verifier_prompt(task_input: str, solver_output: dict, agreement_pct: int) -> str:
    solver_info = format_output(solver_output)
    agree = agreement_instruction(agreement_pct)
    return f"""You are the Verifier in a 3-node reasoning network.
Task: {task_input}

The Solver's answer: {solver_info}

Independently verify this answer from scratch.
Do NOT simply agree - check the math yourself.
Determine if the statement is CORRECT or INCORRECT.
{agree}

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CORRECT" or "INCORRECT",
  "confidence": 0.0 to 1.0,
  "reasoning": "Your independent verification in 2-3 sentences"
}}"""


def critic_prompt(task_input: str, solver_output: dict, verifier_output: dict,
                  agreement_pct: int) -> str:
    solver_info = format_output(solver_output)
    verifier_info = format_output(verifier_output)
    agree = agreement_instruction(agreement_pct)
    return f"""You are the Critic in a 3-node reasoning network.
Task: {task_input}

Solver's reasoning: {solver_info}
Verifier's reasoning: {verifier_info}

Critically evaluate both answers.
If they disagree, determine who is right.
If they agree but seem wrong, say so.
Determine if the statement is CORRECT or INCORRECT.
{agree}

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CORRECT" or "INCORRECT",
  "confidence": 0.0 to 1.0,
  "reasoning": "Final judgment with brief explanation"
}}"""


# ── Single agent baseline ────────────────────────────────────────────────────

def single_agent_prompt(task_input: str) -> str:
    return f"""Task: {task_input}

Solve this step by step and determine if the statement is CORRECT or INCORRECT.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CORRECT" or "INCORRECT",
  "confidence": 0.0 to 1.0,
  "reasoning": "Step-by-step solution in 2-3 sentences"
}}"""


# ── Role assignment ──────────────────────────────────────────────────────────

def get_role_assignment(step: int, mode: str) -> list[str]:
    """Return [role_for_node0, role_for_node1, role_for_node2].

    mode='fixed': always [solver, verifier, critic]
    mode='rotating': rotates each step
    """
    if mode == "fixed":
        return ["solver", "verifier", "critic"]
    # rotating: shift by step
    offset = step % NUM_NODES
    return [ROLES[(i + offset) % NUM_NODES] for i in range(NUM_NODES)]


# ── Aggregation ──────────────────────────────────────────────────────────────

def aggregate_verdict(outputs: list[dict]) -> str:
    scores = {"CORRECT": 0.0, "INCORRECT": 0.0}
    for output in outputs:
        decision = output.get("decision", "UNKNOWN")
        confidence = float(output.get("confidence", 0.5))
        if decision in scores:
            scores[decision] += confidence
    if scores["CORRECT"] == scores["INCORRECT"]:
        return "INCORRECT"
    return max(scores, key=scores.get)


def classify_groupthink(outputs: list[dict]) -> str:
    verdicts = [o.get("decision", "UNKNOWN") if isinstance(o, dict) else "UNKNOWN"
                for o in outputs]
    if all(v == "CORRECT" for v in verdicts):
        return "all_correct"
    elif all(v == "INCORRECT" for v in verdicts):
        return "all_incorrect"
    return "split"


# ── Main NCA runner ──────────────────────────────────────────────────────────

def run_nca_v7(
    task_input: str,
    models: list[str],
    agreement_pct: list[int],
    num_steps: int,
    role_mode: str,  # "fixed" or "rotating"
) -> dict:
    """Run role-division NCA.

    Each step runs sequentially: Solver -> Verifier -> Critic.
    The Verifier sees Solver output; the Critic sees both.
    """
    all_steps = []

    current_outputs = [None, None, None]

    for step in range(num_steps):
        roles = get_role_assignment(step, role_mode)

        # Find which node has which role this step
        solver_idx = roles.index("solver")
        verifier_idx = roles.index("verifier")
        critic_idx = roles.index("critic")

        # Step 1: Solver runs
        prompt_s = solver_prompt(task_input, agreement_pct[solver_idx])
        solver_out = call_llm(models[solver_idx], prompt_s)

        # Step 2: Verifier runs (sees solver output)
        prompt_v = verifier_prompt(task_input, solver_out, agreement_pct[verifier_idx])
        verifier_out = call_llm(models[verifier_idx], prompt_v)

        # Step 3: Critic runs (sees both)
        prompt_c = critic_prompt(task_input, solver_out, verifier_out,
                                 agreement_pct[critic_idx])
        critic_out = call_llm(models[critic_idx], prompt_c)

        # Store outputs in node order
        step_outputs = [None, None, None]
        step_outputs[solver_idx] = solver_out
        step_outputs[verifier_idx] = verifier_out
        step_outputs[critic_idx] = critic_out
        current_outputs = step_outputs

        all_steps.append({
            "step": step,
            "roles": roles,
            "solver": {"node": solver_idx, "model": models[solver_idx], "output": solver_out},
            "verifier": {"node": verifier_idx, "model": models[verifier_idx], "output": verifier_out},
            "critic": {"node": critic_idx, "model": models[critic_idx], "output": critic_out},
        })

    final_verdict = aggregate_verdict(current_outputs)
    groupthink = classify_groupthink(current_outputs)

    return {
        "task_input": task_input,
        "models": models,
        "agreement_pct": agreement_pct,
        "num_steps": num_steps,
        "role_mode": role_mode,
        "steps": all_steps,
        "final_verdict": final_verdict,
        "groupthink": groupthink,
    }


def run_single_agent(task_input: str, model: str) -> dict:
    """Run single agent baseline (no NCA)."""
    prompt = single_agent_prompt(task_input)
    output = call_llm(model, prompt)
    verdict = output.get("decision", "UNKNOWN")
    return {
        "task_input": task_input,
        "models": [model],
        "agreement_pct": [100],
        "num_steps": 1,
        "role_mode": "none",
        "steps": [{"step": 0, "output": output}],
        "final_verdict": verdict,
        "groupthink": "single",
    }
