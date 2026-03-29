# 引継ぎドキュメント: NCA LLM Experiment

最終更新: 2026-03-29

---

## プロジェクト概要

NCA（Neural Cellular Automata）的更新ルールをLLMノードネットワークで検証する実験。
3つのLLMノードをリング状に配置し、各ノードが隣接ノードの出力のみを見て回答を更新する。

**対照群**: `sdnd-proof` の `fixed_network.py`（固定パイプライン Node1→2→3）
**実験群**: `nca_network.py`（NCA的同期更新）
**タスク**: `world_consistency`（ワールドルールと文章の矛盾検出、100問）
**依存**: httpx + scipy（PyTorch不使用）

---

## リポジトリ

| リポジトリ | URL |
|-----------|-----|
| 実験群（メイン） | https://github.com/piperendervt-glitch/nca-llm-experiment |
| 対照群（流用元） | https://github.com/piperendervt-glitch/sdnd-proof |

---

## ローカル環境

### 新PC（メイン実験機）
| 項目 | 内容 |
|------|------|
| OS | Windows 11 |
| GPU | NVIDIA RTX 5060 Ti 16GB（Ollama 100% GPU動作確認済み）|
| 実験フォルダ | `C:\Users\pipe_render\nca-llm-experiment\` |
| 対照群フォルダ | `C:\Users\pipe_render\sdnd-proof\` |
| モデル | qwen2.5:3b, qwen2.5:7b, llama3:latest, llama3.1:8b, llama3.2:3b, mistral:7b, gemma2:2b, fool-qwen:latest |

### 旧PC（サブ機）
| 項目 | 内容 |
|------|------|
| GPU | NVIDIA GTX 1650 4GB |
| モデル | qwen2.5:3b, qwen2.5-coder:3b |
| 用途 | ドキュメント作業・軽量タスクのみ |

### 注意事項
- `gh` CLIはPATHが通っていないため `git push` を直接使う
- sdnd-proofのパスは `C:\Users\pipe_render\sdnd-proof\src` を参照

---

## 実験結果（完了済み）

| バージョン | 全体正解率 | CONSISTENT | CONTRADICTION | 備考 |
|-----------|-----------|-----------|---------------|------|
| Fixed（対照群） | 45.0% | 2.0% | 88.0% | 固定パイプライン |
| NCA v1 | 49.0% | 0.0% | 98.0% | グループシンク：99/100がCONTRADICTIONに収束 |
| NCA v2 | 55.0% | 80.0% | 30.0% | アンチ迎合プロンプト・過補正 |
| NCA v3 | 52.0% | 6.0% | 98.0% | デビルズアドボケート・効果薄 |
| NCA v4 | 53.0% | 24.0% | 82.0% | 信頼度重み付き・最もバランス |
| NCA v5（最良） | 61.0% | 40.0% | 82.0% | 異種モデル全56通り・qwen2.5:7b+llama3.2:3b+mistral:7b |
| 仮説1（v5.5） | 54.0% | 26.0% | 82.0% | v5最良+5ステップ+信頼度重み付き・65%未達 |
| Self-Consistency | 56.0% | 82.0% | 30.0% | 同3モデル・独立実行・多数決のみ |

### 重要な発見
- **ミラー効果**: NCA（CONTRADICTION 82%）とSelf-Consistency（CONSISTENT 82%）が同じ3モデルで逆のバイアスを示した → NCAの更新プロセス自体がCONTRADICTIONバイアスを生成している
- **ステップ数の問題**: ステップ5はグループシンクを増幅（72→78）。少ない方が良い可能性
- **split決定と精度の無相関**: r = -0.089（v5レポート）
- **モデルサイズより役割の多様性が重要**: 7b+3b+7bが7b+7b+7bより高精度

---

## 実行中

| バージョン | 内容 | 状況 |
|-----------|------|------|
| v6 | モデル組み合わせ＋合意強度＋ステップ数をランダムサンプリング（100試行） | 🔄 15/100完了・推定残り30時間 |

### v6のパラメータ空間
- モデルプール: 6モデル（fool-qwen除外）
- 合意強度: 各ノード独立・0〜100%（10%刻み）
- ステップ数: 1〜5
- seed=42（再現性確保）

---

## 今後のタスクリスト

| バージョン | 内容 |
|-----------|------|
| v7 | 数学タスク × 役割分担NCA |
| v8 | 適応的モデル選択 |
| v9 | 動的信頼度重み付けNCA（メタエージェント + 過去ログ参照 + ε-greedy） |
| v10 | 動的ノード選択NCA（複数メタエージェント競合 + ε-greedy） |
| v11 | 既存アーキテクチャとの比較実験（論文用） |

### v11完了後
1. nca-llm-experimentの論文をZenodoに投稿
2. Claudeプロジェクト「aas-v2」を新規作成
3. GitHubに`aas-v2`リポジトリを新規作成
4. 実験データをaas-v2/dataにコピー
5. aas-v2の実験設計・実装開始

---

## 発表媒体（AASと同じパイプライン）

| 媒体 | URL |
|------|-----|
| 論文（Zenodo） | 未投稿（全実験完了後） |
| コード（GitHub） | https://github.com/piperendervt-glitch/nca-llm-experiment |
| ORCID | https://orcid.org/0009-0000-6486-9678 |
| X | https://x.com/pipe_render |
| note | https://note.com/pipe_render |

---

## ファイル構成（新PC）

```
C:\Users\pipe_render\nca-llm-experiment\
├── nca_network.py           # 最新NCAネットワーク
├── nca_network_v1.py        # v1: ベースライン
├── nca_network_v2.py        # v2: アンチ迎合
├── nca_network_v3.py        # v3: デビルズアドボケート
├── nca_network_h1.py        # 仮説1: v5最良+信頼度重み付き
├── nca_network_v6.py        # v6: ランダムサンプリング
├── run_experiment_nca.py    # Fixed vs NCA 比較実験
├── run_hypothesis1.py       # 仮説1 vs Self-Consistency
├── run_v6_sampling.py       # v6ランダムサンプリング実行
├── bias_profiler.py         # モデル単体バイアス確認
├── self_consistency.py      # Self-Consistency実装
├── ideas/                   # アイデアメモ
│   ├── idea_aas_v2_past_log_reference.md
│   ├── idea_queen_of_hearts_effect.md
│   └── idea_antithesis_agent.md
├── results/
│   ├── fixed_results.jsonl
│   ├── nca_results.jsonl
│   ├── nca_v2_results.jsonl
│   ├── nca_v3_results.jsonl
│   ├── nca_v4_results.jsonl
│   ├── nca_h1_results.jsonl
│   ├── self_consistency_results.jsonl
│   ├── bias_profile_*.jsonl
│   ├── v5/
│   │   ├── summary.jsonl
│   │   ├── combo_*.jsonl
│   │   └── v5_report.md
│   └── v6/
│       ├── v6_summary.jsonl  # 実行中
│       └── sample_*.jsonl
├── reports/
│   └── v5_report.md
├── requirements.txt
└── README.md
```

---

## 重要なアイデアメモ（ideas/フォルダに保存済み）

### 1. 過去ログ参照型AAS
AASの重み更新ルールに過去ログ参照を組み込む改良案。
ゼロスタートではなく実績ある重みで初期化し、ε-greedyで探索を維持。
→ `ideas/idea_aas_v2_past_log_reference.md`

### 2. ハートの女王化
より賢いAIを使う人間が自身の過ちを指摘されにくくなる現象。
グループシンクの人間レベルの対応概念。
→ `ideas/idea_queen_of_hearts_effect.md`

### 3. 反対案専用エージェント（アンチテーゼAI）
共通ルールに従いながら常に多数意見とは異なる結論を提案するエージェント。
テーゼAI + アンチテーゼAIの両運用で人間のハートの女王化を防ぐ。
→ `ideas/idea_antithesis_agent.md`

---

## 関連研究

- **MAD**: Du et al. (2023) arXiv:2305.14325 — Multi-Agent Debate
- **DoT問題**: Liang et al. (2024) EMNLP — Degeneration of Thought
- **AAS**: https://github.com/piperendervt-glitch/sdnd-proof（p=0.0007, d=4.29）
- **Growing NCA**: Mordvintsev et al. (2020) https://distill.pub/2020/growing-ca/

---

## 技術メモ

- タスク入力フォーマット: `"World rule: {world_rule}\nStatement: {question}"`
- verdict変換: `"CONSISTENT"→True` / `"CONTRADICTION"→False` / `"UNKNOWN"→None`
- sdnd-proofのインポート: `sys.path.insert(0, "C:/Users/pipe_render/sdnd-proof/src")`
- Ollamaが起動していないと実験が止まるので注意
- v6はresume対応済み（中断後に再実行すると続きから再開）
