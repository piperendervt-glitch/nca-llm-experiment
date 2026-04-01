"""
run_v9d.py

Run NCA v9d: best_fixed + Game-Theory AntiNode (Veto + Level-K) on 350 tasks.

One-variable experiment: game-theory veto is the ONLY change from best_fixed.
  - Models: qwen2.5:7b + llama3:latest + mistral:7b (fixed)
  - agree: [30, 80, 80] (fixed)
  - steps: 3 (fixed)
  - role: fixed (fixed)
  - Veto AntiNode: mistral:7b, unanimous-only, Level-K selection (NEW)
  - NO MetaAgent (v9a), NO dynamic weighting (v9b), NO blind contrarian (v9c)
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
from nca_network_v9d import run_v9d, get_anti_node

RESULTS_DIR = Path("results/v9d")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "v9d_results.jsonl"
VETO_LOG_PATH = RESULTS_DIR / "v9d_veto_log.jsonl"
SUMMARY_PATH = RESULTS_DIR / "v9d_summary.jsonl"


# ── Statistical helpers ────────────────────────────────────────────────────

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


# ── Task loader ───────────────────────────────────────────────────────────

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
    print("Phase 1: Loading tasks...")
    tasks = load_all_tasks()

    by_set = defaultdict(int)
    for t in tasks:
        by_set[t["task_set"]] += 1
    print(f"  Total tasks: {len(tasks)}")
    for s, n in sorted(by_set.items()):
        print(f"    {s}: {n}")

    anti_node = get_anti_node()
    print(f"  Initial risk scores: {anti_node.get_risk_scores()}")

    # ── Resume support ──────────────────────────────────────────────────
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
        print(f"\nPhase 3: Running best_fixed + Veto AntiNode ({len(tasks)} tasks)...")
        start_idx = len(existing)
        results = list(existing)
        mode = "a" if start_idx > 0 else "w"

        # Replay risk updates for resume
        if start_idx > 0:
            print(f"  Resuming from task {start_idx}, replaying risk updates...")
            for r in existing:
                was_unanimous = r.get("pre_anti_groupthink", "") in (
                    "all_correct", "all_incorrect")
                if was_unanimous:
                    anti_node.update_risk(
                        r["task_type"], True, r.get("pre_anti_correct", False))
            print(f"  Risk scores after replay: {anti_node.get_risk_scores()}")

        total_start = time.time()

        with open(RESULTS_PATH, mode, encoding="utf-8") as f_results, \
             open(VETO_LOG_PATH, mode, encoding="utf-8") as f_veto:
            for i, task in enumerate(tasks):
                if i < start_idx:
                    continue

                t0 = time.time()
                try:
                    nca_result = run_v9d(task["task_input"], task["task_type"])
                    verdict = nca_result["final_verdict"]
                    pre_anti = nca_result.get("pre_anti_majority", "")
                    pre_anti_gt = nca_result.get("pre_anti_groupthink", "unknown")
                    anti_intervened = nca_result.get("anti_intervened", False)
                    anti_reason = nca_result.get("anti_reason", "")
                    anti_label = nca_result.get("anti_label", "")
                    anti_conf = nca_result.get("anti_confidence", 0.0)
                    anti_reasoning = nca_result.get("anti_reasoning", "")
                    anti_complied = nca_result.get("anti_complied", False)
                    anti_changed = nca_result.get("anti_changed_outcome", False)
                    uncertainty = nca_result.get("uncertainty_flagged", False)
                    agg_scores = nca_result.get("aggregation_scores", {})
                    vote_dist = nca_result.get("vote_distribution", {})
                    steps = nca_result.get("steps", [])
                except Exception as e:
                    verdict = f"ERROR: {e}"
                    pre_anti = ""; pre_anti_gt = "unknown"
                    anti_intervened = False; anti_reason = f"ERROR: {e}"
                    anti_label = ""; anti_conf = 0.0; anti_reasoning = ""
                    anti_complied = False; anti_changed = False
                    uncertainty = False; agg_scores = {}; vote_dist = {}
                    steps = []

                elapsed = time.time() - t0
                is_correct = verdict_matches(verdict, task["label"])
                pre_anti_correct = verdict_matches(pre_anti, task["label"])

                # Online learning: update risk scores
                was_unanimous = pre_anti_gt in ("all_correct", "all_incorrect")
                anti_node.update_risk(
                    task["task_type"], was_unanimous, pre_anti_correct)

                record = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "question": task["question"],
                    "label": task["label"],
                    "prediction": verdict,
                    "is_correct": is_correct,
                    "pattern_used": "best_fixed_veto",
                    "elapsed_sec": round(elapsed, 2),
                    "steps": steps,
                    # Pre-anti
                    "pre_anti_majority": pre_anti,
                    "pre_anti_correct": pre_anti_correct,
                    "pre_anti_groupthink": pre_anti_gt,
                    "vote_distribution": vote_dist,
                    # AntiNode
                    "anti_intervened": anti_intervened,
                    "anti_reason": anti_reason,
                    "anti_label": anti_label,
                    "anti_confidence": anti_conf,
                    "anti_reasoning": anti_reasoning,
                    "anti_complied": anti_complied,
                    "anti_changed_outcome": anti_changed,
                    "uncertainty_flagged": uncertainty,
                    "aggregation_scores": agg_scores,
                }
                results.append(record)
                f_results.write(json.dumps(record, ensure_ascii=False) + "\n")
                f_results.flush()

                # Veto log
                veto_entry = {
                    "task_idx": i,
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "label": task["label"],
                    "pre_anti_groupthink": pre_anti_gt,
                    "anti_intervened": anti_intervened,
                    "anti_reason": anti_reason,
                    "anti_label": anti_label,
                    "anti_complied": anti_complied,
                    "anti_changed_outcome": anti_changed,
                    "uncertainty_flagged": uncertainty,
                    "is_correct": is_correct,
                    "risk_scores": anti_node.get_risk_scores(),
                }
                f_veto.write(json.dumps(veto_entry, ensure_ascii=False) + "\n")
                f_veto.flush()

                veto_tag = " [VETO]" if anti_intervened else ""
                unc_tag = " [UNC]" if uncertainty else ""
                status = "OK" if is_correct else "NG"
                print(
                    f"  [{i+1:3d}/{len(tasks)}] {status} {verdict:14s}"
                    f"{veto_tag:7s}{unc_tag:6s} ({elapsed:.1f}s) "
                    f"[{task['task_set']:18s}] {task['question'][:40]}"
                )

        total_elapsed = time.time() - total_start
        print(f"\nAll {len(tasks)} tasks complete in {total_elapsed:.0f}s "
              f"({total_elapsed/3600:.1f}h)")

    # ── Phase 4: Analysis ───────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  NCA v9d: Game-Theory AntiNode (Veto + Level-K) Results")
    print("=" * 80)

    # Baselines
    v8_scores = {
        "world_consistency": (66, 100), "math_elementary": (85, 100),
        "math_middle": (57, 75), "math_high": (61, 75),
    }
    v8_overall = (269, 350)
    v9b_scores = {
        "world_consistency": (69, 100), "math_elementary": (87, 100),
        "math_middle": (58, 75), "math_high": (63, 75),
    }
    v9b_overall = (277, 350)
    v9c_scores = {
        "world_consistency": (63, 100), "math_elementary": (83, 100),
        "math_middle": (57, 75), "math_high": (57, 75),
    }
    v9c_overall = (260, 350)

    # Main table
    print(f"\n{'Task Set':<20} | {'v9d':>18} | {'v9c':>5} | {'v9b':>5} | "
          f"{'v8':>5} | {'Dv8':>5} | {'Dv9b':>5}")
    print("-" * 80)

    overall_correct = 0
    overall_total = 0
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_results = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_results)
        v8_k, v8_n = v8_scores[ts]
        v9b_k, v9b_n = v9b_scores[ts]
        v9c_k, v9c_n = v9c_scores[ts]
        ci_str = fmt_ci(st["n_correct"], st["total"])
        print(f"{ts:<20} | {ci_str:>18} | {v9c_k/v9c_n:>4.0%} | "
              f"{v9b_k/v9b_n:>4.0%} | {v8_k/v8_n:>4.0%} | "
              f"{st['overall'] - v8_k/v8_n:>+4.0%}pp | "
              f"{st['overall'] - v9b_k/v9b_n:>+4.0%}pp")
        overall_correct += st["n_correct"]
        overall_total += st["total"]

    overall_acc = overall_correct / overall_total if overall_total else 0
    ci_overall = fmt_ci(overall_correct, overall_total)
    v8_ov = v8_overall[0] / v8_overall[1]
    v9b_ov = v9b_overall[0] / v9b_overall[1]
    v9c_ov = v9c_overall[0] / v9c_overall[1]
    print(f"{'Overall':<20} | {ci_overall:>18} | {v9c_ov:>4.0%} | "
          f"{v9b_ov:>4.0%} | {v8_ov:>4.0%} | "
          f"{overall_acc - v8_ov:>+4.0%}pp | {overall_acc - v9b_ov:>+4.0%}pp")

    # ── Statistical tests ───────────────────────────────────────────────
    print("\n--- Statistical Tests ---")
    for label, ref_overall, ref_scores in [
        ("v9d vs v8", v8_overall, v8_scores),
        ("v9d vs v9b", v9b_overall, v9b_scores),
        ("v9d vs v9c", v9c_overall, v9c_scores),
    ]:
        z, p = two_prop_ztest(overall_correct, overall_total, *ref_overall)
        print(f"\n{label} overall: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")
        for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
            ts_r = [r for r in results if r["task_set"] == ts]
            k1 = sum(1 for r in ts_r if r["is_correct"])
            n1 = len(ts_r)
            k2, n2 = ref_scores[ts]
            z, p = two_prop_ztest(k1, n1, k2, n2)
            print(f"  {ts}: z={z:.3f}, p={p:.4f} ({fmt_sig(p)})")

    print("=" * 80)

    # ── Veto Intervention Statistics ────────────────────────────────────
    print("\n--- AntiNode (Veto) Intervention Statistics ---")

    n_unanimous = sum(1 for r in results
                      if r.get("pre_anti_groupthink") in ("all_correct", "all_incorrect"))
    n_intervened = sum(1 for r in results if r.get("anti_intervened", False))
    n_changed = sum(1 for r in results if r.get("anti_changed_outcome", False))
    n_uncertainty = sum(1 for r in results if r.get("uncertainty_flagged", False))
    n_complied = sum(1 for r in results
                     if r.get("anti_intervened") and r.get("anti_complied", False))
    n_total = len(results)

    print(f"  Unanimous (3-0) tasks:      {n_unanimous}/{n_total} ({n_unanimous/n_total:.0%})")
    print(f"  Intervention triggered:     {n_intervened}/{n_unanimous} unanimous "
          f"({n_intervened/n_unanimous:.0%})" if n_unanimous else "  No unanimous tasks")
    print(f"  Outcomes changed:           {n_changed}/{n_total} ({n_changed/n_total:.0%})")
    print(f"  Uncertainty flags:          {n_uncertainty}/{n_total} ({n_uncertainty/n_total:.0%})")
    if n_intervened > 0:
        print(f"  AntiNode compliance:        {n_complied}/{n_intervened} "
              f"({n_complied/n_intervened:.0%})")

    # Intervention accuracy analysis
    if n_intervened > 0:
        intervened = [r for r in results if r.get("anti_intervened", False)]
        int_correct = sum(1 for r in intervened if r["is_correct"])
        int_pre_correct = sum(1 for r in intervened if r.get("pre_anti_correct", False))
        print(f"\n  Intervened tasks accuracy:   {int_correct}/{n_intervened} "
              f"({int_correct/n_intervened:.0%})")
        print(f"  Pre-anti accuracy (same):    {int_pre_correct}/{n_intervened} "
              f"({int_pre_correct/n_intervened:.0%})")

    # Per task set
    print(f"\n  {'Task Set':<20} | {'Unanimous':>9} | {'Intervened':>10} | "
          f"{'Changed':>8} | {'Unc Flag':>9}")
    print("  " + "-" * 65)
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_r = [r for r in results if r["task_set"] == ts]
        ts_unan = sum(1 for r in ts_r
                      if r.get("pre_anti_groupthink") in ("all_correct", "all_incorrect"))
        ts_int = sum(1 for r in ts_r if r.get("anti_intervened", False))
        ts_chg = sum(1 for r in ts_r if r.get("anti_changed_outcome", False))
        ts_unc = sum(1 for r in ts_r if r.get("uncertainty_flagged", False))
        print(f"  {ts:<20} | {ts_unan:>9} | {ts_int:>10} | {ts_chg:>8} | {ts_unc:>9}")

    print("=" * 80)

    # ── Risk Score Evolution ────────────────────────────────────────────
    print("\n--- Risk Score Evolution (Level-K Learning) ---")
    initial_risks = {
        "sequence": 0.35, "algebraic_expr": 0.40, "simultaneous_eq": 0.45,
        "polynomial": 0.40, "quadratic_ineq": 0.50, "area": 0.45,
        "world_consistency": 0.35,
    }
    final_risks = anti_node.get_risk_scores()
    print(f"\n  {'Task Type':<22} | {'Initial':>8} | {'Final':>8} | {'Delta':>8}")
    print("  " + "-" * 55)
    all_types = sorted(set(list(initial_risks.keys()) + list(final_risks.keys())))
    for tt in all_types:
        init = initial_risks.get(tt, 0.20)
        final = final_risks.get(tt, 0.20)
        delta = final - init
        marker = " *" if abs(delta) > 0.05 else ""
        print(f"  {tt:<22} | {init:>7.3f} | {final:>7.3f} | {delta:>+7.3f}{marker}")

    print("=" * 80)

    # ── CORRECT/INCORRECT Balance ───────────────────────────────────────
    print("\n--- CORRECT/INCORRECT Balance ---")
    print(f"\n  {'Task Set':<20} | {'v9d C':>6} | {'v9d I':>6} | "
          f"{'v9c C':>6} | {'v9c I':>6} | {'v9b C':>6} | {'v9b I':>6}")
    print("  " + "-" * 70)

    v9c_bal = {"world_consistency": (0.58, 0.68), "math_elementary": (0.73, 0.94),
               "math_middle": (0.85, 0.67), "math_high": (0.82, 0.69)}
    v9b_bal = {"world_consistency": (0.72, 0.66), "math_elementary": (0.81, 0.94),
               "math_middle": (0.82, 0.72), "math_high": (0.85, 0.83)}

    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_r = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_r)
        c9c, i9c = v9c_bal[ts]
        c9b, i9b = v9b_bal[ts]
        print(f"  {ts:<20} | {st['correct_acc']:>5.0%} | {st['incorrect_acc']:>5.0%} | "
              f"{c9c:>5.0%} | {i9c:>5.0%} | {c9b:>5.0%} | {i9b:>5.0%}")

    wc_r = [r for r in results if r["task_set"] == "world_consistency"]
    wc_st = compute_stats(wc_r)
    target_met = wc_st["correct_acc"] >= 0.65 and wc_st["incorrect_acc"] >= 0.65
    print(f"\n  WC target (~70%/70%): C={wc_st['correct_acc']:.0%}, "
          f"I={wc_st['incorrect_acc']:.0%} -> {'MET' if target_met else 'NOT MET'}")

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
        "experiment": "v9d",
        "description": "best_fixed + game-theory AntiNode (veto + Level-K)",
        "overall_acc": round(overall_acc, 3),
        "overall_total": overall_total,
        "overall_correct": overall_correct,
        "anti_model": "mistral:7b",
        "n_unanimous": n_unanimous,
        "n_intervened": n_intervened,
        "n_changed": n_changed,
        "n_uncertainty_flags": n_uncertainty,
        "initial_risk_scores": initial_risks,
        "final_risk_scores": final_risks,
        "per_task_set": {},
    }
    for ts in ["world_consistency", "math_elementary", "math_middle", "math_high"]:
        ts_r = [r for r in results if r["task_set"] == ts]
        st = compute_stats(ts_r)
        st["n_intervened"] = sum(1 for r in ts_r if r.get("anti_intervened", False))
        st["n_uncertainty"] = sum(1 for r in ts_r if r.get("uncertainty_flagged", False))
        summary["per_task_set"][ts] = st

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
