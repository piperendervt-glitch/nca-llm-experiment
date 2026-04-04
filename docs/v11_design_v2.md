# v11 実験設計指示書

最終更新: 2026-04-04
研究の北極星: A-4「shared_premisesの更新失敗がAI失敗の根本」
v11の位置づけ: D-1「どのノードをハーネス化できるか」の検証実験

---

## v11の目的（北極星との接続）

```
研究の北極星 A-4:
  「AIの失敗の多くは
   人間がAIとの契約書（shared_premises）を
   更新しなかった結果である」

v11がこれに答える方法:
  「ハーネス化できるノード」=
    shared_premisesが明確に記述できるノード
    （コードで表現できる = 前提が完全）

  「ハーネス化できないノード」=
    shared_premisesが曖昧なノード
    （LLMが必要 = 意味的判断が必要）

D-1の問い:
  「どのノードがハーネスで置き換えられるか」を
  マッピングする
```

---

## 測定すべき3つのこと

```
1. ノード別: どのノードがハーネスで置き換えられるか
   → 各ノードを1つずつハーネス化して精度変化を測定

2. タスク別: どのタスクタイプがハーネスに向くか
   → 計算・論理・文章題・数列・意味的矛盾検出

3. 精度飽和点: 何ノードで精度が頭打ちになるか
   → LLMノードを削減しながら精度を追跡
```

---

## 比較対象（全て同条件で実施）

| System | 内容 | LLMの役割 | 期待精度 |
|--------|------|----------|---------|
| System A | NCA-LLM フル版（現在の実装） | 全て | 76〜83% |
| System B | LLM推論 + コード集約 | 推論のみ | ±0pp期待 |
| System C | 単一LLMパーサー + 完全ハーネス | 抽出のみ | 未知 |
| System D-1a | 集約ノードのみハーネス化 | 推論のみ | ±0pp期待 |
| System D-1b | 数値抽出ノードのみハーネス化 | 意味解釈のみ | +3〜5pp期待 |
| System D-1c | 形式的論理ノードのみハーネス化 | 意味判断のみ | +5〜10pp期待 |

---

## 実験の原則

```
「1変数1実験」を厳守（v9と同じ原則）
  各Systemで変える変数は1つのみ
  それ以外はSystem Aと完全に同一

タスクセット: 350タスク（v9と同一）
  world_consistency: 100タスク
  math_elementary:   100タスク
  math_middle:        75タスク
  math_high:          75タスク

統計処理:
  95% CI（Clopper-Pearson）
  二比率z検定（System Aとの比較）
  重複除外（first occurrence）
```

---

## Phase 1: 各Systemの実装と実験

### System A（ベースライン・再確認）

```
実装: 既存のbest_fixed設定をそのまま使用
  nca_network_v9d.py（AntiNodeなし・Level-Kなし）
  または nca_network_v7.py

設定:
  Models: qwen2.5:7b / llama3:latest / mistral:7b
  Roles: Solver / Verifier / Critic（固定）
  Agreement: [30, 80, 80]
  Steps: 3
  Aggregation: simple majority

出力:
  results/v11/system_a_results.jsonl
```

### System B（LLM推論 + コード集約）

```
変更点: 集約のみをコードに置き換える
  3ノードの出力（CORRECT/INCORRECT）を
  Pythonの多数決コードで集約
  （LLMによる集約ではなくコードによる集約）

実装:
  各ノードはSystem Aと同じプロンプトで推論
  最終集約のみ: Counter(outputs).most_common(1)[0][0]

期待:
  v9の知見から ほぼ変化なし（±1pp）
  「集約のコード化は精度に影響しない」の確認

出力:
  results/v11/system_b_results.jsonl
```

### System C（単一LLMパーサー + 完全ハーネス）

```
変更点: 3ノードを1ノードに削減
  単一のLLM（qwen2.5:7b）が問題を解く
  回答からCORRECT/INCORRECTをパースするのみ

数学タスクの場合:
  LLM: 「この数式は正しいですか？」に答える
  ハーネス: 実際の計算はPythonで検証して
           LLMの回答と照合する

world_consistencyの場合:
  LLM: 矛盾を判定する（ハーネス化困難）
  ハーネス: 回答をパースするのみ

出力:
  results/v11/system_c_results.jsonl
```

### System D-1a（集約ノードのみハーネス化）

```
= System Bと同一
  既にSystem Bで測定済み
  → スキップ可
```

### System D-1b（数値抽出ノードのみハーネス化）

```
変更点: 数学タスクの数値抽出をコード化
  LLMは「式の意味」を解釈するのみ
  実際の数値・演算子の抽出はPython正規表現

実装方針:
  Step 1: LLMに問題を読ませて
          「何を計算すべきか」を自然言語で出力
  Step 2: Pythonが数値・演算子を正規表現で抽出
  Step 3: Pythonが計算を実行
  Step 4: LLMの解釈とPythonの計算結果を照合

対象タスク: math_elementary・math_middle・math_high
非対象: world_consistency（数値抽出不要）

出力:
  results/v11/system_d1b_results.jsonl
```

### System D-1c（形式的論理ノードのみハーネス化）

```
変更点: 論理的な推論をコード化
  例: 「A > B かつ B > C ならば A > C」
      → Pythonで判定

対象タスク:
  math_elementary: logical（論理推論）
  math_middle: simultaneous_eq（連立方程式）
  math_high: quadratic_ineq（二次不等式）

実装方針:
  sympy を使用して方程式・不等式を解く
  LLMは「式を立てる」のみ担当
  「計算・判定」はsympyが担当

出力:
  results/v11/system_d1c_results.jsonl
```

---

## Phase 2: 結果の集計と分析

### 測定する指標

```
各Systemについて:
  1. 全体精度・95% CI
  2. タスクセット別精度
  3. タスクタイプ別精度（特にD-1b・D-1cで重要）
  4. System Aとの差（pp）
  5. 統計的有意差（p値）

ハーネス化効果の測定:
  「どのノードのハーネス化が
   最も精度を上げたか」
  = D-1b と D-1c の比較
```

### 出力フォーマット

```
================================================================
v11 System Comparison Results
================================================================
System   | Overall | WC  | Elem | Mid | High | vs A | p-value
---------|---------|-----|------|-----|------|------|--------
System A |  ??.?%  | ??% |  ??% | ??% |  ??% |  —   |   —
System B |  ??.?%  | ??% |  ??% | ??% |  ??% | ±?pp |  0.??
System C |  ??.?%  | ??% |  ??% | ??% |  ??% | ±?pp |  0.??
D-1b     |  ??.?%  | n/a |  ??% | ??% |  ??% | ±?pp |  0.??
D-1c     |  ??.?%  | n/a |  ??% | ??% |  ??% | ±?pp |  0.??
================================================================

Key Questions:
  Q1: どのノードのハーネス化が最も有効か？
  Q2: world_consistencyはハーネス化に向かないか？
  Q3: 精度飽和点は何ノードか？
================================================================
```

---

## 実装の優先順位

```
Priority 1（すぐ実装・シンプル）:
  System A（ベースライン再確認）
  System B（集約のみコード化）

Priority 2（中程度の複雑さ）:
  System C（単一LLM + ハーネス）
  System D-1b（数値抽出ハーネス化）

Priority 3（複雑・sympy使用）:
  System D-1c（形式的論理ハーネス化）
```

---

## 実装ファイル構成

```
nca-llm-experiment/
├── nca_network_v11_a.py    # System A（ベースライン）
├── nca_network_v11_b.py    # System B（コード集約）
├── nca_network_v11_c.py    # System C（単一LLM）
├── nca_network_v11_d1b.py  # System D-1b（数値抽出）
├── nca_network_v11_d1c.py  # System D-1c（論理ハーネス）
├── run_v11.py              # 全System一括実行
└── results/v11/
    ├── system_a_results.jsonl
    ├── system_b_results.jsonl
    ├── system_c_results.jsonl
    ├── system_d1b_results.jsonl
    └── system_d1c_results.jsonl
```

---

## 北極星A-4との接続（実験後の解釈方針）

```
実験結果をA-4の視点で解釈する:

「ハーネス化できた」= 精度が維持または向上
  → shared_premisesが明確に記述できた
  → コードで前提を完全に表現できた

「ハーネス化できなかった」= 精度が低下
  → shared_premisesが曖昧
  → LLMの意味的判断が不可欠

最終的に示したいこと:
  「LLMが必要な部分はshared_premisesが
   明確でない部分だけである」
  = A-4の「前提の明確化」という主張の実証
```

---

## 注意事項

```
論文の北極星は現在「保留」
  → v11の結果を見てから決める
  → 実験前に「何を証明したいか」を
    仮説として明記しておく（事前登録の精神）

仮説（事前登録）:
  H1: System B ≈ System A（集約コード化は無効）
  H2: System D-1b > System A（数値抽出ハーネス化は有効）
  H3: System D-1c > System A（論理ハーネス化は有効）
  H4: world_consistencyではD-1b・D-1cの効果なし

必要サンプルサイズ:
  350タスク（各System）
  System Aとの差3pp以上を検出するにはn=350で十分
  （p1=0.77, p2=0.80, alpha=0.05, power=0.80）
```
