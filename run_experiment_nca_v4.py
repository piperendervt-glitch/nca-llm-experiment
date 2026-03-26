"""
run_experiment_nca_v4.py

NCA v4（Confidence-Weighted Neighbor Influence）実験。
Fixed, v1, v2, v3 は既存結果を流用し、NCA v4 のみ新規実行する。
"""

import json
import sys
import time
from pathlib import Path

# sdnd-proof の src を参照
SDND_SRC = Path("D:/Users/pipe_render/sdnd-proof/src")
sys.path.insert(0, str(SDND_SRC))
sys.path.insert(0, str(Path(__file__).parent))

from task_generator import generate_tasks
from nca_network_v4 import run_nca_network

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

FIXED_RESULTS_PATH   = RESULTS_DIR / "fixed_results.jsonl"
NCA_V1_RESULTS_PATH  = RESULTS_DIR / "nca_results.jsonl"
NCA_V2_RESULTS_PATH  = RESULTS_DIR / "nca_v2_results.jsonl"
NCA_V3_RESULTS_PATH  = RESULTS_DIR / "nca_v3_results.jsonl"
NCA_V4_RESULTS_PATH  = RESULTS_DIR / "nca_v4_results.jsonl"


def nca_verdict_to_bool(verdict: str) -> bool | None:
    if verdict == "CONSISTENT":
        return True
    elif verdict == "CONTRADICTION":
        return False
    return None


def load_jsonl(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def run_nca_v4_experiment(tasks: list) -> list:
    """実験群: NCA v4 で全タスクを実行。"""
    results = []
    correct_count = 0

    # Resume support: check existing results
    existing_count = 0
    if NCA_V4_RESULTS_PATH.exists():
        with open(NCA_V4_RESULTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                results.append(json.loads(line))
                existing_count += 1
        correct_count = sum(1 for r in results if r["is_correct"])
        print(f"  Resuming from task {existing_count + 1} (found {existing_count} existing results)")

    print("\n" + "=" * 60)
    print("実験群 (NCA v4 Network) 実行開始")
    print("=" * 60)

    mode = "a" if existing_count > 0 else "w"
    with open(NCA_V4_RESULTS_PATH, mode, encoding="utf-8") as f:
        for i, task in enumerate(tasks):
            if i < existing_count:
                continue

            task_input = f"World rule: {task.world_rule}\nStatement: {task.question}"

            t0 = time.time()
            try:
                nca_result = run_nca_network(task_input)
                verdict = nca_result["final_verdict"]
                prediction = nca_verdict_to_bool(verdict)
                raw_output = verdict
                num_steps = nca_result["num_steps"]
                steps = nca_result.get("steps", [])
            except Exception as e:
                prediction = None
                raw_output = f"ERROR: {e}"
                num_steps = 0
                steps = []

            elapsed = time.time() - t0
            is_correct = (prediction == task.label) if prediction is not None else False
            if is_correct:
                correct_count += 1
            cumulative_accuracy = correct_count / (i + 1)

            record = {
                "task_id": task.task_id,
                "question": task.question,
                "world_rule": task.world_rule,
                "label": task.label,
                "prediction": prediction,
                "is_correct": is_correct,
                "raw_output": raw_output,
                "num_steps": num_steps,
                "elapsed_sec": round(elapsed, 2),
                "cumulative_accuracy": round(cumulative_accuracy, 4),
                "steps": steps,
            }
            results.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            mark = "o" if is_correct else "x"
            print(f"  [{i+1:03d}/{len(tasks):03d}] {mark} | acc={cumulative_accuracy:.1%} | {elapsed:.1f}s | {task.question[:40]}")

            if (i + 1) % 10 == 0:
                recent = results[-10:]
                recent_acc = sum(1 for r in recent if r["is_correct"]) / len(recent)
                print(f"  --- 直近10件正解率: {recent_acc:.0%} ---")

    return results


def print_summary(results_fixed, results_v4):
    """5way比較サマリーを表示する。"""
    results_v1 = load_jsonl(NCA_V1_RESULTS_PATH)
    results_v2 = load_jsonl(NCA_V2_RESULTS_PATH)
    results_v3 = load_jsonl(NCA_V3_RESULTS_PATH)

    total = len(results_fixed)
    acc_fixed = sum(1 for r in results_fixed if r["is_correct"]) / total
    acc_v1 = sum(1 for r in results_v1 if r["is_correct"]) / total
    acc_v2 = sum(1 for r in results_v2 if r["is_correct"]) / total
    acc_v3 = sum(1 for r in results_v3 if r["is_correct"]) / total
    acc_v4 = sum(1 for r in results_v4 if r["is_correct"]) / total

    print(f"\n{'=' * 60}")
    print("5way比較サマリー")
    print(f"{'=' * 60}")
    print(f"  Fixed Network:  {acc_fixed:.1%}")
    print(f"  NCA v1:         {acc_v1:.1%}  (vs Fixed: {acc_v1-acc_fixed:+.1%})")
    print(f"  NCA v2:         {acc_v2:.1%}  (vs Fixed: {acc_v2-acc_fixed:+.1%})")
    print(f"  NCA v3:         {acc_v3:.1%}  (vs Fixed: {acc_v3-acc_fixed:+.1%})")
    print(f"  NCA v4:         {acc_v4:.1%}  (vs Fixed: {acc_v4-acc_fixed:+.1%})")

    # CONSISTENT / CONTRADICTION breakdown
    for label_name, label_val in [("CONSISTENT", True), ("CONTRADICTION", False)]:
        f_sub = [r for r in results_fixed if r["label"] == label_val]
        v1_sub = [r for r in results_v1 if r["label"] == label_val]
        v2_sub = [r for r in results_v2 if r["label"] == label_val]
        v3_sub = [r for r in results_v3 if r["label"] == label_val]
        v4_sub = [r for r in results_v4 if r["label"] == label_val]

        acc_f = sum(1 for r in f_sub if r["is_correct"]) / len(f_sub) if f_sub else 0
        acc_1 = sum(1 for r in v1_sub if r["is_correct"]) / len(v1_sub) if v1_sub else 0
        acc_2 = sum(1 for r in v2_sub if r["is_correct"]) / len(v2_sub) if v2_sub else 0
        acc_3 = sum(1 for r in v3_sub if r["is_correct"]) / len(v3_sub) if v3_sub else 0
        acc_4 = sum(1 for r in v4_sub if r["is_correct"]) / len(v4_sub) if v4_sub else 0

        print(f"\n{label_name}タスクのみの正解率:")
        print(f"  Fixed: {acc_f:.1%} | v1: {acc_1:.1%} | v2: {acc_2:.1%} | v3: {acc_3:.1%} | v4: {acc_4:.1%}")

    # Groupthink stats for v3 and v4
    for version_name, version_results in [("v3", results_v3), ("v4", results_v4)]:
        all_contradiction = 0
        all_consistent = 0
        split = 0
        for r in version_results:
            steps = r.get("steps", [])
            if not steps:
                continue
            final_outputs = steps[-1].get("outputs", [])
            if not final_outputs:
                continue
            verdicts = []
            for out in final_outputs:
                decision = out.get("decision", "UNKNOWN") if isinstance(out, dict) else "UNKNOWN"
                if decision == "CONTRADICTION":
                    verdicts.append("CONTRADICTION")
                elif decision == "CONSISTENT":
                    verdicts.append("CONSISTENT")
                else:
                    verdicts.append("UNKNOWN")
            if all(v == "CONTRADICTION" for v in verdicts):
                all_contradiction += 1
            elif all(v == "CONSISTENT" for v in verdicts):
                all_consistent += 1
            else:
                split += 1

        print(f"\nグループシンク検出（NCA {version_name}）:")
        print(f"  全ノードCONTRADICTION: {all_contradiction} / {total}")
        print(f"  全ノードCONSISTENT:    {all_consistent} / {total}")
        print(f"  分裂:                   {split} / {total}")


def main():
    print("タスクを生成中...")
    tasks = generate_tasks()
    print(f"生成完了: {len(tasks)}タスク")

    # Fixed は既存結果を流用
    print("\n既存のFixed結果を読み込み中...")
    results_fixed = load_jsonl(FIXED_RESULTS_PATH)
    print(f"読み込み完了: {len(results_fixed)}件")

    # NCA v4 を実行
    results_v4 = run_nca_v4_experiment(tasks)

    # 5way比較サマリー
    print_summary(results_fixed, results_v4)

    print(f"\n結果ファイル:")
    print(f"  {NCA_V4_RESULTS_PATH}")


if __name__ == "__main__":
    main()
