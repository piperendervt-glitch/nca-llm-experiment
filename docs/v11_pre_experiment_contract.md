# Pre-Experiment Contract: v11

作成日: 2026-04-04
作成者: Robosheep
研究の北極星: A-4「shared_premisesの更新失敗がAI失敗の根本」
実験の位置づけ: D-1「どのノードをハーネス化できるか」のマッピング

---

## このドキュメントの目的

「実験前に何を証明したいかを明記する」ことで
以下の過去の失敗を再発させない:

- 北極星なしで実験を走らせて後から解釈した（v1〜v9）
- 小サンプルで主張を作って大サンプルで崩れた（v9d CFR）
- 定義確認なしに数字を転記した（CFR/LPA混同）

---

## 実験の仮説（事前登録）

### H1: System B ≈ System A（集約コード化は精度に影響しない）

```
根拠:
  v9シリーズで集約改善が全て+0ppだった
  コードによる多数決とLLMによる多数決は
  同じ情報から同じ結論を出すはず

falsifiable条件:
  System Bの精度がSystem Aと
  統計的に有意に異なれば棄却（alpha=0.05）

記録すべき「失敗」:
  B < A の場合:
    「LLMによる集約にはコードでは捉えられない
     何らかの情報処理がある」
  B > A の場合:
    「LLMによる集約にはノイズが含まれており
     コードの方が純粋な多数決を実現する」
```

### H2: System D-1b > System A（数値抽出ハーネス化は有効）

```
根拠:
  LLMは数値計算を間違える（計算ミス）
  Pythonは数値計算を間違えない（決定論的）
  → 計算部分をハーネス化すれば精度が上がるはず

対象タスク:
  math_elementary（計算・数列）
  math_middle（代数・方程式）
  math_high（微分・多項式）

非対象:
  world_consistency（数値計算なし）

falsifiable条件:
  D-1bがmath系タスクでSystem Aより
  統計的に有意に高ければ仮説支持（alpha=0.05）

記録すべき「失敗」:
  D-1b ≈ A の場合:
    「LLMの数値計算ミスは精度のボトルネックではない
     意味的理解の方が支配的」
```

### H3: System D-1c > System A（論理ハーネス化は有効）

```
根拠:
  形式的論理（A>B, B>C → A>C）は
  コードで完全に記述できる
  LLMが論理推論を間違える場合は
  ハーネスで置き換えられる

対象タスク:
  math_elementary（logical）
  math_middle（simultaneous_eq・polynomial）
  math_high（quadratic_ineq）

falsifiable条件:
  D-1cが論理系タスクでSystem Aより
  統計的に有意に高ければ仮説支持（alpha=0.05）

記録すべき「失敗」:
  D-1c ≈ A の場合:
    「LLMの論理推論ミスは精度のボトルネックではない
     問題を式に落とす段階（意味理解）が支配的」
```

### H4: world_consistencyではD-1b・D-1cの効果なし

```
根拠:
  world_consistencyは意味的矛盾検出タスク
  数値計算も形式的論理も不要
  → ハーネス化できる部分がない

falsifiable条件:
  D-1b・D-1cのworld_consistency精度が
  System Aと統計的に有意に異なれば棄却

記録すべき「失敗」:
  D-1b または D-1c > A（WC）の場合:
    「world_consistencyにも
     ハーネス化できる構造が存在する」
    （予想外の発見として記録）
```

---

## 測定指標の定義（計算式）

### 主要指標

```
全体精度:
  overall_accuracy = sum(is_correct) / n_total

タスクセット別精度:
  accuracy(τ) = sum(is_correct for r in τ) / len(τ)

System間の差:
  delta = accuracy(System X) - accuracy(System A)

統計的有意差:
  two-proportion z-test（alpha=0.05・両側）
  H0: accuracy(X) = accuracy(A)
```

### CFR（v11でも測定）

```
CFR(τ) = n_wrong_unanimous(τ) / n_unanimous(τ)

unanimous(t): vote_distributionで全員一致
wrong(t): is_correct = False

95% CI: Clopper-Pearson
```

### ハーネス化効果の測定

```
harness_gain(τ) = accuracy(D-1x, τ) - accuracy(A, τ)

タスクタイプ別:
  各task_typeで個別に測定
  ハーネス化が有効なタスクタイプを特定
```

---

## 使用するフィールド（jsonl）

```
必須フィールド:
  task_id:        重複検出に使用
  task_set:       タスクセット（world_consistency等）
  task_type:      タスクタイプ（calculation等）
  label:          正解ラベル（CORRECT/INCORRECT）
  prediction:     モデルの予測
  is_correct:     prediction == label
  vote_distribution: 各ノードの票数
  elapsed_sec:    実行時間

System D-1b・D-1c追加フィールド:
  harness_used:   True/False（ハーネスが使われたか）
  harness_result: ハーネスの計算結果
  llm_result:     LLMの解釈結果
  conflict:       harness_resultとllm_resultが異なる場合True
```

---

## 必要サンプルサイズ（事前計算済み）

```
検出したい差: 3pp（System Aが77%として80%を検出）
alpha=0.05（両側）・power=0.80

n = (z_α/2 + z_β)² × (p1(1-p1) + p2(1-p2)) / delta²
  = (1.96 + 0.84)² × (0.77×0.23 + 0.80×0.20) / 0.03²
  ≈ 880タスク

現在の計画: 350タスク（タスクセットが75〜100の制約）

→ 350タスクで検出できる差: 約5pp以上
  3pp以下の差は検出困難
  → 「3pp未満の差は統計的に確認できない」
    という限界を事前に明記する
```

---

## 重複除外の方針

```
全実験で:
  task_idのfirst occurrenceのみ使用
  重複があれば verify_results.py が警告

実装:
  seen = set()
  dedup_records = []
  for r in records:
      if r['task_id'] not in seen:
          seen.add(r['task_id'])
          dedup_records.append(r)
```

---

## 「失敗」の定義と記録方針

```
全ての仮説について:
  支持された場合もされなかった場合も
  同等に価値ある発見として記録する

記録フォーマット:
  仮説: H{N}
  結果: 支持 / 棄却 / 判定不能
  数字: delta=?pp, p=0.??
  解釈: 「この結果が示すことは...」
  次の問い: 「この結果から生まれる新しい疑問は...」
```

---

## 実験完了後のチェックリスト

```
□ verify_results.py を実行した
□ 重複task_idがない（またはfirst occurrenceで除外）
□ 各System 350タスクが揃っている
□ 生データから直接計算した
□ 95% CIを計算した
□ H1〜H4の結果を記録した
□ 北極星A-4との接続を書いた
□ コミット・プッシュした
```

---

## 北極星A-4との接続（実験後に記入）

```
実験結果を記入する欄:

ハーネス化できたノード:
  [実験後に記入]

ハーネス化できなかったノード:
  [実験後に記入]

shared_premisesが明確だったタスクタイプ:
  [実験後に記入]

shared_premisesが曖昧だったタスクタイプ:
  [実験後に記入]

A-4への含意:
  [実験後に記入]
```
