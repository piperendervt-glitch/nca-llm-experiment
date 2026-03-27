"""
run_experiment_nca.py

NCA Network（実験群）vs Fixed Network（対照群）の比較実験。
タスク・評価ロジックは sdnd-proof の task_generator を直接流用する。
"""

import json
import sys
import time
from pathlib import Path

# sdnd-proof の src を参照
SDND_SRC = Path("C:/Users/pipe_render/sdnd-proof/src")
sys.path.insert(0, str(SDND_SRC))
sys.path.insert(0, str(Path(__file__).parent))

from task_generator import generate_tasks   # sdnd-proof から流用
from fixed_network import FixedNetwork      # sdnd-proof から流用
from nca_network import run_nca_network     # 実験群

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

NCA_RESULTS_PATH    = RESULTS_DIR / "nca_results.jsonl"
FIXED_RESULTS_PATH  = RESULTS_DIR / "fixed_results.jsonl"


def nca_verdict_to_bool(verdict: str) -> bool | None:
    """
    "CONSISTENT"    -> True  (矛盾しない = label=True と一致)
    "CONTRADICTION" -> False (矛盾する   = label=False と一致)
    "UNKNOWN"       -> None  (判定不能)
    """
    if verdict == "CONSISTENT":
        return True
    elif verdict == "CONTRADICTION":
        return False
    return None


def run_fixed_experiment(tasks: list) -> list:
    """
    対照群: FixedNetwork で全タスクを実行。
    各タスクの結果を FIXED_RESULTS_PATH に逐次書き込む。
    """
    network = FixedNetwork()
    results = []
    correct_count = 0

    print("\n" + "=" * 60)
    print("対照群 (Fixed Network) 実行開始")
    print("=" * 60)

    with open(FIXED_RESULTS_PATH, "w", encoding="utf-8") as f:
        for i, task in enumerate(tasks):
            t0 = time.time()
            try:
                result = network.predict(task.world_rule, task.question)
                prediction = result["prediction"]
                raw_output = result["raw_output"]
            except Exception as e:
                prediction = None
                raw_output = f"ERROR: {e}"

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
                "elapsed_sec": round(elapsed, 2),
                "cumulative_accuracy": round(cumulative_accuracy, 4),
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


def run_nca_experiment(tasks: list) -> list:
    """
    実験群: run_nca_network で全タスクを実行。
    各タスクの結果を NCA_RESULTS_PATH に逐次書き込む。
    """
    results = []
    correct_count = 0

    print("\n" + "=" * 60)
    print("実験群 (NCA Network) 実行開始")
    print("=" * 60)

    with open(NCA_RESULTS_PATH, "w", encoding="utf-8") as f:
        for i, task in enumerate(tasks):
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


def print_summary(results_fixed: list, results_nca: list):
    """実験結果のサマリーを表示する。"""
    total = len(results_fixed)

    # 全体正解率
    fixed_acc = sum(1 for r in results_fixed if r["is_correct"]) / total
    nca_acc = sum(1 for r in results_nca if r["is_correct"]) / total
    diff = nca_acc - fixed_acc
    if diff > 0:
        diff_label = "NCA優勢"
    elif diff < 0:
        diff_label = "Fixed優勢"
    else:
        diff_label = "同率"

    # 後半50タスク
    half = total // 2
    fixed_acc_half = sum(1 for r in results_fixed[half:] if r["is_correct"]) / (total - half)
    nca_acc_half = sum(1 for r in results_nca[half:] if r["is_correct"]) / (total - half)
    diff_half = nca_acc_half - fixed_acc_half

    print("\n" + "=" * 60)
    print("実験結果サマリー")
    print("=" * 60)
    print()
    print("全体正解率:")
    print(f"  対照群 (Fixed Network): {fixed_acc:.1%}")
    print(f"  実験群 (NCA Network):   {nca_acc:.1%}")
    print(f"  差分: {diff:+.1%} ({diff_label})")
    print()
    print(f"後半{total - half}タスク ({half+1}-{total}) の正解率:")
    print(f"  対照群: {fixed_acc_half:.1%}")
    print(f"  実験群: {nca_acc_half:.1%}")
    print(f"  差分: {diff_half:+.1%}")
    print()
    print("10タスクごとの正解率:")
    print(f"  {'タスク範囲':<14} {'対照群':>8} {'実験群':>8} {'差分':>8}")
    print(f"  {'-' * 40}")
    for start in range(0, total, 10):
        end = min(start + 10, total)
        chunk_fixed = results_fixed[start:end]
        chunk_nca = results_nca[start:end]
        n = len(chunk_fixed)
        f_acc = sum(1 for r in chunk_fixed if r["is_correct"]) / n
        n_acc = sum(1 for r in chunk_nca if r["is_correct"]) / n
        d = n_acc - f_acc
        print(f"  {start+1:>4}-{end:<4}     {f_acc:>6.1%}   {n_acc:>6.1%}  {d:>+6.1%}")

    # グループシンク検出（NCAのみ）
    all_contradiction = 0
    all_consistent = 0
    split = 0
    for r in results_nca:
        steps = r.get("steps", [])
        if not steps:
            continue
        final_outputs = steps[-1].get("outputs", [])
        if not final_outputs:
            continue
        verdicts = []
        for out in final_outputs:
            upper = out.upper()
            if "CONTRADICTION" in upper:
                verdicts.append("CONTRADICTION")
            elif "CONSISTENT" in upper:
                verdicts.append("CONSISTENT")
            else:
                verdicts.append("UNKNOWN")
        if all(v == "CONTRADICTION" for v in verdicts):
            all_contradiction += 1
        elif all(v == "CONSISTENT" for v in verdicts):
            all_consistent += 1
        else:
            split += 1

    print()
    print("グループシンク検出（NCAのみ）:")
    print(f"  全ノードがCONTRADICTIONに収束したタスク数: {all_contradiction} / {total}")
    print(f"  全ノードがCONSISTENTに収束したタスク数:   {all_consistent} / {total}")
    print(f"  分裂（ノード間で意見が割れた）タスク数:    {split} / {total}")


def main():
    print("タスクを生成中...")
    tasks = generate_tasks()
    print(f"生成完了: {len(tasks)}タスク (一致:50 / 矛盾:50)")

    # 対照群を先に実行
    results_fixed = run_fixed_experiment(tasks)

    # 実験群を実行
    results_nca = run_nca_experiment(tasks)

    # サマリー表示
    print_summary(results_fixed, results_nca)

    print(f"\n結果ファイル:")
    print(f"  {FIXED_RESULTS_PATH}")
    print(f"  {NCA_RESULTS_PATH}")


if __name__ == "__main__":
    main()
