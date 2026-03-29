import sys
sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")
from task_generator import generate_tasks
import json
from pathlib import Path

tasks = generate_tasks()
output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

# JSON形式で保存
with open(output_dir / "world_consistency_tasks.json", "w", encoding="utf-8") as f:
    json.dump([{
        "task_id": t.task_id,
        "question": t.question,
        "label": t.label,          # True=CONSISTENT / False=CONTRADICTION
        "world_rule": t.world_rule,
    } for t in tasks], f, ensure_ascii=False, indent=2)

# JSONL形式でも保存（実験スクリプトとの互換性）
with open(output_dir / "world_consistency_tasks.jsonl", "w", encoding="utf-8") as f:
    for t in tasks:
        f.write(json.dumps({
            "task_id": t.task_id,
            "question": t.question,
            "label": t.label,
            "world_rule": t.world_rule,
        }, ensure_ascii=False) + "\n")

print(f"Exported {len(tasks)} tasks")
consistent = sum(1 for t in tasks if t.label)
print(f"  CONSISTENT: {consistent}")
print(f"  CONTRADICTION: {len(tasks) - consistent}")
