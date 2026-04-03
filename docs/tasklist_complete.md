# NCA-LLM タスクリスト（最新版）

最終更新: 2026-04-04

---

## 完了済み実験

| バージョン | 内容 | 結果 | 主な発見 |
|-----------|------|------|---------|
| v1〜v4 | world_consistency × NCA基本実験 | 45%→55% | グループシンク・ミラー効果発見 |
| v5 | 異種モデル全56通り | 61% | モデル多様性の有効性 |
| v6 | ランダムサンプリング（合意強度×ステップ数） | 63% | steps=3最適・r=0.821 |
| v7 | 小学生数学 × 役割分担NCA | 83% | 役割分担+15pp（balanced_fixed 68%比） |
| v7.5 | 中学生数学 × 役割分担NCA | 77% | 難易度の壁は中学にある |
| v7.6 | 高校生数学 × 役割分担NCA | 77% | 操作タイプが難易度を決定 |
| v8 | 適応的モデル選択（埋め込みベクトル分類） | 76.9% | unanimous 79.6% vs split 72.3% |
| v9a | MetaAgentのみ追加 | 74.9% | 61件変更・正味-1タスク・有害 |
| v9b | 動的信頼度重み付けのみ | 79.1% | 0件差異・実装確認済み（sanity check） |
| v9c | 反対案専用エージェント（weight=0.5） | 74.3% | ダミープレイヤー問題・0件変更 |
| v9d | ゲーム理論AntiNode（拒否権+Level-K） | 76.0% | 0件変更・CFR/LPA発見 |
| single-agent CFR比較 | qwen2.5:7b単独・n=350 | — | confidence無差別（Δ=0.004〜0.021） |

---

## 実行中

| バージョン | 内容 | 状況 |
|-----------|------|------|
| **v10** | **math_middle vs math_high CFR比較実験** | **🔄 実行中（推定4〜6時間）** |

### v10の目的
```
北極星の主張「math_middleが最も過信しやすい」を
統計的に検証する

必要サンプル: 各723 unanimous決定
必要タスク数: math_middle 875 / math_high 952
新規タスク生成済み: 800 / 877（seed=43）

期待される結果:
  Case A: math_middle CFR > math_high CFR（統計的確認）
         → 北極星の主張が強化される
  Case B: 差が再現されない
         → 「小サンプル観察の不安定性」として記録
```

---

## 論文執筆状況

### 確定済みセクション

| セクション | バージョン | 状態 |
|-----------|-----------|------|
| 北極星（North Star） | v3.0 | ✅ 確定 |
| Methodology | v1.7 | ✅ 確定 |
| Results 3.3（CFR/LPA） | v1.3 | ✅ 確定（Accept判定） |
| Results 3.4（集約無効） | v1.0 | ✅ 作成済み・査読待ち |

### 修正待ちセクション

| セクション | 状態 | 待ち事項 |
|-----------|------|---------|
| Results 3.5（deliberation vs aggregation） | 未作成 | +15pp修正・比較基準明示 |
| Results 3.6（world_consistency bias） | 未作成 | — |
| Abstract | v1.5（旧） | v10結果後に全面改訂 |
| Introduction | v1.2（旧） | v10結果後に部分改訂 |
| Related Work | 未着手 | — |
| Analysis/Discussion | 未着手 | — |
| Conclusion | 未着手 | — |
| Limitations | 草稿済み | v10結果を反映 |

### タイトル（確定候補）
```
「Deliberation Helps, Aggregation Doesn't:
 Diagnosing Multi-Agent LLM Coordination Limits」
（3AI承認済み・正式確定はv10結果後）
```

---

## v10完了後の作業順序

```
Step 1: v10結果を確認
  Case A → 北極星の主張が強化される
  Case B → 北極星を修正（「差は不安定」として記録）

Step 2: Results 3.5作成
  +15pp（v7 best_fixed 83% vs balanced_fixed 68%）
  deliberation vs aggregationの対比表

Step 3: Results 3.6作成
  world_consistency label biasの観察

Step 4: Abstract全面改訂
  v10結果を反映した北極星ベースで書き直し

Step 5: Introduction部分改訂
  Abstract確定後に修正

Step 6: タイトル確定

Step 7: Related Work作成
  Du et al. / Liang et al. / Wang et al.等

Step 8: Analysis/Discussion作成

Step 9: Conclusion + Limitations作成

Step 10: 全体通読・数字の統一確認
  「57%」「84%」等の旧数字が残っていないか

Step 11: Zenodo投稿
```

---

## 確定した重要な数字（生データ検証済み）

```
集約実験（v9シリーズ）:
  unanimous accuracy: 83.5%（932/1,400タスク）
  split accuracy:     62.6%（468/1,400タスク）
  差: 20.9pp
  1,400タスク中61件変更・正味-1タスク

役割分担（v7）:
  best_fixed:     83%（Solver/Verifier/Critic）
  balanced_fixed: 68%（全ノード同じ役割）
  差: +15pp

CFR（v9d・重複除外済み）:
  world_consistency: 4/35  = 11.4% [3.1%, 26.3%]
  math_elementary:   9/83  = 10.8% [5.0%, 19.7%]
  math_middle:      17/62  = 27.4% [16.6%, 40.2%]
  math_high:        12/57  = 21.1% [11.4%, 33.9%]
  ※ math_middleとmath_highのCIが重複 → v10で検証中

LPA（v9d）:
  world_consistency: 7/7   = 100%（n=7・CI [59%, 100%]）
  math_elementary:  18/22  = 81.8%
  math_middle:      13/22  = 59.1%
  math_high:        10/16  = 62.5%

単一エージェント（qwen2.5:7b）:
  world_consistency: 56/100 = 56.0%
  math_elementary:   16/99  = 16.2%
  math_middle:       24/75  = 32.0%
  math_high:         23/75  = 30.7%
  349/350件がconfident（閾値0.8）→ 閾値が機能しない
```

---

## 発見された誤りと修正履歴

```
① CFRとLPAの混同（最重大）
  「100%→82%→59%→55%」はCFRではなくLPA
  真のCFR: 11.4%→10.8%→27.4%→21.1%
  → Methodology v1.7・Results 3.3 v1.3で修正済み

② 「split: 57%」の誤り
  v9a単体の数字をシリーズ全体に一般化
  正しい数字（v9全体）: 62.6%
  → Results 3.4 v1.0で修正済み

③ 「unanimous: 84%」
  実際は83.5%（四捨五入で許容範囲）

④ 「+20pp」の誤り
  異なるタスクセット間の比較だった
  正しくは「+15pp（balanced_fixed比）」
  → Results 3.5で修正予定

⑤ math_highの重複データ（v9d）
  75タスクのはずが168行あった
  → 全分析で重複除外（first occurrence）済み

根本原因:
  実験レポートの数字を
  定義確認なしに論文に転記した
  → 今後は生データから直接計算・検証
```

---

## 論文執筆の原則（今回の教訓）

```
正しい手順:
  Step 1: 北極星（何を証明したいか）を先に決める
  Step 2: 証拠の定義を確定する（生データから計算できる形で）
  Step 3: 実験を設計・実行する
  Step 4: 生データから直接計算する
  Step 5: レポートと照合する（検証として）
  Step 6: 図・表を先に完成させる
  Step 7: 文章を書く（Abstractは最後）

誤りチェックリスト（論文に数字を書く前）:
  □ この数字は何の定義から来るか？
  □ 生データ（.jsonl）から直接計算できるか？
  □ レポートの数字と一致するか？
  □ 重複データが混入していないか？
```

---

## 実験・実装ロードマップ

```
v10結果待ち（実行中）
  ↓
論文執筆
  Results 3.5 → 3.6 → Abstract改訂 → Introduction
  → Related Work → Discussion → Conclusion
  → 全体通読 → Zenodo投稿
  ↓
v11（System A〜D比較）= D-1の検証実験
  ↓
┌─────────────────────┬─────────────────────┐
AAS v2 / HyperNCA             D-2・D-3・D-4
（B系・C系の実装）             （D-1の結果を受けて）
└─────────────────────┴─────────────────────┘
  ↓
残りのアイデア実装フェーズ
```

### 補足：B系・C系・D系の依存関係

```
D系（ハーネス系）: 縦に依存
  D-1 ハーネスネットワーク設計（v11で検証）
    ↓
  D-2 ハイブリッドパーサー
  D-3 アキネーター構造
  D-4 ベイズ的ボトルネック分析

B系・C系（エージェント・AAS系）: D系と独立
  C-1 AAS v2（過去ログ参照）← NCA-LLM全実験完了後
    ↓
  B-2 第3MetaAgent
  B-3 ゲーム理論AntiNode
  C-2 AAS v4
    ↓
  C-3 AAS v5
```

### アイデア整理ドキュメント（2026-04-04 commit: 002c4ee）

```
ideas/NCA-LLM_ideas_sorted.md
  19ファイル・16アイデアを5グループに分解

ideas/NCA-LLM_north_star_candidates.md
  北極星候補3つ・依存関係マップ・判断不能リスト
```
