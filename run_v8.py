"""
run_v8.py

Run NCA v8: Adaptive model selection across all task sets.
Combines world_consistency (100) + math_elementary (100) +
math_middle (75) + math_high (75) = 350 tasks.
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")

from task_generator import generate_tasks as generate_world_consistency_tasks
from math_task_generator import generate_math_tasks
from middle_school_task_generator import generate_middle_school_tasks
from high_school_task_generator import generate_high_school_tasks
from embedding_classifier import build_anchor_embeddings
from nca_network_v8 import run_adaptive

RESULTS_DIR = Path("results/v8")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ROUTING_LOG_PATH = RESULTS_DIR / "v8_routing_log.jsonl"
RESULTS_PATH = RESULTS_DIR / "v8_results.jsonl"
SUMMARY_PATH = RESULTS_DIR / "v8_summary.jsonl"
ANCHOR_CACHE = RESULTS_DIR / "v8_anchor_embeddings.pkl"


# ── Unified task wrapper ────────────────────────────────────────────────────

def load_all_tasks() -> list[dict]:
    """Load all 4 task sets into a unified format."""
    tasks = []

    # World consistency (100 tasks)
    wc_tasks = generate_world_consistency_tasks()
    for t in wc_tasks:
        tasks.append({
            "task_id": f"wc_{t.task_id}",
            "task_set": "world_consistency",
            "task_type": "world_consistency",
            "question": t.question,
            "world_rule": t.world_rule,
            "label": t.label,  # True = CONSISTENT, False = CONTRADICTION
            "task_input": f"World rule: {t.world_rule}\nStatement: {t.question}",
        })

    # Math elementary (100 tasks)
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

    # Math middle school (75 tasks)
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

    # Math high school (75 tasks)
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


def verdict_matches(verdict: str, label: bool) -> bool:
    """Check if verdict matches ground truth label."""
    if verdict in ("CORRECT", "CONSISTENT"):
        return label is True
    elif verdict in ("INCORRECT", "CONTRADICTION"):
        return label is False
    return False


def compute_stats(results: list[dict]) -> dict:
    """Compute accuracy stats from results."""
    total = len(results)
    if total == 0:
        return {"overall": 0, "correct_acc": 0, "incorrect_acc": 0}

    correct = sum(1 for r in results if r["is_correct"])

    correct_label = [r for r in results if r["label"] is True]
    incorrect_label = [r for r in results if r["label"] is False]
    c_acc = sum(1 for r in correct_label if r["is_correct"]) / len(correct_label) if correct_label else 0
    i_acc = sum(1 for r in incorrect_label if r["is_correct"]) / len(incorrect_label) if incorrect_label else 0

    return {
        "overall": round(correct / total, 3),
        "correct_acc": round(c_acc, 3),
        "incorrect_acc": round(i_acc, 3),
        "total": total,
        "n_correct": correct,
    }


def main():
    # ── Phase 1: Load tasks and build anchors ────────────────────────────
    print("Phase 1: Loading tasks and building anchor embeddings...")
    tasks = load_all_tasks()

    by_set = defaultdict(int)
    for t in tasks:
        by_set[t["task_set"]] += 1
    print(f"  Total tasks: {len(tasks)}")
    for s, n in sorted(by_set.items()):
        print(f"    {s}: {n}")

    anchor_vecs = build_anchor_embeddings(cache_path=ANCHOR_CACHE)

    # ── Phase 2: Classify all tasks ──────────────────────────────────────
    print("\nPhase 2: Classifying all tasks...")
    routing_counts = defaultdict(lambda: defaultdict(int))

    # Resume support
    existing = []
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
    if len(existing) >= len(tasks):
        print(f"  Already complete ({len(existing)} results)")
        results = existing
    else:
        # ── Phase 3: Adaptive inference ──────────────────────────────────
        print(f"\nPhase 3: Running adaptive inference ({len(tasks)} tasks)...")
        start_idx = len(existing)
        results = list(existing)
        mode = "a" if start_idx > 0 else "w"

        total_start = time.time()

        with open(RESULTS_PATH, mode, encoding="utf-8") as f_results, \
             open(ROUTING_LOG_PATH, mode, encoding="utf-8") as f_routing:
            for i, task in enumerate(tasks):
                if i < start_idx:
                    continue

                t0 = time.time()
                try:
                    nca_result = run_adaptive(
                        task["task_input"],
                        anchor_vecs,
                        task_type=task["task_type"],
                        task_set=task["task_set"],
                    )
                    verdict = nca_result["final_verdict"]
                    difficulty = nca_result["difficulty"]
                    pattern_used = nca_result["pattern_used"]
                    classification_meta = nca_result.get("classification_meta", {})
                    groupthink = nca_result.get("groupthink", "unknown")
                    steps = nca_result.get("steps", [])
                except Exception as e:
                    verdict = f"ERROR: {e}"
                    difficulty = "unknown"
                    pattern_used = "error"
                    classification_meta = {}
                    groupthink = "unknown"
                    steps = []

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
                    "difficulty": difficulty,
                    "pattern_used": pattern_used,
                    "groupthink": groupthink,
                    "elapsed_sec": round(elapsed, 2),
                    "steps": steps,
                }
                results.append(record)
                f_results.write(json.dumps(record, ensure_ascii=False) + "\n")
                f_results.flush()

                # Routing log (without steps for compactness)
                routing_entry = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "difficulty": difficulty,
                    "pattern_used": pattern_used,
                    "classification_meta": classification_meta,
                }
                f_routing.write(json.dumps(routing_entry, ensure_ascii=False) + "\n")
                f_routing.flush()

                status = "OK" if is_correct else "NG"
                print(f"  [{i+1:3d}/{len(tasks)}] {status} {verdict:14s} [{difficulty:6s}->{pattern_used:18s}] "
                      f"({elapsed:.1f}s) [{task['task_set']:18s}] {task['question'][:40]}")

        total_elapsed = time.time() - total_start
        print(f"\nAll {len(tasks)} tasks complete in {total_elapsed:.0f}s ({total_elapsed/3600:.1f}h)")

    # ── Phase 4: Analysis ────────────────────────────────────────────────
    print("\n" + "=" * 100)
    print("  NCA v8: Adaptive Model Selection Results")
    print("=" * 100)

    # Routing distribution
    route_dist = defaultdict(int)
    route_by_set = defaultdict(lambda: defaultdict(int))
    for r in results:
        route_dist[r["difficulty"]] += 1
        route_by_set[r["task_set"]][r["difficulty"]] += 1

    print(f"\nRouting Distribution:")
    for d in ["easy", "medium", "hard"]:
        pct = route_dist[d] / len(results) * 100
        pattern = {"easy": "single_agent", "medium": "best_fixed", "hard": "balanced_rotating"}[d]
        print(f"  {d:6s} -> {pattern:20s}: {route_dist[d]:3d} tasks ({pct:.0f}%)")

    print(f"\nRouting by Task Set:")
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        dist = route_by_set[ts]
        parts = ", ".join(f"{d}={dist[d]}" for d in ["easy", "medium", "hard"] if dist[d] > 0)
        print(f"  {ts:20s}: {parts}")

    # Per-task-set accuracy
    v7_bests = {
        "world_consistency": 0.63,
        "math_elementary": 0.83,
        "math_middle": 0.77,
        "math_high": 0.77,
    }

    print(f"\n{'Task Set':<20} | {'Adaptive':>9} | {'Best Fixed':>11} | {'Diff':>6}")
    print("-" * 55)
    overall_correct = 0
    overall_total = 0
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        stats = compute_stats(ts_results)
        best = v7_bests.get(ts, 0)
        diff = stats["overall"] - best
        print(f"{ts:<20} | {stats['overall']:>8.0%} | {best:>10.0%} | {diff:>+5.0%}pp")
        overall_correct += stats["n_correct"]
        overall_total += stats["total"]

    overall_acc = overall_correct / overall_total if overall_total else 0
    # Weighted best: sum of best-per-set * n_per_set / total
    weighted_best = sum(
        v7_bests[ts] * sum(1 for r in results if r["task_set"] == ts)
        for ts in v7_bests
    ) / overall_total
    print(f"{'Overall':<20} | {overall_acc:>8.0%} | {weighted_best:>10.0%} | {overall_acc - weighted_best:>+5.0%}pp")
    print("=" * 100)

    # CORRECT vs INCORRECT per task set
    print(f"\n{'Task Set':<20} | {'CORRECT acc':>12} | {'INCORRECT acc':>14}")
    print("-" * 55)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        stats = compute_stats(ts_results)
        print(f"{ts:<20} | {stats['correct_acc']:>11.0%} | {stats['incorrect_acc']:>13.0%}")

    # Per-difficulty accuracy
    print(f"\n{'Difficulty':<10} | {'n':>4} | {'Accuracy':>9} | {'Pattern':>20}")
    print("-" * 55)
    for d in ["easy", "medium", "hard"]:
        d_results = [r for r in results if r["difficulty"] == d]
        if d_results:
            acc = sum(1 for r in d_results if r["is_correct"]) / len(d_results)
            pattern = {"easy": "single_agent", "medium": "best_fixed", "hard": "balanced_rotating"}[d]
            print(f"{d:<10} | {len(d_results):>4} | {acc:>8.0%} | {pattern:>20}")

    print("=" * 100)

    # Save summary
    summary = {
        "overall_acc": round(overall_acc, 3),
        "overall_total": overall_total,
        "routing_distribution": dict(route_dist),
        "per_task_set": {},
    }
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        summary["per_task_set"][ts] = compute_stats(ts_results)

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
