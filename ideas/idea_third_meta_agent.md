# アイデアメモ: AAS v2における第3 MetaAgent設計案

作成日: 2026-03-29
提唱者: Robosheep（pipe_render）+ Grok協議

---

## 概要

AAS v2（過去ログ参照型AAS）に「第3 MetaAgent（中立審判）」を追加する設計案。
Unit-A（CONTRADICTION寄り）とUnit-B（CONSISTENT寄り）の対立を
軽量モデルが1回だけ仲裁する構造。

---

## 全体構成

```
Unit-A（CONTRADICTION寄りモデル群）
  → verdict_A + conf_A + reasoning_A
  
Unit-B（CONSISTENT寄りモデル群）
  → verdict_B + conf_B + reasoning_B

↓ 不一致の場合のみ

第3 MetaAgent（中立審判・軽量モデル）
  → 最終verdict
  → 判断理由をログに記録
```

---

## モデル選択

### 推奨モデル（修正済み）

| 役割 | 推奨モデル | 理由 |
|------|-----------|------|
| Unit-A | qwen2.5:7b + gemma2:2b | CONTRADICTION寄りバイアス |
| Unit-B | mistral:7b + llama3:latest | CONSISTENT寄りバイアス |
| 第3 MetaAgent | llama3.2:3b または mistral:7b | バランス型・中立に近い |

### gemma2:2bを審判に使わない理由

v5実験のper-model分析より：
- gemma2:2b: CONTRADICTION 98/100（極端なバイアス）
- 「審判が最も偏っているモデル」という逆説が起きる
- llama3.2:3b（avg 29.5% CONSISTENT）の方が中立に近い

---

## 改善版プロンプト

```
あなたは中立的な審判です。
自分の過去の傾向を一切無視してください。

【タスク】
{task_input}

【共通ルール】
両ユニットは同一の過去ログ参照＋
convex combinationルールに従っています。

Unit-A: {verdict_A}（確信度: {conf_A}）
理由: {reasoning_A}

Unit-B: {verdict_B}（確信度: {conf_B}）
理由: {reasoning_B}

【判断基準（優先順位順）】
1. 論理的に正確な方を選ぶ
2. 確信度が高い方を優先する
3. 両者の確信度が共にLOWの場合のみ
   ABSTAIN と回答する

回答形式:
選択: [A / B / ABSTAIN]
理由: [1文で]
最終verdict: [CONSISTENT / CONTRADICTION / ABSTAIN]
```

### temperature設定

```
temperature = 0.1〜0.2 推奨
（0.0は同じ入力に常に同じ答えを返し
  実質的にどちらかのUnitを無視することになる）
```

---

## 実装上の安全策

### ①一致時はスキップ（最重要）

```python
if verdict_A == verdict_B:
    # 一致した場合は第3MetaAgentをスキップ
    final_verdict = verdict_A
    meta_agent_called = False
else:
    # 不一致の場合のみ呼び出す
    final_verdict = call_third_meta_agent()
    meta_agent_called = True
```

効果：
- 第3MetaAgentの呼び出し回数を大幅削減
- バイアス注入リスクを最小化
- コスト節約

### ②ABSTAINの明確な定義

```
選択肢C（旧）: 「両者の相違点を明示して人間に提示する」
→ 判断放棄・自動化が崩れる

選択肢C（新）: ABSTAIN
→ 両者の確信度が共にLOWの場合のみ
→ ランダムで決定（または多数決から除外）
→ ログにABSTAINとして記録
```

### ③履歴からの除外

```python
# 第3MetaAgentの判断は過去ログに記録しない
# Unit-AとUnit-Bの判断のみをログに残す
# → 第3MetaAgentが自分の過去判断に引きずられない
# → 自己強化型バイアスの循環を防ぐ
```

### ④（オプション）多数決版

```python
# コストが許せば3回呼び出して多数決
verdicts = [call_meta_agent() for _ in range(3)]
final = majority_vote(verdicts)
```

---

## 期待される効果

| 項目 | 評価 |
|------|------|
| バイアス抑制効果 | ★★★☆☆（中程度） |
| 解釈性の向上 | ★★★★★（非常に高い） |
| 実装コスト | ★★★★☆（低い） |
| 制御不能リスクの低減 | ★★★☆☆（中程度） |

### 最大の貢献：解釈性

```
「第3MetaAgentがUnit-Aを選んだ理由」が
ログに残る
→ AAS元論文の最大の弱点
  （なぜその重みになったか不明）を
  構造的に解決できる
```

---

## falsifier_reviewへの対応

反証チャットで指摘された「アンチテーゼAIの有害ノイズ問題」：

```
問題: 正解が一つに定まる問題では
      「必ず反対する」ルールが有害ノイズを生む

解決: 第3MetaAgentは「必ず反対する」のではなく
     「Unit-AとUnit-Bの論理を比較して正しい方を選ぶ」
     → 有害ノイズを生まない構造的な解決
```

---

## AAS v2完成度への貢献

この設計を組み込むことで：
- 現状比 +30% 程度の完成度向上が見込める
- 特に「解釈性」と「バイアス循環の防止」に効果的

---

## 関連アイデア

- 過去ログ参照型AAS → `ideas/idea_aas_v2_past_log_reference.md`
- ハートの女王化 → `ideas/idea_queen_of_hearts_effect.md`
- 反対案専用エージェント → `ideas/idea_antithesis_agent.md`

---

## ステータス

- [x] 設計案の策定
- [x] Grokとの協議・改善
- [x] 複数媒体に保存
- [ ] v11完了後にaas-v2で実装
