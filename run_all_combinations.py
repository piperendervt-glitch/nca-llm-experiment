"""
run_all_combinations.py

Run all C(8,3)=56 heterogeneous 3-node NCA v5 combinations.
"""

import json
import sys
import time
from itertools import combinations
from pathlib import Path

sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")
sys.path.insert(0, str(Path(__file__).parent))

from task_generator import generate_tasks
from nca_network_v5 import run_nca_network_v5

MODELS = [
    "qwen2.5:3b",
    "qwen2.5:7b",
    "llama3:latest",
    "llama3.1:8b",
    "llama3.2:3b",
    "mistral:7b",
    "gemma2:2b",
    "fool-qwen:latest",
]

RESULTS_DIR = Path("results/v5")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = RESULTS_DIR / "summary.jsonl"


def safe_name(model: str) -> str:
    return model.replace(":", "_").replace(".", "_")


def combo_filename(combo: tuple[str, str, str]) -> Path:
    return RESULTS_DIR / f"combo_{'__'.join(safe_name(m) for m in combo)}.jsonl"


def nca_verdict_to_bool(verdict: str) -> bool | None:
    if verdict == "CONSISTENT":
        return True
    elif verdict == "CONTRADICTION":
        return False
    return None


def run_one_combination(combo: tuple[str, str, str], tasks: list, combo_idx: int, total_combos: int) -> dict:
    model_a, model_b, model_c = combo
    out_path = combo_filename(combo)

    # Resume support
    existing = []
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
        if len(existing) >= len(tasks):
            print(f"  [SKIP] Already complete ({len(existing)} results)")
            return compute_stats(existing)

    start_idx = len(existing)
    results = list(existing)
    correct_count = sum(1 for r in results if r["is_correct"])

    mode = "a" if start_idx > 0 else "w"
    if start_idx > 0:
        print(f"  Resuming from task {start_idx + 1}")

    with open(out_path, mode, encoding="utf-8") as f:
        for i, task in enumerate(tasks):
            if i < start_idx:
                continue

            task_input = f"World rule: {task.world_rule}\nStatement: {task.question}"

            t0 = time.time()
            try:
                nca_result = run_nca_network_v5(task_input, model_a, model_b, model_c)
                verdict = nca_result["final_verdict"]
                prediction = nca_verdict_to_bool(verdict)
                steps = nca_result.get("steps", [])
            except Exception as e:
                prediction = None
                verdict = f"ERROR: {e}"
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
                "elapsed_sec": round(elapsed, 2),
                "steps": steps,
            }
            results.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            acc = correct_count / (i + 1)
            mark = "o" if is_correct else "x"
            if (i + 1) % 25 == 0 or i == 0:
                print(f"    task {i+1:3d}/100  {mark}  acc={acc:.1%}")

    return compute_stats(results)


def compute_stats(results: list) -> dict:
    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])

    cons = [r for r in results if r["label"] is True]
    contr = [r for r in results if r["label"] is False]
    cons_correct = sum(1 for r in cons if r["is_correct"])
    contr_correct = sum(1 for r in contr if r["is_correct"])

    # Groupthink stats
    all_contradiction = 0
    all_consistent = 0
    split = 0
    for r in results:
        steps = r.get("steps", [])
        if not steps:
            continue
        final_outputs = steps[-1].get("outputs", [])
        if not final_outputs:
            continue
        verdicts = []
        for out in final_outputs:
            d = out.get("decision", "UNKNOWN") if isinstance(out, dict) else "UNKNOWN"
            verdicts.append(d)
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


def load_completed_combos() -> set:
    """Load already-completed combos from summary.jsonl."""
    done = set()
    if SUMMARY_PATH.exists():
        with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    done.add(tuple(entry["combo"]))
    return done


def print_leaderboard():
    """Print final leaderboard from summary.jsonl."""
    if not SUMMARY_PATH.exists():
        print("No summary file found.")
        return

    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]

    entries.sort(key=lambda e: e["overall"], reverse=True)

    print(f"\n{'='*90}")
    print("  TOP 10 COMBINATIONS BY OVERALL ACCURACY")
    print(f"{'='*90}")
    print(f"{'Rank':<5} {'Combination':<45} {'Overall':>8} {'Cons':>7} {'Contr':>7} {'Split':>6} {'GT-Con':>7} {'GT-Ctr':>7}")
    print("-" * 90)
    for i, e in enumerate(entries[:10]):
        combo_str = " + ".join(e["combo"])
        print(f" {i+1:<4} {combo_str:<45} {e['overall']:>7.1%} {e['consistent_acc']:>6.1%} {e['contradiction_acc']:>6.1%} {e['split']:>5} {e['groupthink_all_consistent']:>6} {e['groupthink_all_contradiction']:>6}")

    print(f"\n{'='*90}")
    print("  WORST 3 COMBINATIONS")
    print(f"{'='*90}")
    for i, e in enumerate(entries[-3:]):
        combo_str = " + ".join(e["combo"])
        rank = len(entries) - 2 + i
        print(f" {rank:<4} {combo_str:<45} {e['overall']:>7.1%} {e['consistent_acc']:>6.1%} {e['contradiction_acc']:>6.1%}")

    # Most split decisions
    by_split = sorted(entries, key=lambda e: e["split"], reverse=True)
    print(f"\n{'='*90}")
    print("  MOST SPLIT DECISIONS (top 5)")
    print(f"{'='*90}")
    for e in by_split[:5]:
        combo_str = " + ".join(e["combo"])
        print(f"  {combo_str:<45} split={e['split']:>3}  overall={e['overall']:.1%}")

    # Least groupthink (= most split + least unanimous)
    by_least_gt = sorted(entries, key=lambda e: e["groupthink_all_contradiction"] + e["groupthink_all_consistent"])
    print(f"\n{'='*90}")
    print("  LEAST GROUPTHINK (top 5)")
    print(f"{'='*90}")
    for e in by_least_gt[:5]:
        combo_str = " + ".join(e["combo"])
        gt = e["groupthink_all_contradiction"] + e["groupthink_all_consistent"]
        print(f"  {combo_str:<45} groupthink={gt:>3}  split={e['split']:>3}  overall={e['overall']:.1%}")


def main():
    all_combos = list(combinations(MODELS, 3))
    print(f"Total combinations: {len(all_combos)}")

    tasks = generate_tasks()
    print(f"Tasks: {len(tasks)}")

    done = load_completed_combos()
    print(f"Already completed: {len(done)}")

    total_start = time.time()

    for idx, combo in enumerate(all_combos):
        model_a, model_b, model_c = combo
        print(f"\n[{idx+1:02d}/{len(all_combos)}] {model_a} + {model_b} + {model_c}")

        if combo in done:
            print("  [SKIP] Already in summary")
            continue

        stats = run_one_combination(combo, tasks, idx, len(all_combos))

        # Append to summary
        summary_entry = {
            "combo": list(combo),
            **stats,
        }
        with open(SUMMARY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(summary_entry, ensure_ascii=False) + "\n")

        print(f"  => Overall: {stats['overall']:.1%}  Cons: {stats['consistent_acc']:.1%}  Contr: {stats['contradiction_acc']:.1%}  Split: {stats['split']}")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"All {len(all_combos)} combinations complete in {total_elapsed:.0f}s ({total_elapsed/3600:.1f}h)")
    print(f"{'='*60}")

    print_leaderboard()


if __name__ == "__main__":
    main()
