# アイデアメモ: 過去ログ参照型AAS改良案

作成日: 2026-03-29

---

## 概要

AASの重み更新ルールに「過去ログ参照」を組み込む改良案。
元のAASが抱えていた「制御不能問題」と「解釈性の低さ」を解決する可能性がある。

---

## 元のAASの問題点

```python
# タスクの成否だけを見てリアルタイムに更新
if success:
    weight[path] += learning_rate
else:
    weight[path] -= learning_rate
```

- 重みがゼロスタートで収束が遅い
- なぜその重みになったか追跡困難
- 特定経路が強化されすぎて制御不能になるリスク

---

## 改良案: 過去ログ参照型AAS

```python
# 過去ログから「どの経路が何のタスクで強いか」を分析
past_logs = load_jsonl("results/...")

# タスクの特性を分類して重みを初期化
if task_type == "contradiction_heavy":
    weight = best_weights_for_contradiction(past_logs)
elif task_type == "consistent_heavy":
    weight = best_weights_for_consistent(past_logs)
```

---

## 元のAASとの比較

| 項目 | 元のAAS | 過去ログ参照AAS |
|------|---------|--------------|
| 重みの初期値 | 均等（ゼロスタート） | 過去ログから最適値で開始 |
| 更新タイミング | タスクごとにリアルタイム | バッチ参照 + リアルタイム |
| 収束速度 | 遅い（ゼロから学習） | 速い（良い初期値から出発） |
| 制御不能リスク | 高い | 低い（初期値が安定） |
| 解釈性 | 低い | 高い（重みの根拠が説明可能） |

---

## さらなる発展案

### タスク難易度に応じた動的切り替え

```
簡単なタスク: 過去ログの最適重みをそのまま使う
難しいタスク: ε-greedyで探索的な重みを試す
```

### メタエージェントとの組み合わせ（v9/v10との連携）

```
MetaAgent が過去ログを分析
→ タスク特性を分類
→ 最適な初期重みを決定
→ ε-greedyでファジーさを導入
```

---

## 注意点

- 過去ログの質が重みの質を決める
- v1〜v6のログはworld_consistencyタスク専用
- 数学タスクには別のログが必要
- タスクごとに別のログを管理する設計が必要

---

## リポジトリ案

現在のNCA実験とは独立した研究として成立する。
候補名: `sdnd-proof-v2` または `aas-v2-experiment`

---

## 関連実験

- AAS元論文: https://github.com/piperendervt-glitch/sdnd-proof
- NCA実験: https://github.com/piperendervt-glitch/nca-llm-experiment
- v9（動的信頼度重み付けNCA）: メタエージェント + 過去ログ参照 + ε-greedy
- v10（動的ノード選択NCA）: 複数メタエージェント競合 + ε-greedy

---

## ステータス

- [ ] v6完了後に詳細設計を行う
- [ ] NCA実験全体が完了後に着手予定
- [ ] 別リポジトリとして独立した実験にする
