"""
run_v9b.py

Run NCA v9b: best_fixed + Dynamic Confidence-Weighted Aggregation on all 350 tasks.

One-variable experiment: dynamic weighted aggregation is the ONLY change from best_fixed.
  - Models: qwen2.5:7b + llama3:latest + mistral:7b (fixed)
  - agree: [30, 80, 80] (fixed)
  - steps: 3 (fixed)
  - role: fixed (fixed)
  - Aggregation: trust-weighted confidence (NEW) instead of simple majority
  - NO MetaAgent (v9a only)
  - Online learning: alpha=0.1 EMA weight updates after each task
  - Initial weights from v7/v7.5/v7.6 per-model accuracy
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")

from task_generator import generate_tasks as generate_world_consistency_tasks
from math_task_generator import generate_math_tasks
from middle_school_task_generator import generate_middle_school_tasks
from high_school_task_generator import generate_high_school_tasks
from nca_network_v9b import run_v9b, get_aggregator

RESULTS_DIR = Path("results/v9b")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "v9b_results.jsonl"
WEIGHT_LOG_PATH = RESULTS_DIR / "v9b_weight_log.jsonl"
SUMMARY_PATH = RESULTS_DIR / "v9b_summary.jsonl"


# ── Statistical helpers ────────────────────────────────────────────────────

def binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Clopper-Pearson exact 95% CI."""
    if n == 0:
        return 0.0, 1.0
    if k == 0:
        return 0.0, 1 - (alpha / 2) ** (1 / n)
    if k == n:
        return (alpha / 2) ** (1 / n), 1.0
    ci_low = sp_stats.beta.ppf(alpha / 2, k, n - k + 1)
    ci_high = sp_stats.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return ci_low, ci_high


def two_prop_ztest(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Two-proportion z-test. Returns (z, p_value)."""
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    p_val = 2 * (1 - sp_stats.norm.cdf(abs(z)))
    return z, p_val


def fmt_ci(k: int, n: int) -> str:
    if n == 0:
        return "N/A"
    acc = k / n
    lo, hi = binomial_ci(k, n)
    return f"{acc:.1%} [{lo:.1%}, {hi:.1%}]"


def fmt_sig(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "n.s."


# ── Unified task loader (same as v8/v9a) ─────────────────────────────────

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
            "label": t.label,
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
        return {"overall": 0, "correct_acc": 0, "incorrect_acc": 0,
                "total": 0, "n_correct": 0}

    correct = sum(1 for r in results if r["is_correct"])

    correct_label = [r for r in results if r["label"] is True]
    incorrect_label = [r for r in results if r["label"] is False]
    c_acc = (sum(1 for r in correct_label if r["is_correct"]) / len(correct_label)
             if correct_label else 0)
    i_acc = (sum(1 for r in incorrect_label if r["is_correct"]) / len(incorrect_label)
             if incorrect_label else 0)

    return {
        "overall": round(correct / total, 3),
        "correct_acc": round(c_acc, 3),
        "incorrect_acc": round(i_acc, 3),
        "total": total,
        "n_correct": correct,
    }


def main():
    # ── Phase 1: Load tasks ─────────────────────────────────────────────
    print("Phase 1: Loading tasks...")
    tasks = load_all_tasks()

    by_set = defaultdict(int)
    for t in tasks:
        by_set[t["task_set"]] += 1
    print(f"  Total tasks: {len(tasks)}")
    for s, n in sorted(by_set.items()):
        print(f"    {s}: {n}")

    aggregator = get_aggregator()
    models = ["qwen2.5:7b", "llama3:latest", "mistral:7b"]
    print(f"  Initial weights: {aggregator.get_weights()}")

    # ── Phase 2: Resume support ─────────────────────────────────────────
    existing = []
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    existing.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # skip corrupted lines
    if len(existing) >= len(tasks):
        print(f"  Already complete ({len(existing)} results)")
        results = existing
    else:
        # ── Phase 3: Run best_fixed + weighted aggregation ─────────────
        print(f"\nPhase 3: Running best_fixed + weighted aggregation ({len(tasks)} tasks)...")
        start_idx = len(existing)
        results = list(existing)
        mode = "a" if start_idx > 0 else "w"

        # If resuming, replay weight updates from existing results
        if start_idx > 0:
            print(f"  Resuming from task {start_idx}, replaying weight updates...")
            for r in existing:
                if "final_node_outputs" in r:
                    node_outputs = r["final_node_outputs"]
                    aggregator.update(node_outputs, models, r["label"])
            print(f"  Weights after replay: {aggregator.get_weights()}")

        total_start = time.time()

        with open(RESULTS_PATH, mode, encoding="utf-8") as f_results, \
             open(WEIGHT_LOG_PATH, mode, encoding="utf-8") as f_weights:
            for i, task in enumerate(tasks):
                if i < start_idx:
                    continue

                t0 = time.time()
                try:
                    nca_result = run_v9b(task["task_input"])
                    verdict = nca_result["final_verdict"]
                    simple_majority = nca_result.get("simple_majority", "")
                    groupthink = nca_result.get("groupthink", "unknown")
                    agg_details = nca_result.get("aggregation_details", {})
                    steps = nca_result.get("steps", [])

                    # Extract final node outputs for weight update
                    last_step = nca_result["steps"][-1]
                    final_node_outputs = [
                        last_step["solver"]["output"],
                        last_step["verifier"]["output"],
                        last_step["critic"]["output"],
                    ]
                except Exception as e:
                    verdict = f"ERROR: {e}"
                    simple_majority = ""
                    groupthink = "unknown"
                    agg_details = {}
                    steps = []
                    final_node_outputs = []

                elapsed = time.time() - t0
                is_correct = verdict_matches(verdict, task["label"])
                simple_correct = verdict_matches(simple_majority, task["label"])

                # Online learning: update weights AFTER verdict
                weight_changes = {}
                if final_node_outputs:
                    weight_changes = aggregator.update(
                        final_node_outputs, models, task["label"]
                    )

                record = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "question": task["question"],
                    "label": task["label"],
                    "prediction": verdict,
                    "is_correct": is_correct,
                    "pattern_used": "best_fixed_weighted",
                    "groupthink": groupthink,
                    "elapsed_sec": round(elapsed, 2),
                    "steps": steps,
                    # Weighted aggregation fields
                    "simple_majority": simple_majority,
                    "simple_correct": simple_correct,
                    "aggregation_scores": agg_details.get("scores", {}),
                    "weights_used": agg_details.get("current_weights", {}),
                    "final_node_outputs": final_node_outputs,
                }
                results.append(record)
                f_results.write(json.dumps(record, ensure_ascii=False) + "\n")
                f_results.flush()

                # Weight log
                weight_entry = {
                    "task_idx": i,
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "weights_before": agg_details.get("current_weights", {}),
                    "weights_after": aggregator.get_weights(),
                    "weight_changes": weight_changes,
                    "verdict": verdict,
                    "is_correct": is_correct,
                    "simple_majority": simple_majority,
                    "simple_correct": simple_correct,
                    "agreed_with_simple": (verdict == simple_majority),
                }
                f_weights.write(json.dumps(weight_entry, ensure_ascii=False) + "\n")
                f_weights.flush()

                diff_tag = "" if verdict == simple_majority else " [DIFF]"
                status = "OK" if is_correct else "NG"
                print(
                    f"  [{i+1:3d}/{len(tasks)}] {status} {verdict:14s}"
                    f"{diff_tag:7s} ({elapsed:.1f}s) "
                    f"[{task['task_set']:18s}] {task['question'][:40]}"
                )

        total_elapsed = time.time() - total_start
        print(f"\nAll {len(tasks)} tasks complete in {total_elapsed:.0f}s "
              f"({total_elapsed/3600:.1f}h)")

    # ── Phase 4: Analysis ───────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  NCA v9b: Dynamic Confidence-Weighted Aggregation Results")
    print("=" * 80)

    # v8 baselines (from v8 report)
    v8_scores = {
        "world_consistency": (66, 100),
        "math_elementary": (85, 100),
        "math_middle": (57, 75),
        "math_high": (61, 75),
    }
    v8_overall = (269, 350)

    # v9a baselines (from v9a summary)
    v9a_scores = {
        "world_consistency": (69, 100),
        "math_elementary": (81, 100),
        "math_middle": (55, 75),
        "math_high": (57, 75),
    }
    v9a_overall = (262, 350)

    # Main results table
    print(f"\n{'Task Set':<20} | {'v9b':>18} | {'v8(adaptive)':>12} | "
          f"{'v9a(meta)':>10} | {'Δv8':>6} | {'Δv9a':>6}")
    print("-" * 85)

    overall_correct = 0
    overall_total = 0
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        v8_k, v8_n = v8_scores[ts]
        v8_acc = v8_k / v8_n
        v9a_k, v9a_n = v9a_scores[ts]
        v9a_acc = v9a_k / v9a_n
        diff_v8 = st["overall"] - v8_acc
        diff_v9a = st["overall"] - v9a_acc
        ci_str = fmt_ci(st["n_correct"], st["total"])
        print(f"{ts:<20} | {ci_str:>18} | {v8_acc:>11.0%} | "
              f"{v9a_acc:>9.0%} | {diff_v8:>+5.0%}pp | {diff_v9a:>+5.0%}pp")
        overall_correct += st["n_correct"]
        overall_total += st["total"]

    overall_acc = overall_correct / overall_total if overall_total else 0
    ci_overall = fmt_ci(overall_correct, overall_total)
    v8_ov_acc = v8_overall[0] / v8_overall[1]
    v9a_ov_acc = v9a_overall[0] / v9a_overall[1]
    diff_ov_v8 = overall_acc - v8_ov_acc
    diff_ov_v9a = overall_acc - v9a_ov_acc
    print(f"{'Overall':<20} | {ci_overall:>18} | {v8_ov_acc:>11.0%} | "
          f"{v9a_ov_acc:>9.0%} | {diff_ov_v8:>+5.0%}pp | {diff_ov_v9a:>+5.0%}pp")

    # ── Statistical tests ───────────────────────────────────────────────
    print("\n--- Statistical Tests (two-proportion z-test) ---")

    # v9b vs v8 overall
    z, p = two_prop_ztest(overall_correct, overall_total, *v8_overall)
    print(f"\nv9b vs v8 overall: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        k1 = sum(1 for r in ts_results if r["is_correct"])
        n1 = len(ts_results)
        k2, n2 = v8_scores[ts]
        z, p = two_prop_ztest(k1, n1, k2, n2)
        print(f"  {ts}: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")

    # v9b vs v9a overall
    z, p = two_prop_ztest(overall_correct, overall_total, *v9a_overall)
    print(f"\nv9b vs v9a overall: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        k1 = sum(1 for r in ts_results if r["is_correct"])
        n1 = len(ts_results)
        k2, n2 = v9a_scores[ts]
        z, p = two_prop_ztest(k1, n1, k2, n2)
        print(f"  {ts}: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")

    print("=" * 80)

    # ── Weighted vs Simple Majority comparison ──────────────────────────
    print("\nWeighted vs Simple Majority Comparison:")
    n_diff = sum(1 for r in results
                 if r.get("prediction") != r.get("simple_majority"))
    n_total = len(results)
    print(f"  Disagreements: {n_diff} / {n_total} ({n_diff/n_total:.1%})")

    if n_diff > 0:
        diff_tasks = [r for r in results
                      if r.get("prediction") != r.get("simple_majority")]
        weighted_wins = sum(1 for r in diff_tasks if r["is_correct"])
        simple_wins = sum(1 for r in diff_tasks if r.get("simple_correct", False))
        print(f"  When they disagree:")
        print(f"    Weighted correct: {weighted_wins}/{n_diff} ({weighted_wins/n_diff:.1%})")
        print(f"    Simple correct:   {simple_wins}/{n_diff} ({simple_wins/n_diff:.1%})")
        print(f"    Net impact: {weighted_wins - simple_wins:+d} tasks")

        # Breakdown by task set
        print(f"\n  {'Task Set':<20} | {'Disagree':>9} | {'Weighted':>8} | "
              f"{'Simple':>8} | {'Net':>5}")
        print("  " + "-" * 60)
        for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
            ts_diff = [r for r in diff_tasks if r["task_set"] == ts]
            if ts_diff:
                w_k = sum(1 for r in ts_diff if r["is_correct"])
                s_k = sum(1 for r in ts_diff if r.get("simple_correct", False))
                print(f"  {ts:<20} | {len(ts_diff):>9} | {w_k:>8} | "
                      f"{s_k:>8} | {w_k - s_k:>+5}")
            else:
                print(f"  {ts:<20} | {'0':>9} | {'-':>8} | {'-':>8} | {'-':>5}")

    # ── Weight evolution ────────────────────────────────────────────────
    print(f"\nFinal weights: {aggregator.get_weights()}")
    print(f"Initial weights were: qwen2.5:7b=0.740, llama3=0.768, mistral=0.796")

    # ── CORRECT vs INCORRECT per task set ───────────────────────────────
    print(f"\n{'Task Set':<20} | {'CORRECT acc':>14} | {'INCORRECT acc':>14}")
    print("-" * 55)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        print(f"{ts:<20} | {st['correct_acc']:>13.0%} | {st['incorrect_acc']:>13.0%}")

    # ── Groupthink distribution ─────────────────────────────────────────
    print(f"\n{'Task Set':<20} | {'All Correct':>12} | {'All Incorrect':>14} | "
          f"{'Split':>6}")
    print("-" * 60)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        ac = sum(1 for r in ts_results if r.get("groupthink") == "all_correct")
        ai = sum(1 for r in ts_results if r.get("groupthink") == "all_incorrect")
        sp = sum(1 for r in ts_results if r.get("groupthink") == "split")
        print(f"{ts:<20} | {ac:>12} | {ai:>14} | {sp:>6}")

    print("=" * 80)

    # ── Save summary ────────────────────────────────────────────────────
    summary = {
        "experiment": "v9b",
        "description": "best_fixed + dynamic confidence-weighted aggregation",
        "overall_acc": round(overall_acc, 3),
        "overall_total": overall_total,
        "overall_correct": overall_correct,
        "initial_weights": {"qwen2.5:7b": 0.740, "llama3:latest": 0.768,
                            "mistral:7b": 0.796},
        "final_weights": aggregator.get_weights(),
        "learning_rate": 0.1,
        "disagreements_with_simple": n_diff,
        "per_task_set": {},
    }
    if n_diff > 0:
        diff_tasks = [r for r in results
                      if r.get("prediction") != r.get("simple_majority")]
        weighted_wins = sum(1 for r in diff_tasks if r["is_correct"])
        simple_wins = sum(1 for r in diff_tasks if r.get("simple_correct", False))
        summary["weighted_wins"] = weighted_wins
        summary["simple_wins"] = simple_wins
        summary["net_impact"] = weighted_wins - simple_wins

    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        ts_diff = [r for r in results if r["task_set"] == ts
                   and r.get("prediction") != r.get("simple_majority")]
        st["disagreements"] = len(ts_diff)
        summary["per_task_set"][ts] = st

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
