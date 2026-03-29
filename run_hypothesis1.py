"""
run_hypothesis1.py

Run hypothesis 1 (NCA + confidence-weighted voting) and self-consistency baseline,
then print comparison results.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")
sys.path.insert(0, str(Path(__file__).parent))

from task_generator import generate_tasks
from nca_network_h1 import run_nca_h1
from self_consistency import run_self_consistency

H1_PATH = Path("results/nca_h1_results.jsonl")
SC_PATH = Path("results/self_consistency_results.jsonl")
H1_PATH.parent.mkdir(parents=True, exist_ok=True)


def verdict_to_bool(verdict: str) -> bool | None:
    if verdict == "CONSISTENT":
        return True
    elif verdict == "CONTRADICTION":
        return False
    return None


def compute_stats(results: list) -> dict:
    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])

    cons = [r for r in results if r["label"] is True]
    contr = [r for r in results if r["label"] is False]
    cons_correct = sum(1 for r in cons if r["is_correct"])
    contr_correct = sum(1 for r in contr if r["is_correct"])

    # Groupthink stats (only for NCA results with steps)
    all_contradiction = 0
    all_consistent = 0
    split = 0
    for r in results:
        steps = r.get("steps", [])
        if not steps:
            # Self-consistency: check outputs directly
            outputs = r.get("outputs", [])
            if not outputs:
                continue
            verdicts = [o.get("decision", "UNKNOWN") if isinstance(o, dict) else "UNKNOWN" for o in outputs]
        else:
            final_outputs = steps[-1].get("outputs", [])
            if not final_outputs:
                continue
            verdicts = [o.get("decision", "UNKNOWN") if isinstance(o, dict) else "UNKNOWN" for o in final_outputs]

        if all(v == "CONTRADICTION" for v in verdicts):
            all_contradiction += 1
        elif all(v == "CONSISTENT" for v in verdicts):
            all_consistent += 1
        else:
            split += 1

    return {
        "overall": correct / total if total else 0,
        "consistent_acc": cons_correct / len(cons) if cons else 0,
        "contradiction_acc": contr_correct / len(contr) if contr else 0,
        "groupthink_all_contradiction": all_contradiction,
        "groupthink_all_consistent": all_consistent,
        "split": split,
    }


def run_experiment(name: str, run_fn, tasks: list, out_path: Path) -> list:
    # Resume support
    existing = []
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
        if len(existing) >= len(tasks):
            print(f"  [{name}] Already complete ({len(existing)} results)")
            return existing

    start_idx = len(existing)
    results = list(existing)
    correct_count = sum(1 for r in results if r["is_correct"])

    mode = "a" if start_idx > 0 else "w"
    if start_idx > 0:
        print(f"  [{name}] Resuming from task {start_idx + 1}")

    t_start = time.time()

    with open(out_path, mode, encoding="utf-8") as f:
        for i, task in enumerate(tasks):
            if i < start_idx:
                continue

            task_input = f"World rule: {task.world_rule}\nStatement: {task.question}"

            t0 = time.time()
            try:
                result = run_fn(task_input)
                verdict = result["final_verdict"]
                prediction = verdict_to_bool(verdict)
            except Exception as e:
                prediction = None
                verdict = f"ERROR: {e}"
                result = {}

            elapsed = time.time() - t0
            is_correct = (prediction == task.label) if prediction is not None else False
            if is_correct:
                correct_count += 1

            record = {
                "task_id": task.task_id,
                "question": task.question,
                "world_rule": task.world_rule,
                "label": task.label,
                "prediction": prediction,
                "is_correct": is_correct,
                "raw_output": verdict,
                "elapsed_sec": round(elapsed, 2),
            }
            # Store steps for NCA, outputs for self-consistency
            if "steps" in result:
                record["steps"] = result["steps"]
            if "outputs" in result:
                record["outputs"] = result["outputs"]

            results.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            acc = correct_count / (i + 1)
            mark = "o" if is_correct else "x"
            print(f"  [{name}] task {i+1:3d}/100  {mark}  acc={acc:.1%}  ({elapsed:.1f}s)")

    total_time = time.time() - t_start
    print(f"  [{name}] Done in {total_time:.0f}s ({total_time/60:.1f}min)")
    return results


def print_comparison(h1_stats: dict, sc_stats: dict):
    print()
    print("=" * 80)
    print("  仮説1 vs Self-Consistency 比較結果")
    print("=" * 80)
    print()
    print(f"{'手法':<35} | {'Overall':>8} | {'CONSISTENT':>11} | {'CONTRADICTION':>14} | {'LLM呼出/タスク':>14}")
    print("-" * 95)
    print(f"{'NCA v5 1位（参考・既存結果）':<27} | {'61.0%':>8} | {'40.0%':>11} | {'82.0%':>14} | {'12回':>11}")
    print(f"{'仮説1（信頼度重み付き・5step）':<25} | {h1_stats['overall']:>7.1%} | {h1_stats['consistent_acc']:>10.1%} | {h1_stats['contradiction_acc']:>13.1%} | {'18回':>11}")
    print(f"{'Self-Consistency（多数決のみ）':<25} | {sc_stats['overall']:>7.1%} | {sc_stats['consistent_acc']:>10.1%} | {sc_stats['contradiction_acc']:>13.1%} | {'3回':>12}")
    print()

    # Groupthink comparison
    print(f"{'グループシンク':<35} | {'All-CONTR':>9} | {'All-CONS':>9} | {'Split':>6}")
    print("-" * 70)
    print(f"{'NCA v5 1位（参考）':<30} | {'57':>9} | {'15':>9} | {'28':>6}")
    print(f"{'仮説1':<35} | {h1_stats['groupthink_all_contradiction']:>9} | {h1_stats['groupthink_all_consistent']:>9} | {h1_stats['split']:>6}")
    print(f"{'Self-Consistency':<35} | {sc_stats['groupthink_all_contradiction']:>9} | {sc_stats['groupthink_all_consistent']:>9} | {sc_stats['split']:>6}")
    print()

    # Judgment
    print("=" * 80)
    print("  判定")
    print("=" * 80)

    if h1_stats["overall"] > 0.65:
        print("  → 仮説1 confirmed: NCAの繰り返し更新 + 信頼度重み付きで65%超え達成!")
    else:
        print(f"  → 仮説1 not confirmed: {h1_stats['overall']:.1%} < 65%. 仮説2へ進む")

    if h1_stats["overall"] > sc_stats["overall"]:
        delta = h1_stats["overall"] - sc_stats["overall"]
        print(f"  → NCAの議論プロセスに意味あり（+{delta:.1%} vs Self-Consistency）")
    elif h1_stats["overall"] == sc_stats["overall"]:
        print("  → NCAとSelf-Consistencyが同等 — 議論プロセスの効果は不明")
    else:
        delta = sc_stats["overall"] - h1_stats["overall"]
        print(f"  → 多数決で十分、議論プロセスの価値は薄い（Self-Consistencyが+{delta:.1%}上回る）")

    # v5 3-step vs h1 5-step
    print()
    v5_overall = 0.61
    if h1_stats["overall"] > v5_overall:
        print(f"  → 5ステップ化で精度向上: {v5_overall:.1%} → {h1_stats['overall']:.1%} (+{h1_stats['overall'] - v5_overall:.1%})")
    elif h1_stats["overall"] == v5_overall:
        print(f"  → 5ステップ化の効果なし: v5 3-step ({v5_overall:.1%}) = h1 5-step ({h1_stats['overall']:.1%})")
    else:
        print(f"  -> 5step de seido teika: {v5_overall:.1%} -> {h1_stats['overall']:.1%} ({h1_stats['overall'] - v5_overall:+.1%}) -- step zouka wa gyakukouka")

    print("=" * 80)


def main():
    tasks = generate_tasks()
    print(f"Tasks: {len(tasks)}")

    # 1. Run hypothesis 1 (NCA with confidence-weighted voting, 5 steps)
    print(f"\n{'='*60}")
    print("  Phase 1: Hypothesis 1 (NCA + confidence-weighted voting)")
    print(f"{'='*60}")
    h1_results = run_experiment("H1", run_nca_h1, tasks, H1_PATH)
    h1_stats = compute_stats(h1_results)

    # 2. Run self-consistency baseline
    print(f"\n{'='*60}")
    print("  Phase 2: Self-Consistency (independent majority vote)")
    print(f"{'='*60}")
    sc_results = run_experiment("SC", run_self_consistency, tasks, SC_PATH)
    sc_stats = compute_stats(sc_results)

    # 3. Print comparison
    print_comparison(h1_stats, sc_stats)


if __name__ == "__main__":
    main()
