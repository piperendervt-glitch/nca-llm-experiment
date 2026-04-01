"""
run_v9c.py

Run NCA v9c: best_fixed + AntiNode on all 350 tasks.

One-variable experiment: AntiNode is the ONLY change from best_fixed.
  - Models: qwen2.5:7b + llama3:latest + mistral:7b (fixed)
  - agree: [30, 80, 80] (fixed)
  - steps: 3 (fixed)
  - role: fixed (fixed)
  - AntiNode: mistral:7b, weight=0.5, argues against majority (NEW)
  - NO MetaAgent (v9a only)
  - NO dynamic weighting (v9b only)
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
from nca_network_v9c import run_v9c

RESULTS_DIR = Path("results/v9c")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "v9c_results.jsonl"
ANTI_LOG_PATH = RESULTS_DIR / "v9c_anti_log.jsonl"
SUMMARY_PATH = RESULTS_DIR / "v9c_summary.jsonl"


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


# ── Unified task loader (same as v8/v9a/v9b) ─────────────────────────────

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


def verdict_matches(verdict: str, label: bool) -> bool:
    if verdict in ("CORRECT", "CONSISTENT"):
        return label is True
    elif verdict in ("INCORRECT", "CONTRADICTION"):
        return label is False
    return False


def compute_stats(results: list[dict]) -> dict:
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
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    existing.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    if len(existing) >= len(tasks):
        print(f"  Already complete ({len(existing)} results)")
        results = existing
    else:
        # ── Phase 3: Run best_fixed + AntiNode ─────────────────────────
        print(f"\nPhase 3: Running best_fixed + AntiNode ({len(tasks)} tasks)...")
        start_idx = len(existing)
        results = list(existing)
        mode = "a" if start_idx > 0 else "w"

        total_start = time.time()

        with open(RESULTS_PATH, mode, encoding="utf-8") as f_results, \
             open(ANTI_LOG_PATH, mode, encoding="utf-8") as f_anti:
            for i, task in enumerate(tasks):
                if i < start_idx:
                    continue

                t0 = time.time()
                try:
                    nca_result = run_v9c(task["task_input"])
                    verdict = nca_result["final_verdict"]
                    pre_anti = nca_result.get("pre_anti_majority", "")
                    pre_anti_gt = nca_result.get("pre_anti_groupthink", "unknown")
                    anti_output = nca_result.get("anti_output", {})
                    anti_complied = nca_result.get("anti_complied", False)
                    anti_changed = nca_result.get("anti_changed_outcome", False)
                    gt_prevented = nca_result.get("groupthink_prevented", False)
                    agg_details = nca_result.get("aggregation_details", {})
                    steps = nca_result.get("steps", [])
                    groupthink = nca_result.get("groupthink", "unknown")
                except Exception as e:
                    verdict = f"ERROR: {e}"
                    pre_anti = ""
                    pre_anti_gt = "unknown"
                    anti_output = {}
                    anti_complied = False
                    anti_changed = False
                    gt_prevented = False
                    agg_details = {}
                    steps = []
                    groupthink = "unknown"

                elapsed = time.time() - t0
                is_correct = verdict_matches(verdict, task["label"])
                pre_anti_correct = verdict_matches(pre_anti, task["label"])

                record = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "question": task["question"],
                    "label": task["label"],
                    "prediction": verdict,
                    "is_correct": is_correct,
                    "pattern_used": "best_fixed_anti",
                    "groupthink": groupthink,
                    "elapsed_sec": round(elapsed, 2),
                    "steps": steps,
                    # Pre-anti baseline
                    "pre_anti_majority": pre_anti,
                    "pre_anti_correct": pre_anti_correct,
                    "pre_anti_groupthink": pre_anti_gt,
                    # AntiNode fields
                    "anti_decision": anti_output.get("decision", "UNKNOWN"),
                    "anti_confidence": float(anti_output.get("confidence", 0.5)),
                    "anti_reasoning": str(anti_output.get("reasoning", ""))[:500],
                    "anti_complied": anti_complied,
                    "anti_changed_outcome": anti_changed,
                    "groupthink_prevented": gt_prevented,
                    # Aggregation
                    "aggregation_scores": agg_details.get("scores", {}),
                }
                results.append(record)
                f_results.write(json.dumps(record, ensure_ascii=False) + "\n")
                f_results.flush()

                # AntiNode log
                anti_entry = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "label": task["label"],
                    "pre_anti_majority": pre_anti,
                    "pre_anti_correct": pre_anti_correct,
                    "pre_anti_groupthink": pre_anti_gt,
                    "anti_decision": anti_output.get("decision", "UNKNOWN"),
                    "anti_complied": anti_complied,
                    "final_verdict": verdict,
                    "final_correct": is_correct,
                    "anti_changed_outcome": anti_changed,
                    "groupthink_prevented": gt_prevented,
                }
                f_anti.write(json.dumps(anti_entry, ensure_ascii=False) + "\n")
                f_anti.flush()

                anti_tag = " [ANTI]" if anti_changed else ""
                gt_tag = " [GT!]" if gt_prevented else ""
                status = "OK" if is_correct else "NG"
                print(
                    f"  [{i+1:3d}/{len(tasks)}] {status} {verdict:14s}"
                    f"{anti_tag:7s}{gt_tag:6s} ({elapsed:.1f}s) "
                    f"[{task['task_set']:18s}] {task['question'][:40]}"
                )

        total_elapsed = time.time() - total_start
        print(f"\nAll {len(tasks)} tasks complete in {total_elapsed:.0f}s "
              f"({total_elapsed/3600:.1f}h)")

    # ── Phase 4: Analysis ───────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  NCA v9c: AntiNode Contrarian Bias Correction Results")
    print("=" * 80)

    # Baselines
    v8_scores = {
        "world_consistency": (66, 100),
        "math_elementary": (85, 100),
        "math_middle": (57, 75),
        "math_high": (61, 75),
    }
    v8_overall = (269, 350)

    v9a_scores = {
        "world_consistency": (69, 100),
        "math_elementary": (81, 100),
        "math_middle": (55, 75),
        "math_high": (57, 75),
    }
    v9a_overall = (262, 350)

    v9b_scores = {
        "world_consistency": (69, 100),
        "math_elementary": (87, 100),
        "math_middle": (58, 75),
        "math_high": (63, 75),
    }
    v9b_overall = (277, 350)

    # ── Main results table ──────────────────────────────────────────────
    print(f"\n{'Task Set':<20} | {'v9c':>18} | {'v9b':>5} | {'v8':>5} | "
          f"{'v9a':>5} | {'Dv8':>5} | {'Dv9b':>5}")
    print("-" * 80)

    overall_correct = 0
    overall_total = 0
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        v8_k, v8_n = v8_scores[ts]
        v9a_k, v9a_n = v9a_scores[ts]
        v9b_k, v9b_n = v9b_scores[ts]
        ci_str = fmt_ci(st["n_correct"], st["total"])
        diff_v8 = st["overall"] - v8_k / v8_n
        diff_v9b = st["overall"] - v9b_k / v9b_n
        print(f"{ts:<20} | {ci_str:>18} | {v9b_k/v9b_n:>4.0%} | "
              f"{v8_k/v8_n:>4.0%} | {v9a_k/v9a_n:>4.0%} | "
              f"{diff_v8:>+4.0%}pp | {diff_v9b:>+4.0%}pp")
        overall_correct += st["n_correct"]
        overall_total += st["total"]

    overall_acc = overall_correct / overall_total if overall_total else 0
    ci_overall = fmt_ci(overall_correct, overall_total)
    v8_ov = v8_overall[0] / v8_overall[1]
    v9a_ov = v9a_overall[0] / v9a_overall[1]
    v9b_ov = v9b_overall[0] / v9b_overall[1]
    print(f"{'Overall':<20} | {ci_overall:>18} | {v9b_ov:>4.0%} | "
          f"{v8_ov:>4.0%} | {v9a_ov:>4.0%} | "
          f"{overall_acc - v8_ov:>+4.0%}pp | {overall_acc - v9b_ov:>+4.0%}pp")

    # ── Statistical tests ───────────────────────────────────────────────
    print("\n--- Statistical Tests ---")

    for label, ref_overall, ref_scores in [
        ("v9c vs v8", v8_overall, v8_scores),
        ("v9c vs v9a", v9a_overall, v9a_scores),
        ("v9c vs v9b", v9b_overall, v9b_scores),
    ]:
        z, p = two_prop_ztest(overall_correct, overall_total, *ref_overall)
        print(f"\n{label} overall: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")
        for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
            ts_results = [r for r in results if r["task_set"] == ts]
            k1 = sum(1 for r in ts_results if r["is_correct"])
            n1 = len(ts_results)
            k2, n2 = ref_scores[ts]
            z, p = two_prop_ztest(k1, n1, k2, n2)
            print(f"  {ts}: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")

    print("=" * 80)

    # ── CORRECT/INCORRECT Balance (Key Success Metric) ──────────────────
    print("\n--- CORRECT/INCORRECT Balance (Success Criterion) ---")
    print(f"\n{'Task Set':<20} | {'CORRECT acc':>12} | {'INCORRECT acc':>14} | "
          f"{'Balance':>8} | {'v9b Bal':>8}")
    print("-" * 75)

    # v9b balance for comparison
    v9b_balance = {
        "world_consistency": (0.72, 0.66),
        "math_elementary": (0.81, 0.94),
        "math_middle": (0.82, 0.72),
        "math_high": (0.85, 0.83),
    }

    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        bal = min(st["correct_acc"], st["incorrect_acc"]) / max(st["correct_acc"], st["incorrect_acc"]) if max(st["correct_acc"], st["incorrect_acc"]) > 0 else 0
        v9b_c, v9b_i = v9b_balance[ts]
        v9b_bal = min(v9b_c, v9b_i) / max(v9b_c, v9b_i) if max(v9b_c, v9b_i) > 0 else 0
        print(f"{ts:<20} | {st['correct_acc']:>11.0%} | {st['incorrect_acc']:>13.0%} | "
              f"{bal:>7.2f} | {v9b_bal:>7.2f}")

    # World consistency target check
    wc_results = [r for r in results if r["task_set"] == "world_consistency"]
    wc_st = compute_stats(wc_results)
    target_met = wc_st["correct_acc"] >= 0.65 and wc_st["incorrect_acc"] >= 0.65
    print(f"\n  World consistency target (~70%/70%): "
          f"CORRECT={wc_st['correct_acc']:.0%}, INCORRECT={wc_st['incorrect_acc']:.0%} "
          f"-> {'MET' if target_met else 'NOT MET'}")

    print("=" * 80)

    # ── AntiNode Intervention Statistics ─────────────────────────────────
    print("\n--- AntiNode Intervention Statistics ---")

    n_complied = sum(1 for r in results if r.get("anti_complied", False))
    n_changed = sum(1 for r in results if r.get("anti_changed_outcome", False))
    n_gt_prevented = sum(1 for r in results if r.get("groupthink_prevented", False))
    n_total = len(results)

    print(f"  AntiNode compliance (argued against majority): "
          f"{n_complied}/{n_total} ({n_complied/n_total:.0%})")
    print(f"  Outcomes changed by AntiNode: "
          f"{n_changed}/{n_total} ({n_changed/n_total:.0%})")
    print(f"  Groupthink prevented: "
          f"{n_gt_prevented}/{n_total} ({n_gt_prevented/n_total:.0%})")

    if n_changed > 0:
        changed = [r for r in results if r.get("anti_changed_outcome", False)]
        anti_correct = sum(1 for r in changed if r["is_correct"])
        pre_anti_correct = sum(1 for r in changed if r.get("pre_anti_correct", False))
        net = anti_correct - pre_anti_correct

        print(f"\n  When AntiNode changed the outcome ({n_changed} tasks):")
        print(f"    v9c correct:       {anti_correct}/{n_changed} ({anti_correct/n_changed:.0%})")
        print(f"    Pre-anti correct:  {pre_anti_correct}/{n_changed} ({pre_anti_correct/n_changed:.0%})")
        print(f"    Net impact:        {net:+d} tasks ({net/n_total:+.1%}pp overall)")

        # Helpful vs harmful
        helpful = sum(1 for r in changed
                      if r["is_correct"] and not r.get("pre_anti_correct", False))
        harmful = sum(1 for r in changed
                      if not r["is_correct"] and r.get("pre_anti_correct", False))
        neutral = n_changed - helpful - harmful
        print(f"    Helpful (wrong->right): {helpful}")
        print(f"    Harmful (right->wrong): {harmful}")
        print(f"    Neutral (same result):  {neutral}")

    # Per task set
    print(f"\n  {'Task Set':<20} | {'Complied':>8} | {'Changed':>8} | "
          f"{'GT Prev':>8} | {'Helpful':>8} | {'Harmful':>8}")
    print("  " + "-" * 70)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_r = [r for r in results if r["task_set"] == ts]
        ts_comp = sum(1 for r in ts_r if r.get("anti_complied", False))
        ts_changed = [r for r in ts_r if r.get("anti_changed_outcome", False)]
        ts_gt = sum(1 for r in ts_r if r.get("groupthink_prevented", False))
        ts_help = sum(1 for r in ts_changed
                      if r["is_correct"] and not r.get("pre_anti_correct", False))
        ts_harm = sum(1 for r in ts_changed
                      if not r["is_correct"] and r.get("pre_anti_correct", False))
        print(f"  {ts:<20} | {ts_comp:>8} | {len(ts_changed):>8} | "
              f"{ts_gt:>8} | {ts_help:>8} | {ts_harm:>8}")

    print("=" * 80)

    # ── Mirror Effect Check ─────────────────────────────────────────────
    print("\n--- Mirror Effect Check ---")
    print("(Does AntiNode just mirror the bias in the opposite direction?)")

    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_r = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_r)

        # Pre-anti balance
        pre_correct = [r for r in ts_r if r["label"] is True]
        pre_incorrect = [r for r in ts_r if r["label"] is False]
        pre_c_acc = sum(1 for r in pre_correct if r.get("pre_anti_correct", False)) / len(pre_correct) if pre_correct else 0
        pre_i_acc = sum(1 for r in pre_incorrect if r.get("pre_anti_correct", False)) / len(pre_incorrect) if pre_incorrect else 0

        print(f"\n  {ts}:")
        print(f"    Pre-anti:  CORRECT={pre_c_acc:.0%}, INCORRECT={pre_i_acc:.0%} "
              f"(bias={abs(pre_c_acc - pre_i_acc):.0%}pp)")
        print(f"    Post-anti: CORRECT={st['correct_acc']:.0%}, INCORRECT={st['incorrect_acc']:.0%} "
              f"(bias={abs(st['correct_acc'] - st['incorrect_acc']):.0%}pp)")
        bias_change = abs(st["correct_acc"] - st["incorrect_acc"]) - abs(pre_c_acc - pre_i_acc)
        mirror = "REDUCED" if bias_change < 0 else "INCREASED" if bias_change > 0 else "UNCHANGED"
        print(f"    Bias change: {bias_change:+.0%}pp -> {mirror}")

    # ── Groupthink distribution ─────────────────────────────────────────
    print(f"\n{'Task Set':<20} | {'All Correct':>12} | {'All Incorrect':>14} | {'Split':>6}")
    print("-" * 60)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_r = [r for r in results if r["task_set"] == ts]
        ac = sum(1 for r in ts_r if r.get("pre_anti_groupthink") == "all_correct")
        ai = sum(1 for r in ts_r if r.get("pre_anti_groupthink") == "all_incorrect")
        sp = sum(1 for r in ts_r if r.get("pre_anti_groupthink") == "split")
        print(f"{ts:<20} | {ac:>12} | {ai:>14} | {sp:>6}")

    print("=" * 80)

    # ── Save summary ────────────────────────────────────────────────────
    summary = {
        "experiment": "v9c",
        "description": "best_fixed + AntiNode contrarian bias correction",
        "overall_acc": round(overall_acc, 3),
        "overall_total": overall_total,
        "overall_correct": overall_correct,
        "anti_model": "mistral:7b",
        "anti_weight": 0.5,
        "anti_compliance_rate": round(n_complied / n_total, 3),
        "anti_changed_outcomes": n_changed,
        "groupthink_prevented": n_gt_prevented,
        "per_task_set": {},
    }

    if n_changed > 0:
        changed = [r for r in results if r.get("anti_changed_outcome", False)]
        helpful = sum(1 for r in changed
                      if r["is_correct"] and not r.get("pre_anti_correct", False))
        harmful = sum(1 for r in changed
                      if not r["is_correct"] and r.get("pre_anti_correct", False))
        summary["anti_helpful"] = helpful
        summary["anti_harmful"] = harmful
        summary["anti_net_impact"] = helpful - harmful

    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        ts_changed = [r for r in ts_results if r.get("anti_changed_outcome", False)]
        st["anti_changed"] = len(ts_changed)
        st["groupthink_prevented"] = sum(1 for r in ts_results
                                         if r.get("groupthink_prevented", False))
        summary["per_task_set"][ts] = st

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
