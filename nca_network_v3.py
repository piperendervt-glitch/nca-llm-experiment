"""
nca_network_v3.py

NCA v3: Devil's Advocate + Balanced Prompts
  - Remove bias warnings, use neutral language
  - Devil's advocate when all neighbors agree
  - Balanced prompt when neighbors disagree

依存: httpx
モデル: Ollama qwen2.5:3b (http://localhost:11434)
"""

import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"
NUM_NODES = 3
NUM_STEPS = 5


def call_llm(prompt: str) -> dict:
    """OllamaにJSON形式で出力させる。戻り値はdict。"""
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
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


def initial_response(node_id: int, task_input: str) -> dict:
    """ステップ0の初期回答。中立的なプロンプト。"""
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
    return call_llm(prompt)


def nca_update(node_id: int, task_input: str, neighbor_outputs: list[dict]) -> dict:
    """NCA更新ステップ。隣人が一致→Devil's Advocate、不一致→バランスプロンプト。"""
    left = neighbor_outputs[0]
    right = neighbor_outputs[1]

    left_decision = left.get("decision", "UNKNOWN")
    right_decision = right.get("decision", "UNKNOWN")

    left_str = json.dumps(left, ensure_ascii=False)
    right_str = json.dumps(right, ensure_ascii=False)

    # Check if both neighbors agree
    neighbors_agree = (left_decision == right_decision and left_decision in ("CONSISTENT", "CONTRADICTION"))

    if neighbors_agree:
        agreed_decision = left_decision
        prompt = f"""You are Node {node_id} in a 3-node reasoning network.
Task: Detect any logical contradiction in the following statements.
{task_input}

Your neighbors' previous states:
- Left neighbor: {left_str}
- Right neighbor: {right_str}

Your neighbors both agreed on {agreed_decision}. Before you decide, consider:
- What evidence would support the OPPOSITE conclusion?
- Is the agreement based on strong reasoning or just convergence?
After considering both sides, give your final judgment.

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
- Left neighbor: {left_str}
- Right neighbor: {right_str}

Your neighbors disagree. Carefully evaluate both perspectives:
- Respect your own previous judgment. Do NOT change your answer unless a neighbor provides clearly new evidence or reasoning.
- Critically evaluate your neighbors' reasoning. Clearly state why you agree or disagree.
- Evaluate the statements on their own merits.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CONSISTENT" or "CONTRADICTION",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences explaining your judgment, including whether you agree/disagree with neighbors"
}}"""
    return call_llm(prompt)


def get_neighbors(node_id: int) -> tuple[int, int]:
    """リング状の左隣・右隣ノードIDを返す。"""
    left = (node_id - 1) % NUM_NODES
    right = (node_id + 1) % NUM_NODES
    return left, right


def aggregate_verdict(outputs: list[dict]) -> str:
    """confidence加重多数決で最終判定。"""
    scores = {"CONSISTENT": 0.0, "CONTRADICTION": 0.0}
    for output in outputs:
        decision = output.get("decision", "UNKNOWN")
        confidence = float(output.get("confidence", 0.5))
        if decision in scores:
            scores[decision] += confidence
    if scores["CONSISTENT"] == scores["CONTRADICTION"]:
        return "CONTRADICTION"
    return max(scores, key=scores.get)


def run_nca_network(task_input: str) -> dict:
    """
    メイン実行関数。
    3ノードがNCA的更新ルールで回答を更新し、最終判定を返す。
    """
    # ステップ0: 初期回答
    print(f"  Step 0...")
    current_outputs = [initial_response(i, task_input) for i in range(NUM_NODES)]
    steps = [{"step": 0, "outputs": list(current_outputs)}]

    # NCA更新ループ
    for step in range(1, NUM_STEPS + 1):
        print(f"  Step {step}...")
        prev_outputs = list(current_outputs)
        new_outputs = []
        for node_id in range(NUM_NODES):
            left, right = get_neighbors(node_id)
            neighbor_out = [prev_outputs[left], prev_outputs[right]]
            resp = nca_update(node_id, task_input, neighbor_out)
            new_outputs.append(resp)
        current_outputs = new_outputs
        steps.append({"step": step, "outputs": list(current_outputs)})

    final_verdict = aggregate_verdict(current_outputs)

    return {
        "task_input": task_input,
        "steps": steps,
        "final_verdict": final_verdict,
        "num_steps": NUM_STEPS,
    }


if __name__ == "__main__":
    test_cases = [
        "World rule: In this world, the sky is green.\nStatement: Looking up, the sky appeared green.",
        "World rule: In this world, the sky is green.\nStatement: Looking up, the sky appeared blue.",
        "World rule: In this world, the sun rises from west to east.\nStatement: The sun rose from the east this morning.",
    ]

    for i, task in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"Test {i+1}")
        result = run_nca_network(task)
        for step in result["steps"]:
            for node_id, out in enumerate(step["outputs"]):
                print(f"  Step {step['step']} Node {node_id}: "
                      f"{out.get('decision')} (conf={out.get('confidence', 0):.2f})")
        print(f"  Final verdict: {result['final_verdict']}")
