"""
run_v6_sampling.py

Run NCA v6 random sampling experiment.
Randomly samples model combos, agreement intensity, and step count.
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")
sys.path.insert(0, str(Path(__file__).parent))

from task_generator import generate_tasks
from nca_network_v6 import run_nca_v6

MODEL_POOL = [
    "qwen2.5:3b",
    "qwen2.5:7b",
    "llama3:latest",
    "llama3.1:8b",
    "llama3.2:3b",
    "mistral:7b",
]

RESULTS_DIR = Path("results/v6")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = RESULTS_DIR / "v6_summary.jsonl"


def sample_params(rng: random.Random) -> dict:
    models = rng.sample(MODEL_POOL, 3)
    agreement_pct = [rng.choice(range(0, 101, 10)) for _ in range(3)]
    num_steps = rng.randint(1, 5)
    return {
        "models": models,
        "agreement_pct": agreement_pct,
        "num_steps": num_steps,
    }


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

    all_contradiction = sum(1 for r in results if r.get("groupthink") == "all_contradiction")
    all_consistent = sum(1 for r in results if r.get("groupthink") == "all_consistent")
    split = sum(1 for r in results if r.get("groupthink") == "split")

    return {
        "overall": round(correct / total, 2) if total else 0,
        "consistent_acc": round(cons_correct / len(cons), 2) if cons else 0,
        "contradiction_acc": round(contr_correct / len(contr), 2) if contr else 0,
        "groupthink_all_contradiction": all_contradiction,
        "groupthink_all_consistent": all_consistent,
        "split": split,
    }


def run_one_trial(trial_num: int, params: dict, tasks: list) -> dict:
    models = params["models"]
    agreement_pct = params["agreement_pct"]
    num_steps = params["num_steps"]

    out_path = RESULTS_DIR / f"sample_{trial_num:04d}.jsonl"

    # Resume support for partial trial
    existing = []
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
        if len(existing) >= len(tasks):
            return compute_stats(existing)

    start_idx = len(existing)
    results = list(existing)
    correct_count = sum(1 for r in results if r["is_correct"])

    mode = "a" if start_idx > 0 else "w"

    with open(out_path, mode, encoding="utf-8") as f:
        for i, task in enumerate(tasks):
            if i < start_idx:
                continue

            task_input = f"World rule: {task.world_rule}\nStatement: {task.question}"

            t0 = time.time()
            try:
                nca_result = run_nca_v6(
                    task_input,
                    models[0], models[1], models[2],
                    agreement_pct,
                    num_steps,
                )
                verdict = nca_result["final_verdict"]
                prediction = verdict_to_bool(verdict)
                groupthink = nca_result["groupthink"]
                steps = nca_result.get("steps", [])
            except Exception as e:
                prediction = None
                verdict = f"ERROR: {e}"
                groupthink = "unknown"
                steps = []

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
                "groupthink": groupthink,
                "elapsed_sec": round(elapsed, 2),
                "steps": steps,
            }
            results.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

    return compute_stats(results)


def load_completed_trials() -> int:
    if not SUMMARY_PATH.exists():
        return 0
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def print_leaderboard(total_trials: int):
    if not SUMMARY_PATH.exists():
        return

    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]

    entries.sort(key=lambda e: -e["overall"])

    print(f"\n{'='*100}")
    print(f"  NCA v6 Random Sampling Results ({len(entries)} trials)")
    print(f"{'='*100}")

    # Top 10
    print(f"\nTOP 10 by Overall Accuracy:")
    print(f"{'Trial':>6} | {'Models':<40} | {'Agreement':<16} | {'Steps':>5} | {'Overall':>8} | {'Cons':>6} | {'Contr':>6} | {'Split':>5}")
    print("-" * 100)
    for e in entries[:10]:
        combo = "+".join(e["models"])
        agree = str(e["agreement_pct"])
        print(f"  {e['trial']:04d} | {combo:<40} | {agree:<16} | {e['num_steps']:>5} | {e['overall']:>7.0%} | {e['consistent_acc']:>5.0%} | {e['contradiction_acc']:>5.0%} | {e['split']:>5}")

    # Steps analysis
    print(f"\nAccuracy by step count:")
    from collections import defaultdict
    by_steps = defaultdict(list)
    for e in entries:
        by_steps[e["num_steps"]].append(e["overall"])
    for s in sorted(by_steps.keys()):
        vals = by_steps[s]
        avg = sum(vals) / len(vals)
        print(f"  Steps={s}: {avg:.1%} (n={len(vals)})")

    # Agreement band analysis
    print(f"\nAccuracy by average agreement intensity:")
    bands = {"0-30%": [], "40-60%": [], "70-100%": []}
    for e in entries:
        avg_agree = sum(e["agreement_pct"]) / 3
        if avg_agree <= 30:
            bands["0-30%"].append(e["overall"])
        elif avg_agree <= 60:
            bands["40-60%"].append(e["overall"])
        else:
            bands["70-100%"].append(e["overall"])
    for band, vals in bands.items():
        if vals:
            avg = sum(vals) / len(vals)
            print(f"  {band:>8}: {avg:.1%} (n={len(vals)})")
        else:
            print(f"  {band:>8}: no data")

    # vs v5 best
    best = entries[0]
    print(f"\nComparison with v5 best:")
    print(f"  v5 best:  61.0%")
    print(f"  v6 best:  {best['overall']:.0%} ({best['overall'] - 0.61:+.0%}pp)")
    print(f"  v6 best config: {'+'.join(best['models'])} agree={best['agreement_pct']} steps={best['num_steps']}")
    print(f"{'='*100}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    tasks = generate_tasks()
    print(f"Tasks: {len(tasks)}")
    print(f"Target trials: {args.trials}")

    rng = random.Random(args.seed)

    # Pre-generate all trial params (deterministic with seed)
    all_params = [sample_params(rng) for _ in range(args.trials)]

    done = load_completed_trials()
    print(f"Already completed: {done}")

    total_start = time.time()

    for trial_idx in range(args.trials):
        trial_num = trial_idx + 1
        params = all_params[trial_idx]

        combo_str = "+".join(params["models"])
        agree_str = str(params["agreement_pct"])

        if trial_idx < done:
            continue

        print(f"\n[{trial_num:03d}/{args.trials}] models={combo_str} agree={agree_str} steps={params['num_steps']}")

        t0 = time.time()
        stats = run_one_trial(trial_num, params, tasks)
        elapsed = time.time() - t0

        summary_entry = {
            "trial": trial_num,
            "models": params["models"],
            "agreement_pct": params["agreement_pct"],
            "num_steps": params["num_steps"],
            **stats,
            "elapsed_sec": round(elapsed, 1),
        }
        with open(SUMMARY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(summary_entry, ensure_ascii=False) + "\n")

        print(f"  => Overall: {stats['overall']:.0%}  Cons: {stats['consistent_acc']:.0%}  Contr: {stats['contradiction_acc']:.0%}  Split: {stats['split']}  ({elapsed:.0f}s)")

    total_elapsed = time.time() - total_start
    print(f"\nAll {args.trials} trials complete in {total_elapsed:.0f}s ({total_elapsed/3600:.1f}h)")

    print_leaderboard(args.trials)


if __name__ == "__main__":
    main()
