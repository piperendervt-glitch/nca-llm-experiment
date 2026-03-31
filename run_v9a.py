"""
run_v9a.py

Run NCA v9a: best_fixed + MetaAgent on all 350 tasks.

One-variable experiment: MetaAgent is the ONLY change from best_fixed.
  - Models: qwen2.5:7b + llama3:latest + mistral:7b (fixed)
  - agree: [30, 80, 80] (fixed)
  - steps: 3 (fixed)
  - role: fixed (fixed)
  - MetaAgent: qwen2.5:7b, intervenes on split only (NEW)
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
from nca_network_v9a import run_v9a

RESULTS_DIR = Path("results/v9a")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "v9a_results.jsonl"
META_LOG_PATH = RESULTS_DIR / "v9a_meta_log.jsonl"
SUMMARY_PATH = RESULTS_DIR / "v9a_summary.jsonl"


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
    """Format accuracy with 95% CI."""
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


# ── Unified task loader (same as v8) ───────────────────────────────────────

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

    # ── Phase 2: Resume support ─────────────────────────────────────────
    existing = []
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
    if len(existing) >= len(tasks):
        print(f"  Already complete ({len(existing)} results)")
        results = existing
    else:
        # ── Phase 3: Run best_fixed + MetaAgent ─────────────────────────
        print(f"\nPhase 3: Running best_fixed + MetaAgent ({len(tasks)} tasks)...")
        start_idx = len(existing)
        results = list(existing)
        mode = "a" if start_idx > 0 else "w"

        total_start = time.time()

        with open(RESULTS_PATH, mode, encoding="utf-8") as f_results, \
             open(META_LOG_PATH, mode, encoding="utf-8") as f_meta:
            for i, task in enumerate(tasks):
                if i < start_idx:
                    continue

                t0 = time.time()
                try:
                    nca_result = run_v9a(task["task_input"])
                    verdict = nca_result["final_verdict"]
                    groupthink = nca_result.get("groupthink", "unknown")
                    steps = nca_result.get("steps", [])
                    meta_intervened = nca_result.get("meta_intervened", False)
                    meta_reasoning = nca_result.get("meta_reasoning", "")
                    vote_dist = nca_result.get("vote_distribution", {})
                    pre_meta_majority = nca_result.get("pre_meta_majority", "")
                except Exception as e:
                    verdict = f"ERROR: {e}"
                    groupthink = "unknown"
                    steps = []
                    meta_intervened = False
                    meta_reasoning = f"ERROR: {e}"
                    vote_dist = {}
                    pre_meta_majority = ""

                elapsed = time.time() - t0
                is_correct = verdict_matches(verdict, task["label"])

                # Also check if pre-meta majority would have been correct
                pre_meta_correct = verdict_matches(pre_meta_majority, task["label"])

                record = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "question": task["question"],
                    "label": task["label"],
                    "prediction": verdict,
                    "is_correct": is_correct,
                    "pattern_used": "best_fixed_meta",
                    "groupthink": groupthink,
                    "elapsed_sec": round(elapsed, 2),
                    "steps": steps,
                    # MetaAgent fields
                    "meta_intervened": meta_intervened,
                    "meta_reasoning": meta_reasoning,
                    "vote_distribution": vote_dist,
                    "pre_meta_majority": pre_meta_majority,
                    "pre_meta_correct": pre_meta_correct,
                }
                results.append(record)
                f_results.write(json.dumps(record, ensure_ascii=False) + "\n")
                f_results.flush()

                # MetaAgent log (compact)
                meta_entry = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "label": task["label"],
                    "meta_intervened": meta_intervened,
                    "meta_verdict": verdict,
                    "meta_correct": is_correct,
                    "pre_meta_majority": pre_meta_majority,
                    "pre_meta_correct": pre_meta_correct,
                    "vote_distribution": vote_dist,
                }
                f_meta.write(json.dumps(meta_entry, ensure_ascii=False) + "\n")
                f_meta.flush()

                meta_tag = " [META]" if meta_intervened else ""
                status = "OK" if is_correct else "NG"
                print(
                    f"  [{i+1:3d}/{len(tasks)}] {status} {verdict:14s}"
                    f"{meta_tag:7s} ({elapsed:.1f}s) "
                    f"[{task['task_set']:18s}] {task['question'][:40]}"
                )

        total_elapsed = time.time() - total_start
        print(f"\nAll {len(tasks)} tasks complete in {total_elapsed:.0f}s "
              f"({total_elapsed/3600:.1f}h)")

    # ── Phase 4: Analysis ───────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  NCA v9a: MetaAgent Addition Results")
    print("=" * 80)

    # v8 baselines (from v8 report)
    v8_scores = {
        "world_consistency": (66, 100),
        "math_elementary": (85, 100),
        "math_middle": (57, 75),
        "math_high": (61, 75),
    }
    v8_overall = (269, 350)

    v7_bests = {
        "world_consistency": 0.63,
        "math_elementary": 0.83,
        "math_middle": 0.77,
        "math_high": 0.77,
    }

    # Main results table
    print(f"\n{'Task Set':<20} | {'v9a':>12} | {'v8(adaptive)':>12} | "
          f"{'v6/v7 best':>10} | {'Diff(v8)':>8}")
    print("-" * 75)

    overall_correct = 0
    overall_total = 0
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        v8_k, v8_n = v8_scores[ts]
        v8_acc = v8_k / v8_n
        v7_best = v7_bests[ts]
        diff_v8 = st["overall"] - v8_acc
        ci_str = fmt_ci(st["n_correct"], st["total"])
        print(f"{ts:<20} | {ci_str:>12} | {v8_acc:>11.0%} | "
              f"{v7_best:>9.0%} | {diff_v8:>+7.0%}pp")
        overall_correct += st["n_correct"]
        overall_total += st["total"]

    overall_acc = overall_correct / overall_total if overall_total else 0
    ci_overall = fmt_ci(overall_correct, overall_total)
    v8_ov_acc = v8_overall[0] / v8_overall[1]
    diff_ov = overall_acc - v8_ov_acc
    print(f"{'Overall':<20} | {ci_overall:>12} | {v8_ov_acc:>11.0%} | "
          f"{'—':>9} | {diff_ov:>+7.0%}pp")

    # z-test: v9a vs v8 overall
    z, p = two_prop_ztest(overall_correct, overall_total, *v8_overall)
    print(f"\nv9a vs v8 overall: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")

    # Per-task-set z-tests
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        k1 = sum(1 for r in ts_results if r["is_correct"])
        n1 = len(ts_results)
        k2, n2 = v8_scores[ts]
        z, p = two_prop_ztest(k1, n1, k2, n2)
        print(f"  {ts}: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")

    print("=" * 80)

    # ── MetaAgent Intervention Statistics ────────────────────────────────
    print("\nMetaAgent Intervention Statistics:")
    meta_tasks = [r for r in results if r.get("meta_intervened", False)]
    non_meta_tasks = [r for r in results if not r.get("meta_intervened", False)]
    n_meta = len(meta_tasks)
    n_total = len(results)

    print(f"  Total interventions: {n_meta} / {n_total} tasks ({n_meta/n_total:.0%})")

    if n_meta > 0:
        meta_correct = sum(1 for r in meta_tasks if r["is_correct"])
        meta_acc = meta_correct / n_meta
        # What would majority-only have scored on these same tasks?
        majority_correct = sum(1 for r in meta_tasks if r.get("pre_meta_correct", False))
        majority_acc = majority_correct / n_meta

        print(f"  Intervention accuracy: {fmt_ci(meta_correct, n_meta)}")
        print(f"  Majority-only accuracy: {fmt_ci(majority_correct, n_meta)} "
              f"(same {n_meta} tasks)")
        net_impact = meta_correct - majority_correct
        print(f"  MetaAgent net impact: {net_impact:+d} tasks "
              f"({net_impact/n_total:+.1%}pp on overall)")

        # z-test: MetaAgent vs majority on split tasks
        z_m, p_m = two_prop_ztest(meta_correct, n_meta, majority_correct, n_meta)
        print(f"  MetaAgent vs majority on splits: z={z_m:.3f}, p={p_m:.4f} ({fmt_sig(p_m)})")

    # Breakdown by task set
    print(f"\n  {'Task Set':<20} | {'Interventions':>14} | {'Meta acc':>12} | "
          f"{'Majority acc':>12}")
    print("  " + "-" * 70)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_meta = [r for r in meta_tasks if r["task_set"] == ts]
        if ts_meta:
            m_k = sum(1 for r in ts_meta if r["is_correct"])
            maj_k = sum(1 for r in ts_meta if r.get("pre_meta_correct", False))
            print(f"  {ts:<20} | {len(ts_meta):>3d} / "
                  f"{sum(1 for r in results if r['task_set']==ts):>3d}"
                  f" ({len(ts_meta)/sum(1 for r in results if r['task_set']==ts):.0%})"
                  f" | {fmt_ci(m_k, len(ts_meta)):>12}"
                  f" | {fmt_ci(maj_k, len(ts_meta)):>12}")
        else:
            n_ts = sum(1 for r in results if r["task_set"] == ts)
            print(f"  {ts:<20} |   0 / {n_ts:>3d} (0%)  | {'N/A':>12} | {'N/A':>12}")

    # CORRECT vs INCORRECT per task set
    print(f"\n{'Task Set':<20} | {'CORRECT acc':>14} | {'INCORRECT acc':>14}")
    print("-" * 55)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        print(f"{ts:<20} | {st['correct_acc']:>13.0%} | {st['incorrect_acc']:>13.0%}")

    print("=" * 80)

    # ── Save summary ────────────────────────────────────────────────────
    summary = {
        "overall_acc": round(overall_acc, 3),
        "overall_total": overall_total,
        "overall_correct": overall_correct,
        "meta_interventions": n_meta,
        "meta_intervention_rate": round(n_meta / n_total, 3) if n_total else 0,
        "per_task_set": {},
    }
    if n_meta > 0:
        meta_correct = sum(1 for r in meta_tasks if r["is_correct"])
        majority_correct = sum(1 for r in meta_tasks if r.get("pre_meta_correct", False))
        summary["meta_accuracy"] = round(meta_correct / n_meta, 3)
        summary["majority_accuracy_on_splits"] = round(majority_correct / n_meta, 3)
        summary["meta_net_impact"] = meta_correct - majority_correct

    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        ts_meta = [r for r in meta_tasks if r["task_set"] == ts]
        st = compute_stats(ts_results)
        st["meta_interventions"] = len(ts_meta)
        if ts_meta:
            st["meta_accuracy"] = round(
                sum(1 for r in ts_meta if r["is_correct"]) / len(ts_meta), 3)
        summary["per_task_set"][ts] = st

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
