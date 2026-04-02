"""
run_single_agent_cfr.py

Single-Agent CFR Comparison Experiment
Validates whether the CFR gradient (100%→82%→59%→55%) observed in multi-agent
v9d is specific to multi-agent interaction, or whether a single agent's
verbalized confidence produces the same pattern.

Comparison reference (v9d multi-agent CFR):
  world_consistency: 100%
  math_elementary:    82%
  math_middle:        59%
  math_high:          55%
"""

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx
from scipy import stats as sp_stats

sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")

from task_generator import generate_tasks as generate_world_consistency_tasks
from math_task_generator import generate_math_tasks
from middle_school_task_generator import generate_middle_school_tasks
from high_school_task_generator import generate_high_school_tasks

# ── Configuration ─────────────────────────────────────────────────────────

MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"
CONFIDENCE_THRESHOLD = 0.8  # "confident judgment" = multi-agent "unanimous"

RESULTS_DIR = Path("results/single_agent_cfr")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "single_agent_cfr_results.jsonl"
SUMMARY_PATH = RESULTS_DIR / "single_agent_cfr_summary.json"

_client = httpx.Client(timeout=120.0)

# v9d multi-agent CFR reference values
V9D_CFR = {
    "world_consistency": 1.00,
    "math_elementary": 0.82,
    "math_middle": 0.59,
    "math_high": 0.55,
}


# ── LLM call ──────────────────────────────────────────────────────────────

def call_llm(prompt: str) -> dict:
    """Call single LLM agent via Ollama, requesting JSON output."""
    response = _client.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
    )
    response.raise_for_status()
    raw = response.json()["response"].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"decision": "UNKNOWN", "confidence": 0.5, "reasoning": raw}


def build_prompt(task_input: str) -> str:
    """Build evaluation prompt for single agent."""
    return f"""You are evaluating whether the following statement is correct.

{task_input}

Analyze step by step, then determine if the statement is CORRECT or INCORRECT.

Respond ONLY in the following JSON format (nothing else):
{{
  "decision": "CORRECT" or "INCORRECT",
  "confidence": 0.0 to 1.0,
  "reasoning": "Step-by-step analysis in 2-3 sentences"
}}"""


# ── Task loader (identical to v9b) ────────────────────────────────────────

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
            "label": t.label,
            "task_input": f"Rule: {t.world_rule}\nStatement: {t.question}",
        })

    return tasks


def verdict_matches(decision: str, label: bool) -> bool:
    """Check if verdict matches ground truth label."""
    if decision in ("CORRECT", "CONSISTENT"):
        return label is True
    elif decision in ("INCORRECT", "CONTRADICTION"):
        return label is False
    return False


# ── Statistical helpers ───────────────────────────────────────────────────

def binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple:
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


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Single Agent CFR Comparison Experiment")
    print(f"Model: {MODEL} (single agent)")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print("=" * 70)

    # ── Phase 1: Load tasks ───────────────────────────────────────────
    print("\nPhase 1: Loading tasks...")
    tasks = load_all_tasks()

    by_set = defaultdict(int)
    for t in tasks:
        by_set[t["task_set"]] += 1
    print(f"  Total tasks: {len(tasks)}")
    for s, n in sorted(by_set.items()):
        print(f"    {s}: {n}")

    # ── Phase 2: Resume support ───────────────────────────────────────
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
        # ── Phase 3: Run single-agent evaluation ──────────────────────
        start_idx = len(existing)
        results = list(existing)
        mode = "a" if start_idx > 0 else "w"

        if start_idx > 0:
            print(f"  Resuming from task {start_idx}...")

        print(f"\nPhase 3: Running single-agent evaluation ({len(tasks)} tasks)...")
        total_start = time.time()

        with open(RESULTS_PATH, mode, encoding="utf-8") as f_results:
            for i, task in enumerate(tasks):
                if i < start_idx:
                    continue

                t0 = time.time()
                try:
                    prompt = build_prompt(task["task_input"])
                    output = call_llm(prompt)

                    decision = output.get("decision", "UNKNOWN")
                    confidence = float(output.get("confidence", 0.5))
                    confidence = min(max(confidence, 0.0), 1.0)
                    reasoning = output.get("reasoning", "")
                except Exception as e:
                    decision = "UNKNOWN"
                    confidence = 0.5
                    reasoning = f"ERROR: {e}"

                elapsed = time.time() - t0
                is_correct = verdict_matches(decision, task["label"])
                is_confident = confidence >= CONFIDENCE_THRESHOLD

                record = {
                    "task_id": task["task_id"],
                    "task_set": task["task_set"],
                    "task_type": task["task_type"],
                    "question": task["question"],
                    "label": task["label"],
                    "decision": decision,
                    "confidence": round(confidence, 4),
                    "reasoning": reasoning,
                    "is_correct": is_correct,
                    "is_confident": is_confident,
                    "confident_and_wrong": is_confident and not is_correct,
                    "elapsed_sec": round(elapsed, 2),
                }
                results.append(record)
                f_results.write(json.dumps(record, ensure_ascii=False) + "\n")
                f_results.flush()

                status = "OK" if is_correct else "NG"
                conf_tag = f"c={confidence:.2f}"
                flag = " [CFR]" if is_confident and not is_correct else ""
                print(
                    f"  [{i+1:3d}/{len(tasks)}] {status} {decision:14s} "
                    f"{conf_tag:8s}{flag:6s} ({elapsed:.1f}s) "
                    f"[{task['task_set']:18s}] {task['question'][:40]}"
                )

        total_elapsed = time.time() - total_start
        print(f"\nAll {len(tasks)} tasks complete in {total_elapsed:.0f}s "
              f"({total_elapsed/60:.1f}min)")

    # ── Phase 4: Analysis ─────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  RESULTS: Single Agent CFR Comparison")
    print("=" * 70)

    # Per task-set stats
    task_sets = ["world_consistency", "math_elementary", "math_middle", "math_high"]

    print(f"\n{'Task Set':<20} | {'Accuracy':>10} | {'Confident%':>10} | "
          f"{'CFR':>8} | {'v9d CFR':>8}")
    print("-" * 70)

    cfr_by_set = {}
    summary_per_set = {}

    for ts in task_sets:
        ts_results = [r for r in results if r["task_set"] == ts]
        n_total = len(ts_results)
        n_correct = sum(1 for r in ts_results if r["is_correct"])
        n_confident = sum(1 for r in ts_results if r["is_confident"])
        n_cfr = sum(1 for r in ts_results if r["confident_and_wrong"])

        accuracy = n_correct / n_total if n_total > 0 else 0
        confident_pct = n_confident / n_total if n_total > 0 else 0
        cfr = n_cfr / n_confident if n_confident > 0 else None

        cfr_by_set[ts] = cfr
        lo, hi = binomial_ci(n_correct, n_total)

        cfr_str = f"{cfr:.0%}" if cfr is not None else "N/A"
        v9d_str = f"{V9D_CFR[ts]:.0%}"

        print(f"{ts:<20} | {accuracy:>9.1%} | {confident_pct:>9.0%} | "
              f"{cfr_str:>8} | {v9d_str:>8}")

        summary_per_set[ts] = {
            "n_total": n_total,
            "n_correct": n_correct,
            "accuracy": round(accuracy, 4),
            "accuracy_ci_95": [round(lo, 4), round(hi, 4)],
            "n_confident": n_confident,
            "confident_pct": round(confident_pct, 4),
            "n_confident_wrong": n_cfr,
            "cfr": round(cfr, 4) if cfr is not None else None,
            "v9d_cfr": V9D_CFR[ts],
        }

    # ── Overall stats ─────────────────────────────────────────────────
    n_total_all = len(results)
    n_correct_all = sum(1 for r in results if r["is_correct"])
    n_confident_all = sum(1 for r in results if r["is_confident"])
    n_cfr_all = sum(1 for r in results if r["confident_and_wrong"])

    overall_acc = n_correct_all / n_total_all if n_total_all > 0 else 0
    overall_cfr = n_cfr_all / n_confident_all if n_confident_all > 0 else None

    lo_all, hi_all = binomial_ci(n_correct_all, n_total_all)
    cfr_all_str = f"{overall_cfr:.0%}" if overall_cfr is not None else "N/A"
    print(f"{'Overall':<20} | {overall_acc:>9.1%} | "
          f"{n_confident_all/n_total_all:>9.0%} | {cfr_all_str:>8} |")

    # ── KEY COMPARISON ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("KEY QUESTION: Does single-agent CFR show the same gradient?")
    print("=" * 70)

    sa_values = []
    v9d_values = []
    print(f"\n  {'Task Set':<20} | {'v9d (multi)':>12} | {'Single':>12} | {'Delta':>8}")
    print("  " + "-" * 58)
    for ts in task_sets:
        v9d_val = V9D_CFR[ts]
        sa_val = cfr_by_set[ts]
        v9d_values.append(v9d_val)
        sa_values.append(sa_val if sa_val is not None else 0)
        sa_str = f"{sa_val:.0%}" if sa_val is not None else "N/A"
        delta = (sa_val - v9d_val) if sa_val is not None else None
        delta_str = f"{delta:+.0%}pp" if delta is not None else "N/A"
        print(f"  {ts:<20} | {v9d_val:>11.0%} | {sa_str:>12} | {delta_str:>8}")

    # Gradient summary
    print(f"\n  Gradient comparison:")
    v9d_grad = " -> ".join(f"{v:.0%}" for v in v9d_values)
    sa_grad = " -> ".join(
        f"{v:.0%}" if cfr_by_set[ts] is not None else "N/A"
        for v, ts in zip(sa_values, task_sets)
    )
    print(f"    v9d (multi-agent):   {v9d_grad}")
    print(f"    single agent:        {sa_grad}")

    # Determine conclusion
    # Check if gradients are "same" (monotonically decreasing, similar spread)
    valid_sa = [v for v in sa_values if v is not None]
    if len(valid_sa) >= 3:
        is_decreasing = all(valid_sa[i] >= valid_sa[i+1] for i in range(len(valid_sa)-1))
        spread = max(valid_sa) - min(valid_sa)
        v9d_spread = max(v9d_values) - min(v9d_values)

        print(f"\n  Single-agent gradient decreasing: {is_decreasing}")
        print(f"  Single-agent spread: {spread:.0%}pp  vs  v9d spread: {v9d_spread:.0%}pp")

        if is_decreasing and spread >= 0.15:
            print("\n  >> SAME gradient detected")
            print("     CFR gradient is NOT specific to multi-agent interaction")
            print("     Abstract claim needs to be scoped to multi-agent amplification")
        else:
            print("\n  >> DIFFERENT gradient detected")
            print("     CFR gradient IS specific to multi-agent interaction")
            print("     Major concern 1 (reviewer critique) is resolved")
    else:
        print("\n  Insufficient confident judgments to determine gradient")

    # ── CFR by task type (detailed) ───────────────────────────────────
    print("\n" + "=" * 70)
    print("CFR by task type (detailed):")
    print("=" * 70)

    type_details = {}
    for ts in task_sets:
        ts_results = [r for r in results if r["task_set"] == ts]
        types = set(r["task_type"] for r in ts_results)

        print(f"\n{ts}:")
        print(f"  {'task_type':<20} | {'n':>4} | {'confident':>9} | "
              f"{'cfr_n':>5} | {'CFR':>6}")
        print("  " + "-" * 52)

        type_details[ts] = {}
        for tt in sorted(types):
            tt_results = [r for r in ts_results if r["task_type"] == tt]
            n = len(tt_results)
            n_conf = sum(1 for r in tt_results if r["is_confident"])
            n_cfr = sum(1 for r in tt_results if r["confident_and_wrong"])
            cfr = n_cfr / n_conf if n_conf > 0 else None
            cfr_str = f"{cfr:.0%}" if cfr is not None else "N/A"
            print(f"  {tt:<20} | {n:>4} | {n_conf:>9} | "
                  f"{n_cfr:>5} | {cfr_str:>6}")
            type_details[ts][tt] = {
                "n": n,
                "n_confident": n_conf,
                "n_confident_wrong": n_cfr,
                "cfr": round(cfr, 4) if cfr is not None else None,
            }

    # ── Confidence distribution ───────────────────────────────────────
    print("\n" + "=" * 70)
    print("Confidence distribution:")
    print("=" * 70)

    for ts in task_sets:
        ts_results = [r for r in results if r["task_set"] == ts]
        confs = [r["confidence"] for r in ts_results]
        if confs:
            import statistics
            mean_c = statistics.mean(confs)
            median_c = statistics.median(confs)
            correct_confs = [r["confidence"] for r in ts_results if r["is_correct"]]
            wrong_confs = [r["confidence"] for r in ts_results if not r["is_correct"]]
            mean_correct = statistics.mean(correct_confs) if correct_confs else 0
            mean_wrong = statistics.mean(wrong_confs) if wrong_confs else 0
            print(f"  {ts:<20}: mean={mean_c:.3f} median={median_c:.3f} "
                  f"| correct={mean_correct:.3f} wrong={mean_wrong:.3f} "
                  f"| gap={mean_correct - mean_wrong:+.3f}")

    print("=" * 70)

    # ── Save summary ──────────────────────────────────────────────────
    summary = {
        "experiment": "single_agent_cfr",
        "model": MODEL,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "n_tasks": n_total_all,
        "overall_accuracy": round(overall_acc, 4),
        "overall_accuracy_ci_95": [round(lo_all, 4), round(hi_all, 4)],
        "overall_cfr": round(overall_cfr, 4) if overall_cfr is not None else None,
        "n_confident_total": n_confident_all,
        "n_confident_wrong_total": n_cfr_all,
        "per_task_set": summary_per_set,
        "cfr_by_task_type": type_details,
        "v9d_reference": V9D_CFR,
    }

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {RESULTS_DIR}/")
    print(f"  {RESULTS_PATH}")
    print(f"  {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
