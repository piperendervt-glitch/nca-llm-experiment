# verify_results.py 仕様書

作成日: 2026-04-04
目的: 実験結果の数値を生データから自動検証する
     「レポートの数字を信じる」問題の再発防止

---

## 概要

実験完了直後に自動実行するスクリプト。
生データ（.jsonl）から直接計算して
レポートの数字と照合する。
不一致があればエラーで停止・修正を促す。

---

## 実行方法

```bash
# 単一実験の検証
python verify_results.py --version v9d

# 複数実験の一括検証
python verify_results.py --version v9a v9b v9c v9d

# v11の全Systemを検証
python verify_results.py --version v11 --systems a b c d1b d1c
```

---

## 検証項目（全実験共通）

### Check 1: 重複データ検出

```python
# 各task_idの出現回数を確認
# 重複があれば警告・first occurrenceで分析を続行
duplicate_ids = [id for id, count in Counter(task_ids).items() if count > 1]
if duplicate_ids:
    print(f"WARNING: {len(duplicate_ids)} duplicate task_ids found")
    print(f"Using first occurrence for all analyses")
```

### Check 2: タスク数の確認

```python
# 期待されるタスク数と実際のタスク数を照合
expected = {
    'world_consistency': 100,
    'math_elementary': 100,
    'math_middle': 75,
    'math_high': 75,
    'total': 350
}
```

### Check 3: 精度の直接計算

```python
# 生データから直接計算
overall_accuracy = sum(r['is_correct'] for r in records) / len(records)

# per task_set
for task_set in task_sets:
    subset = [r for r in records if r['task_set'] == task_set]
    accuracy = sum(r['is_correct'] for r in subset) / len(subset)
```

### Check 4: unanimous vs split の直接計算

```python
# vote_distributionフィールドから判定
def is_unanimous(vote_dist):
    return max(vote_dist.values()) == 3  # 全員一致

unanimous = [r for r in records if is_unanimous(r['vote_distribution'])]
split = [r for r in records if not is_unanimous(r['vote_distribution'])]

acc_unanimous = sum(r['is_correct'] for r in unanimous) / len(unanimous)
acc_split = sum(r['is_correct'] for r in split) / len(split)
```

### Check 5: CFRの直接計算

```python
# CFR = wrong_unanimous / total_unanimous（per task_set）
for task_set in task_sets:
    subset_unanimous = [r for r in unanimous if r['task_set'] == task_set]
    wrong_unanimous = sum(1 for r in subset_unanimous if not r['is_correct'])
    cfr = wrong_unanimous / len(subset_unanimous) if subset_unanimous else None

    # Clopper-Pearson 95% CI
    from scipy.stats import beta
    lo = beta.ppf(0.025, wrong_unanimous, len(subset_unanimous) - wrong_unanimous + 1)
    hi = beta.ppf(0.975, wrong_unanimous + 1, len(subset_unanimous) - wrong_unanimous)
```

### Check 6: レポートとの照合（オプション）

```python
# reports/{version}_report.md から数字を抽出して照合
# 不一致があれば警告
report_accuracy = extract_from_report(version, 'overall_accuracy')
if abs(calculated_accuracy - report_accuracy) > 0.005:  # 0.5pp以上の差
    print(f"DISCREPANCY: calculated={calculated_accuracy:.3f}, report={report_accuracy:.3f}")
```

---

## 出力フォーマット

```
================================================================
Verification Report: v9d
================================================================
[CHECK 1] Duplicate task_ids
  math_high: 93 duplicates found → using first occurrence
  Others: no duplicates

[CHECK 2] Task counts (after dedup)
  world_consistency: 100 ✓
  math_elementary:   100 ✓
  math_middle:        75 ✓
  math_high:          75 ✓ (was 168 rows → 75 unique)
  Total:             350 ✓

[CHECK 3] Overall accuracy
  Calculated: 76.0%
  Report:     76.0% ✓

[CHECK 4] Unanimous vs Split
  Unanimous: n=237, accuracy=82.3%
  Split:     n=113, accuracy=62.8%

[CHECK 5] CFR per task_set
  world_consistency: 4/35  = 11.4% [3.1%, 26.3%]
  math_elementary:   9/83  = 10.8% [5.0%, 19.7%]
  math_middle:      17/62  = 27.4% [16.6%, 40.2%]
  math_high:        12/57  = 21.1% [11.4%, 33.9%]

[CHECK 6] Report comparison
  Overall accuracy: ✓ (match within 0.5pp)
  WARNING: CFR values in report differ from calculated
    Report says: LPA values (not CFR)
    This is a definition mismatch → manual review required

================================================================
RESULT: 1 WARNING, 0 ERRORS
All analyses should use calculated values, not report values.
================================================================
```

---

## エラーの種類

```
ERROR（実験をやり直すべき）:
  - task_idが全て重複（実験が失敗）
  - タスク数が期待値と大幅に異なる（>10%）
  - is_correctフィールドが存在しない

WARNING（手動確認が必要）:
  - 重複task_idが存在する（first occurrenceで続行）
  - レポートの数字と0.5pp以上の差
  - CFRの定義がレポートと異なる可能性

INFO（正常）:
  - 全チェック通過
  - 軽微な四捨五入の差（<0.5pp）
```

---

## v11への適用

```
v11完了後に以下を実行:

python verify_results.py --version v11 --systems a b c d1b d1c

検証項目（v11追加分）:
  - System別の精度
  - System AとのΔpp
  - 統計的有意差（z検定）
  - タスクタイプ別の精度
    （D-1bはmath系のみ・D-1cはlogic/eq系のみ）
```

---

## 実装スケジュール

```
v11実験完了後:
  1. verify_results.py を実装
  2. 過去の全実験（v9a〜v10）に遡って検証
  3. 不一致が見つかれば論文の数字を修正

以降の全実験:
  実験完了 → verify_results.py 実行 → 問題なければコミット
  という手順を標準化
```
