"""
run_v10_cfr.py

v10 CFR Comparison Experiment.
Test whether math_middle CFR > math_high CFR with larger samples.

Uses best_fixed NCA (no AntiNode) with simple majority voting.
  Models: qwen2.5:7b (Solver), llama3:latest (Verifier), mistral:7b (Critic)
  Roles: fixed
  Agreement: [30, 80, 80]
  Steps: 3
"""

import json
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

from nca_network_v7 import run_nca_v7, aggregate_verdict, classify_groupthink

# ── Configuration ─────────────────────────────────────────────────────────

BEST_FIXED_CONFIG = {
    "models": ["qwen2.5:7b", "llama3:latest", "mistral:7b"],
    "agree": [30, 80, 80],
    "steps": 3,
    "role": "fixed",
}

RESULTS_DIR = Path("results/v10")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "v10_cfr_results.jsonl"

TASK_FILES = [
    RESULTS_DIR / "tasks" / "math_middle_new_tasks.jsonl",
    RESULTS_DIR / "tasks" / "math_high_new_tasks.jsonl",
]


# ── Helpers ───────────────────────────────────────────────────────────────

def verdict_matches(verdict: str, label: bool) -> bool:
    if verdict in ("CORRECT", "CONSISTENT"):
        return label is True
    elif verdict in ("INCORRECT", "CONTRADICTION"):
        return label is False
    return False


def binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
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
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    p_val = 2 * (1 - sp_stats.norm.cdf(abs(z)))
    return z, p_val


# ── Task loader ───────────────────────────────────────────────────────────

def load_tasks() -> list[dict]:
    tasks = []
    for fpath in TASK_FILES:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                task_input = f"Rule: {r['world_rule']}\nStatement: {r['question']}"
                tasks.append({
                    "task_id": r["task_id"],
                    "task_set": r["task_set"],
                    "task_type": r["task_type"],
                    "question": r["question"],
                    "label": r["label"],
                    "task_input": task_input,
                })
    return tasks


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 64)
    print("  v10 CFR Comparison Experiment")
    print("=" * 64)

    print("\nLoading tasks...")
    tasks = load_tasks()
    by_set = defaultdict(int)
    for t in tasks:
        by_set[t["task_set"]] += 1
    print(f"  Total: {len(tasks)}")
    for s, n in sorted(by_set.items()):
        print(f"    {s}: {n}")

    # Resume support
    existing = []
    completed_ids = set()
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    existing.append(r)
                    completed_ids.add(r["task_id"])
                except json.JSONDecodeError:
                    continue

    remaining = [t for t in tasks if t["task_id"] not in completed_ids]
    results = list(existing)

    if not remaining:
        print(f"  Already complete ({len(existing)} results)")
    else:
        print(f"\n  Resuming from {len(existing)}, {len(remaining)} remaining...")
        mode = "a" if existing else "w"
        total_start = time.time()

        with open(RESULTS_PATH, mode, encoding="utf-8") as f_out:
            for i, task in enumerate(remaining):
                global_idx = len(existing) + i
                t0 = time.time()

                try:
                    nca_result = run_nca_v7(
                        task["task_input"],
                        BEST_FIXED_CONFIG["models"],
                        BEST_FIXED_CONFIG["agree"],
                        BEST_FIXED_CONFIG["steps"],
                        BEST_FIXED_CONFIG["role"],
                    )

                    verdict = nca_result["final_verdict"]
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
                    is_unanimous = any(v == 3 for v in vote_dist.values())
                    steps = nca_result["steps"]

                except Exception as e:
                    verdict = f"ERROR: {e}"
                    vote_dist = {"CORRECT": 0, "INCORRECT": 0}
                    is_unanimous = False
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
                    "vote_distribution": vote_dist,
                    "is_unanimous": is_unanimous,
                    "elapsed_sec": round(elapsed, 2),
                    "steps": steps,
                }
                results.append(record)
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                f_out.flush()

                status = "OK" if is_correct else "NG"
                unan_tag = " [U]" if is_unanimous else " [S]"
                print(
                    f"  [{global_idx+1:4d}/{len(tasks)}] {status} {verdict:14s}"
                    f"{unan_tag} ({elapsed:.1f}s) "
                    f"[{task['task_set']:12s}/{task['task_type']:18s}] "
                    f"{task['question'][:40]}"
                )

                if (global_idx + 1) % 100 == 0:
                    elapsed_total = time.time() - total_start
                    rate = (i + 1) / elapsed_total
                    eta = (len(remaining) - i - 1) / rate if rate > 0 else 0
                    print(f"\n  --- Progress: {global_idx+1}/{len(tasks)} "
                          f"({elapsed_total/3600:.1f}h elapsed, "
                          f"~{eta/3600:.1f}h remaining) ---\n")

        total_elapsed = time.time() - total_start
        print(f"\nAll {len(tasks)} tasks complete in {total_elapsed:.0f}s "
              f"({total_elapsed/3600:.1f}h)")

    # ── Analysis ──────────────────────────────────────────────────────────
    print("\n" + "=" * 64)
    print("  v10 CFR Comparison Results")
    print("=" * 64)

    # Per task_set CFR
    by_ts = defaultdict(list)
    for r in results:
        by_ts[r["task_set"]].append(r)

    cfr_data = {}
    print(f"\n{'Task Set':<14} | {'n_tasks':>7} | {'n_unan':>7} | "
          f"{'n_wrong_u':>9} | {'CFR':>7} | {'95% CI':>16}")
    print("-" * 72)

    for ts in sorted(by_ts):
        recs = by_ts[ts]
        n_tasks = len(recs)
        unanimous = [r for r in recs if r.get("is_unanimous", False)]
        n_unan = len(unanimous)
        wrong_unan = [r for r in unanimous if not r["is_correct"]]
        n_wrong = len(wrong_unan)
        cfr = n_wrong / n_unan if n_unan > 0 else 0
        lo, hi = binomial_ci(n_wrong, n_unan) if n_unan > 0 else (0, 1)
        cfr_data[ts] = (n_wrong, n_unan)
        print(f"{ts:<14} | {n_tasks:>7} | {n_unan:>7} | "
              f"{n_wrong:>9} | {cfr:>6.1%} | [{lo:.1%}, {hi:.1%}]")

    # Statistical test: math_middle CFR vs math_high CFR
    print("\n" + "=" * 64)
    print("  Statistical Test: math_middle CFR vs math_high CFR")
    print("=" * 64)

    k1, n1 = cfr_data.get("math_middle", (0, 0))
    k2, n2 = cfr_data.get("math_high", (0, 0))

    if n1 > 0 and n2 > 0:
        z, p = two_prop_ztest(k1, n1, k2, n2)
        sig = "YES" if p < 0.05 else "NO"
        print(f"  math_middle CFR: {k1}/{n1} = {k1/n1:.4f}")
        print(f"  math_high CFR:   {k2}/{n2} = {k2/n2:.4f}")
        print(f"  z-statistic: {z:.4f}")
        print(f"  p-value:     {p:.4f}")
        print(f"  Significant at alpha=0.05: {sig}")
    else:
        print("  Insufficient data for test")

    # Comparison with v9d
    print("\n" + "=" * 64)
    print("  Comparison with v9d")
    print("=" * 64)
    v9d_mid = (17, 62)
    v9d_high = (12, 57)
    if n1 > 0:
        print(f"  math_middle: v9d={v9d_mid[0]}/{v9d_mid[1]}={v9d_mid[0]/v9d_mid[1]:.1%}"
              f" -> v10={k1}/{n1}={k1/n1:.1%}")
    if n2 > 0:
        print(f"  math_high:   v9d={v9d_high[0]}/{v9d_high[1]}={v9d_high[0]/v9d_high[1]:.1%}"
              f" -> v10={k2}/{n2}={k2/n2:.1%}")

    # Conclusion
    print("\n" + "=" * 64)
    print("  Conclusion")
    print("=" * 64)
    if n1 > 0 and n2 > 0:
        cfr_mid = k1 / n1
        cfr_high = k2 / n2
        if p < 0.05 and cfr_mid > cfr_high:
            print("  [X] math_middle CFR > math_high CFR (statistically confirmed)")
        elif p < 0.05 and cfr_mid < cfr_high:
            print("  [X] math_middle CFR < math_high CFR (unexpected reversal)")
        else:
            print("  [X] math_middle CFR ≈ math_high CFR (no significant difference)")
    print("=" * 64)

    # Also report overall accuracy per task_set
    print("\n--- Overall Accuracy ---")
    for ts in sorted(by_ts):
        recs = by_ts[ts]
        correct = sum(1 for r in recs if r["is_correct"])
        total = len(recs)
        lo, hi = binomial_ci(correct, total)
        print(f"  {ts}: {correct}/{total} = {correct/total:.1%} [{lo:.1%}, {hi:.1%}]")


if __name__ == "__main__":
    main()
