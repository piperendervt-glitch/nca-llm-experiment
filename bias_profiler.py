"""
bias_profiler.py
各モデルの単体バイアスを測定する。NCA v5 のモデル選定に使用。
"""

import sys
import json
import time
from pathlib import Path

import requests

# sdnd-proof の src を参照
sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")
from task_generator import generate_tasks

OLLAMA_URL = "http://localhost:11434/api/generate"
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

MODELS = ["qwen2.5:3b", "llama3.2:3b", "gemma2:2b"]


def build_prompt(world_rule: str, question: str) -> str:
    return (
        f"World rule: {world_rule}\n"
        f"Statement: {question}\n\n"
        f"Does this statement contradict the world rule?\n"
        f"Answer with exactly one word: CONSISTENT or CONTRADICTION."
    )


def call_ollama(model: str, prompt: str) -> str:
    resp = requests.post(OLLAMA_URL, json={
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 20},
    }, timeout=120)
    resp.raise_for_status()
    return resp.json()["response"].strip()


def parse_answer(raw: str) -> str:
    """Extract CONSISTENT or CONTRADICTION from raw response."""
    upper = raw.upper()
    if "CONTRADICTION" in upper:
        return "CONTRADICTION"
    if "CONSISTENT" in upper:
        return "CONSISTENT"
    return "UNKNOWN"


def run_model(model: str):
    tasks = generate_tasks()
    safe_name = model.replace(":", "_").replace(".", "_")
    out_path = RESULTS_DIR / f"bias_profile_{safe_name}.jsonl"

    print(f"\n{'='*60}")
    print(f"  Running bias profile: {model}  ({len(tasks)} tasks)")
    print(f"{'='*60}")

    results = []
    correct = 0

    for i, task in enumerate(tasks):
        prompt = build_prompt(task.world_rule, task.question)
        raw = call_ollama(model, prompt)
        predicted = parse_answer(raw)

        # label=True means CONSISTENT, label=False means CONTRADICTION
        expected = "CONSISTENT" if task.label else "CONTRADICTION"
        is_correct = predicted == expected

        if is_correct:
            correct += 1

        record = {
            "task_id": task.task_id,
            "world_rule": task.world_rule,
            "question": task.question,
            "expected": expected,
            "predicted": predicted,
            "raw_response": raw,
            "correct": is_correct,
        }
        results.append(record)

        status = "OK" if is_correct else "XX"
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1:3d}/100] acc={correct/(i+1)*100:5.1f}%  last: {status} pred={predicted} exp={expected}")

    # Save results
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"  Final accuracy: {correct}/{len(tasks)} = {correct/len(tasks)*100:.1f}%")
    print(f"  Saved to {out_path}")
    return results


def print_comparison():
    print(f"\n{'='*80}")
    print("  BIAS PROFILE COMPARISON")
    print(f"{'='*80}")
    print(f"{'Model':<16}| {'Overall':>8} | {'CONSISTENT Acc':>15} | {'CONTRADICTION Acc':>18} | {'CONTRADICTION bias':>20}")
    print("-" * 86)

    for model in MODELS:
        safe_name = model.replace(":", "_").replace(".", "_")
        path = RESULTS_DIR / f"bias_profile_{safe_name}.jsonl"
        if not path.exists():
            print(f"{model:<16}|  (no data)")
            continue

        with open(path, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]

        total = len(records)
        correct = sum(1 for r in records if r["correct"])

        cons_records = [r for r in records if r["expected"] == "CONSISTENT"]
        cons_correct = sum(1 for r in cons_records if r["correct"])

        contr_records = [r for r in records if r["expected"] == "CONTRADICTION"]
        contr_correct = sum(1 for r in contr_records if r["correct"])

        contr_predicted = sum(1 for r in records if r["predicted"] == "CONTRADICTION")

        overall = correct / total * 100 if total else 0
        cons_acc = cons_correct / len(cons_records) * 100 if cons_records else 0
        contr_acc = contr_correct / len(contr_records) * 100 if contr_records else 0

        print(
            f"{model:<16}|  {overall:5.1f}%  |"
            f"     {cons_acc:5.1f}%      |"
            f"      {contr_acc:5.1f}%        |"
            f"  {contr_predicted:2d}/100 predicted CONTRADICTION"
        )

    print()


if __name__ == "__main__":
    start = time.time()

    for model in MODELS:
        run_model(model)

    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.1f}s")

    print_comparison()
