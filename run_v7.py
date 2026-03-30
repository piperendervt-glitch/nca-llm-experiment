"""
run_v7.py

Run NCA v7: Math tasks with role-division NCA.
4 patterns (best/balanced x fixed/rotating) + single agent baseline.
"""

import json
import time
from pathlib import Path

from math_task_generator import generate_math_tasks, Task
from nca_network_v7 import run_nca_v7, run_single_agent

# ── v6 best and balanced settings ────────────────────────────────────────────

BEST_MODELS = ["qwen2.5:7b", "llama3:latest", "mistral:7b"]
BEST_AGREE = [30, 80, 80]
BEST_STEPS = 3

BALANCED_MODELS = ["mistral:7b", "llama3:latest", "llama3.1:8b"]
BALANCED_AGREE = [80, 70, 10]
BALANCED_STEPS = 2

PATTERNS = [
    {
        "name": "best_fixed",
        "models": BEST_MODELS,
        "agree": BEST_AGREE,
        "steps": BEST_STEPS,
        "role": "fixed",
    },
    {
        "name": "best_rotating",
        "models": BEST_MODELS,
        "agree": BEST_AGREE,
        "steps": BEST_STEPS,
        "role": "rotating",
    },
    {
        "name": "balanced_fixed",
        "models": BALANCED_MODELS,
        "agree": BALANCED_AGREE,
        "steps": BALANCED_STEPS,
        "role": "fixed",
    },
    {
        "name": "balanced_rotating",
        "models": BALANCED_MODELS,
        "agree": BALANCED_AGREE,
        "steps": BALANCED_STEPS,
        "role": "rotating",
    },
    {
        "name": "single_agent",
        "models": ["qwen2.5:7b"],
        "agree": [100],
        "steps": 1,
        "role": "none",
    },
]

RESULTS_DIR = Path("results/v7")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = RESULTS_DIR / "v7_summary.jsonl"


def task_to_input(task: Task) -> str:
    """Format task for the NCA prompt."""
    return f"Rule: {task.world_rule}\nStatement: {task.question}"


def verdict_matches(verdict: str, label: bool) -> bool:
    """Check if the NCA verdict matches the ground truth label.

    label=True means the statement is correct/consistent.
    label=False means the statement is incorrect/contradictory.
    """
    if verdict == "CORRECT":
        return label is True
    elif verdict == "INCORRECT":
        return label is False
    # Also handle CONSISTENT/CONTRADICTION from models that use v6 vocabulary
    elif verdict == "CONSISTENT":
        return label is True
    elif verdict == "CONTRADICTION":
        return label is False
    return False


def compute_stats(results: list[dict]) -> dict:
    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])

    correct_label = [r for r in results if r["label"] is True]
    incorrect_label = [r for r in results if r["label"] is False]
    correct_acc = sum(1 for r in correct_label if r["is_correct"]) / len(correct_label) if correct_label else 0
    incorrect_acc = sum(1 for r in incorrect_label if r["is_correct"]) / len(incorrect_label) if incorrect_label else 0

    all_correct = sum(1 for r in results if r.get("groupthink") == "all_correct")
    all_incorrect = sum(1 for r in results if r.get("groupthink") == "all_incorrect")
    split = sum(1 for r in results if r.get("groupthink") == "split")
    single = sum(1 for r in results if r.get("groupthink") == "single")

    # Per task type
    by_type = {}
    for task_type in ["calculation", "logical", "word_problem", "sequence"]:
        type_results = [r for r in results if r.get("task_type") == task_type]
        if type_results:
            by_type[task_type] = round(sum(1 for r in type_results if r["is_correct"]) / len(type_results), 2)

    return {
        "overall": round(correct / total, 2) if total else 0,
        "correct_acc": round(correct_acc, 2),
        "incorrect_acc": round(incorrect_acc, 2),
        "groupthink_all_correct": all_correct,
        "groupthink_all_incorrect": all_incorrect,
        "split": split,
        "single": single,
        "by_type": by_type,
    }


def run_pattern(pattern: dict, tasks: list[Task]) -> dict:
    """Run one pattern across all tasks."""
    name = pattern["name"]
    out_path = RESULTS_DIR / f"v7_{name}_results.jsonl"

    # Resume support
    existing = []
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
        if len(existing) >= len(tasks):
            print(f"  [{name}] Already complete ({len(existing)} tasks)")
            return compute_stats(existing)

    start_idx = len(existing)
    results = list(existing)
    mode = "a" if start_idx > 0 else "w"

    with open(out_path, mode, encoding="utf-8") as f:
        for i, task in enumerate(tasks):
            if i < start_idx:
                continue

            task_input = task_to_input(task)
            t0 = time.time()

            try:
                if pattern["role"] == "none":
                    nca_result = run_single_agent(task_input, pattern["models"][0])
                else:
                    nca_result = run_nca_v7(
                        task_input,
                        pattern["models"],
                        pattern["agree"],
                        pattern["steps"],
                        pattern["role"],
                    )
                verdict = nca_result["final_verdict"]
                groupthink = nca_result["groupthink"]
                steps = nca_result.get("steps", [])
            except Exception as e:
                verdict = f"ERROR: {e}"
                groupthink = "unknown"
                steps = []

            elapsed = time.time() - t0
            is_correct = verdict_matches(verdict, task.label)

            record = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "question": task.question,
                "label": task.label,
                "prediction": verdict,
                "is_correct": is_correct,
                "groupthink": groupthink,
                "elapsed_sec": round(elapsed, 2),
                "steps": steps,
            }
            results.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            status = "OK" if is_correct else "NG"
            print(f"  [{name}] {i+1:3d}/{len(tasks)} {status} {verdict:12s} ({elapsed:.1f}s) {task.question[:50]}")

    return compute_stats(results)


def print_summary(summaries: list[dict]):
    """Print final comparison table."""
    print(f"\n{'='*90}")
    print(f"  NCA v7: Math Tasks x Role-Division (4 patterns + baseline)")
    print(f"{'='*90}")
    print(f"{'Pattern':<24} | {'Overall':>8} | {'CORRECT':>8} | {'INCORRECT':>9} | {'Calc':>5} | {'Logic':>5} | {'Word':>5} | {'Seq':>5}")
    print("-" * 90)
    for s in summaries:
        by_type = s.get("by_type", {})
        print(
            f"{s['name']:<24} | {s['overall']:>7.0%} | {s['correct_acc']:>7.0%} | {s['incorrect_acc']:>8.0%} "
            f"| {by_type.get('calculation', 0):>5.0%} | {by_type.get('logical', 0):>5.0%} "
            f"| {by_type.get('word_problem', 0):>5.0%} | {by_type.get('sequence', 0):>5.0%}"
        )
    print(f"{'='*90}")


def main():
    tasks = generate_math_tasks()
    print(f"Tasks: {len(tasks)} (CORRECT: {sum(1 for t in tasks if t.label)}, "
          f"INCORRECT: {sum(1 for t in tasks if not t.label)})")

    summaries = []
    total_start = time.time()

    for pattern in PATTERNS:
        name = pattern["name"]
        print(f"\n--- Pattern: {name} ---")
        print(f"  Models: {pattern['models']}")
        print(f"  Agreement: {pattern['agree']}, Steps: {pattern['steps']}, Role: {pattern['role']}")

        t0 = time.time()
        stats = run_pattern(pattern, tasks)
        elapsed = time.time() - t0

        entry = {
            "name": name,
            **pattern,
            **stats,
            "elapsed_sec": round(elapsed, 1),
        }
        summaries.append(entry)

        with open(SUMMARY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"  => Overall: {stats['overall']:.0%}  CORRECT: {stats['correct_acc']:.0%}  "
              f"INCORRECT: {stats['incorrect_acc']:.0%}  ({elapsed:.0f}s)")

    total_elapsed = time.time() - total_start
    print(f"\nAll patterns complete in {total_elapsed:.0f}s ({total_elapsed/3600:.1f}h)")

    print_summary(summaries)


if __name__ == "__main__":
    main()
