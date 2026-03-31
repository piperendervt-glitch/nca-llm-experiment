"""
run_v7_5.py

Run NCA v7.5: Middle school math tasks with role-division NCA.
Same 5 patterns as v7, with grade-level breakdown in output.
"""

import json
import time
from pathlib import Path

from middle_school_task_generator import generate_middle_school_tasks, Task
from nca_network_v7 import run_nca_v7, run_single_agent

# ── Same settings as v7 ─────────────────────────────────────────────────────

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

RESULTS_DIR = Path("results/v7_5")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = RESULTS_DIR / "v7_5_summary.jsonl"


def task_to_input(task: Task) -> str:
    return f"Rule: {task.world_rule}\nStatement: {task.question}"


def verdict_matches(verdict: str, label: bool) -> bool:
    if verdict == "CORRECT":
        return label is True
    elif verdict == "INCORRECT":
        return label is False
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

    # Per grade level
    by_level = {}
    for level in ["grade7", "grade8", "grade9"]:
        level_results = [r for r in results if r.get("level") == level]
        if level_results:
            by_level[level] = round(
                sum(1 for r in level_results if r["is_correct"]) / len(level_results), 2
            )

    # Per task type
    by_type = {}
    all_types = set(r.get("task_type", "") for r in results)
    for task_type in sorted(all_types):
        if task_type:
            type_results = [r for r in results if r.get("task_type") == task_type]
            if type_results:
                by_type[task_type] = round(
                    sum(1 for r in type_results if r["is_correct"]) / len(type_results), 2
                )

    return {
        "overall": round(correct / total, 2) if total else 0,
        "correct_acc": round(correct_acc, 2),
        "incorrect_acc": round(incorrect_acc, 2),
        "groupthink_all_correct": all_correct,
        "groupthink_all_incorrect": all_incorrect,
        "split": split,
        "single": single,
        "by_level": by_level,
        "by_type": by_type,
    }


def run_pattern(pattern: dict, tasks: list[Task]) -> dict:
    name = pattern["name"]
    out_path = RESULTS_DIR / f"v7_5_{name}_results.jsonl"

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
                "level": task.level,
                "difficulty": task.difficulty,
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
            print(f"  [{name}] {i+1:3d}/{len(tasks)} {status} {verdict:12s} ({elapsed:.1f}s) [{task.level}] {task.question[:45]}")

    return compute_stats(results)


def print_summary(summaries: list[dict]):
    print(f"\n{'='*100}")
    print(f"  NCA v7.5: Middle School Math Tasks x Role-Division (5 patterns)")
    print(f"{'='*100}")
    print(f"{'Pattern':<24} | {'Overall':>8} | {'Grade7':>7} | {'Grade8':>7} | {'Grade9':>7} | {'CORRECT':>8} | {'INCORRECT':>9}")
    print("-" * 100)
    for s in summaries:
        by_level = s.get("by_level", {})
        print(
            f"{s['name']:<24} | {s['overall']:>7.0%} | {by_level.get('grade7', 0):>6.0%} "
            f"| {by_level.get('grade8', 0):>6.0%} | {by_level.get('grade9', 0):>6.0%} "
            f"| {s['correct_acc']:>7.0%} | {s['incorrect_acc']:>8.0%}"
        )
    print(f"{'='*100}")

    # v7 comparison
    print(f"\nv7 (elementary) vs v7.5 (middle school) comparison:")
    v7_results = {
        "best_fixed": 0.83,
        "best_rotating": 0.81,
        "balanced_fixed": 0.68,
        "balanced_rotating": 0.80,
        "single_agent": 0.83,
    }
    for s in summaries:
        v7_val = v7_results.get(s["name"], 0)
        diff = s["overall"] - v7_val
        print(f"  {s['name']:<24}: v7={v7_val:.0%}  ->  v7.5={s['overall']:.0%}  (diff: {diff:+.0%}pp)")
    print(f"{'='*100}")


def main():
    tasks = generate_middle_school_tasks()
    correct_count = sum(1 for t in tasks if t.label)
    print(f"Tasks: {len(tasks)} (CORRECT: {correct_count}, INCORRECT: {len(tasks) - correct_count})")
    for level in ["grade7", "grade8", "grade9"]:
        level_tasks = [t for t in tasks if t.level == level]
        print(f"  {level}: {len(level_tasks)} tasks")

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

        print(f"  => Overall: {stats['overall']:.0%}  Grade7: {stats['by_level'].get('grade7', 0):.0%}  "
              f"Grade8: {stats['by_level'].get('grade8', 0):.0%}  Grade9: {stats['by_level'].get('grade9', 0):.0%}  ({elapsed:.0f}s)")

    total_elapsed = time.time() - total_start
    print(f"\nAll patterns complete in {total_elapsed:.0f}s ({total_elapsed/3600:.1f}h)")

    print_summary(summaries)


if __name__ == "__main__":
    main()
