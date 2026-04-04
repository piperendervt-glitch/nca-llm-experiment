"""
run_v11_ab.py

v11 Phase 1: System A (baseline) and System B (code aggregation).

System A: Full NCA-LLM (best_fixed, 3 steps, Solver/Verifier/Critic)
System B: Same as A but final aggregation by Python Counter instead of
          confidence-weighted scoring.

Both share the same task set (350 tasks, same as v9).
"""

import json
import sys
import time
from collections import Counter
from pathlib import Path

# Task generators
sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")
from task_generator import generate_tasks as generate_world_consistency_tasks
from math_task_generator import generate_math_tasks
from middle_school_task_generator import generate_middle_school_tasks
from high_school_task_generator import generate_high_school_tasks
from nca_network_v7 import run_nca_v7

# ── Config ────────────────────────────────────────────────────────────────────

BEST_FIXED = {
    "models": ["qwen2.5:7b", "llama3:latest", "mistral:7b"],
    "agree": [30, 80, 80],
    "steps": 3,
    "role": "fixed",
}

RESULTS_DIR = Path("results/v11")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_A_PATH = RESULTS_DIR / "system_a_results.jsonl"
SYSTEM_B_PATH = RESULTS_DIR / "system_b_results.jsonl"


# ── Helpers ───────────────────────────────────────────────────────────────────

def verdict_matches(verdict: str, label: bool) -> bool:
    if verdict in ("CORRECT", "CONSISTENT"):
        return label is True
    elif verdict in ("INCORRECT", "CONTRADICTION"):
        return label is False
    return False


def load_all_tasks() -> list[dict]:
    tasks = []

    wc_tasks = generate_world_consistency_tasks()
    for t in wc_tasks:
        tasks.append({
            "task_id": f"wc_{t.task_id}",
            "task_set": "world_consistency",
            "task_type": "world_consistency",
            "question": t.question,
            "world_rule": t.world_rule,
            "label": t.label,
            "task_input": f"World rule: {t.world_rule}\nStatement: {t.question}",
        })

    elem_tasks = generate_math_tasks()
    for t in elem_tasks:
        tasks.append({
            "task_id": f"elem_{t.task_id}",
            "task_set": "math_elementary",
            "task_type": t.task_type,
            "question": t.question,
            "world_rule": t.world_rule,
            "label": t.label,
            "task_input": f"Rule: {t.world_rule}\nStatement: {t.question}",
        })

    mid_tasks = generate_middle_school_tasks()
    for t in mid_tasks:
        tasks.append({
            "task_id": f"mid_{t.task_id}",
            "task_set": "math_middle",
            "task_type": t.task_type,
            "question": t.question,
            "world_rule": t.world_rule,
            "label": t.label,
            "task_input": f"Rule: {t.world_rule}\nStatement: {t.question}",
        })

    high_tasks = generate_high_school_tasks()
    for t in high_tasks:
        tasks.append({
            "task_id": f"high_{t.task_id}",
            "task_set": "math_high",
            "task_type": t.task_type,
            "question": t.question,
            "world_rule": t.world_rule,
            "label": t.label,
            "task_input": f"Rule: {t.world_rule}\nStatement: {t.question}",
        })

    return tasks


def load_completed(path: Path) -> set[str]:
    """Load already-completed task IDs for resume support."""
    completed = set()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    completed.add(r["task_id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    return completed


def extract_votes(nca_result: dict) -> tuple[list[str], dict[str, int]]:
    """Extract votes from last step of NCA result."""
    last_step = nca_result["steps"][-1]
    node_outputs = [
        last_step["solver"]["output"],
        last_step["verifier"]["output"],
        last_step["critic"]["output"],
    ]
    votes = [o.get("decision", "UNKNOWN") for o in node_outputs]
    vote_dist = {
        "CORRECT": votes.count("CORRECT"),
        "INCORRECT": votes.count("INCORRECT"),
    }
    return votes, vote_dist


def code_majority(votes: list[str]) -> str:
    """System B aggregation: simple Counter majority."""
    filtered = [v for v in votes if v in ("CORRECT", "INCORRECT")]
    if not filtered:
        return "UNKNOWN"
    return Counter(filtered).most_common(1)[0][0]


# ── Run one system ────────────────────────────────────────────────────────────

def run_system(system_name: str, results_path: Path, tasks: list[dict],
               use_code_aggregation: bool):
    """Run System A or B on all tasks."""

    completed = load_completed(results_path)
    remaining = [t for t in tasks if t["task_id"] not in completed]

    if not remaining:
        print(f"[{system_name}] All {len(tasks)} tasks already completed. Skipping.")
        return

    total = len(tasks)
    done = len(completed)
    print(f"[{system_name}] {done}/{total} done, {len(remaining)} remaining.")

    mode = "a" if completed else "w"
    correct_count = done  # approximate (won't be exact on resume, but fine for progress)

    with open(results_path, mode, encoding="utf-8") as f_out:
        for i, task in enumerate(remaining):
            t0 = time.time()
            try:
                nca_result = run_nca_v7(
                    task["task_input"],
                    BEST_FIXED["models"],
                    BEST_FIXED["agree"],
                    BEST_FIXED["steps"],
                    BEST_FIXED["role"],
                )
                votes, vote_dist = extract_votes(nca_result)

                if use_code_aggregation:
                    # System B: Python Counter majority
                    verdict = code_majority(votes)
                else:
                    # System A: confidence-weighted aggregation (from nca_network_v7)
                    verdict = nca_result["final_verdict"]

            except Exception as e:
                verdict = "ERROR"
                vote_dist = {"CORRECT": 0, "INCORRECT": 0}
                votes = []
                nca_result = {"steps": []}
                print(f"  ERROR on {task['task_id']}: {e}")

            elapsed = time.time() - t0
            is_correct = verdict_matches(verdict, task["label"])

            record = {
                "task_id": task["task_id"],
                "task_set": task["task_set"],
                "task_type": task["task_type"],
                "question": task["question"],
                "label": task["label"],
                "prediction": verdict,
                "is_correct": is_correct,
                "vote_distribution": vote_dist,
                "is_unanimous": any(v == 3 for v in vote_dist.values()),
                "elapsed_sec": round(elapsed, 2),
                "steps": nca_result["steps"],
            }

            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            f_out.flush()

            done += 1
            if is_correct:
                correct_count += 1

            # Progress every 50 tasks
            if done % 50 == 0 or done == total:
                acc = correct_count / done * 100 if done > 0 else 0
                print(f"  [{system_name}] {done}/{total} tasks "
                      f"({acc:.1f}% acc so far) "
                      f"last={elapsed:.1f}s")

    print(f"[{system_name}] Complete. Results saved to {results_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("v11 Phase 1: System A & System B")
    print("=" * 60)

    print("\nLoading 350 tasks...")
    tasks = load_all_tasks()
    print(f"  Loaded {len(tasks)} tasks")
    from collections import Counter as C
    sets = C(t["task_set"] for t in tasks)
    for s in sorted(sets):
        print(f"    {s}: {sets[s]}")

    # System A: baseline (confidence-weighted aggregation)
    print("\n" + "=" * 60)
    print("System A: NCA-LLM baseline (confidence-weighted aggregation)")
    print("=" * 60)
    run_system("System A", SYSTEM_A_PATH, tasks, use_code_aggregation=False)

    # System B: code aggregation
    print("\n" + "=" * 60)
    print("System B: NCA-LLM + code aggregation (Counter majority)")
    print("=" * 60)
    run_system("System B", SYSTEM_B_PATH, tasks, use_code_aggregation=True)

    print("\n" + "=" * 60)
    print("v11 Phase 1 complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
