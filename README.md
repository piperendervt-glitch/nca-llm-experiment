# NCA LLM Experiment

> Can Neural Cellular Automata-style update rules improve LLM reasoning?

3 LLM nodes arranged in a ring. Each node only sees its neighbors' previous output — no central coordinator, no shared memory. Inspired by [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/).

**No PyTorch. Just Ollama + httpx + scipy.**

---

## Overview

This experiment applies NCA-style local update rules to a network of LLM nodes and compares it against a fixed sequential pipeline (baseline from [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof)).

### Network Topology

```
  ┌─────────────────────────────────────────┐
  │                                         │
  ▼                                         │
Node 0  ◄──────►  Node 1  ◄──────►  Node 2
                                         │
  ▲                                         │
  └─────────────────────────────────────────┘

Ring topology. Each node sees only left/right neighbors' previous output.
```

### Update Rule (NCA-style)

At each step `t`, every node updates using only step `t-1` outputs from its two neighbors:

```
node[i].output[t] = LLM(task_input, neighbor[left].output[t-1], neighbor[right].output[t-1])
```

All nodes update synchronously — the same rule as NCA's parallel cell updates.

---

## Tasks

### `world_consistency` (v1–v6)
Given a world rule and a statement, detect whether the statement contradicts the rule.
- 100 tasks total (50 consistent, 50 contradictory)
- Labels: `CONSISTENT` / `CONTRADICTION`

### `math` (v7–)
Elementary to high school math verification tasks.
- Labels: `CORRECT` / `INCORRECT`
- v7: 100 elementary tasks (calculation, logic, word problems, sequences)
- v7.5: 75 middle school tasks (grade 7 / 8 / 9, 25 each)
- v7.6: 75 high school tasks (grade 10 / 11 / 12, 25 each)
- v8: 350 tasks (all of the above) with adaptive model selection

---

## Results

### world_consistency tasks (v1–v6)

| Version | Overall | CONSISTENT | CONTRADICTION | Notes |
|---------|---------|-----------|---------------|-------|
| Fixed (baseline) | 45% | 2% | 88% | Sequential pipeline |
| NCA v1 | 49% | 0% | 98% | Groupthink: 99/100 → CONTRADICTION |
| NCA v2 | 55% | 80% | 30% | Anti-sycophancy — overcorrected |
| NCA v3 | 52% | 6% | 98% | Devil's advocate — too weak |
| NCA v4 | 53% | 24% | 82% | Confidence-weighted updates |
| NCA v5 (best) | 61% | 40% | 82% | Heterogeneous models |
| NCA v5 (balanced) | 56% | 56% | 56% | Perfectly symmetric |
| **NCA v6 (best)** | **63%** | 30% | 96% | agree=[30,80,80], steps=3 |
| NCA v6 (balanced) | 60% | 62% | 58% | Best balance result |

### math tasks (v7)

| Pattern | Overall | CORRECT | INCORRECT | Calc | Logic | Word | Seq |
|---------|---------|---------|-----------|------|-------|------|-----|
| best_fixed | **83%** | 77% | 90% | 92% | 72% | 92% | 76% |
| best_rotating | 81% | **96%** | 65% | 92% | **100%** | 72% | 60% |
| balanced_fixed | 68% | 73% | 62% | 80% | 68% | 68% | 56% |
| balanced_rotating | 80% | 87% | 73% | 88% | 84% | 76% | 72% |
| single_agent | **83%** | 69% | **98%** | 76% | 84% | 84% | 88% |

### math difficulty series (v7 → v7.5 → v7.6)

| Pattern | v7 (Elementary) | v7.5 (Middle) | v7.6 (High School) | Total Drop |
|---------|----------------|--------------|-------------------|------------|
| **best_fixed** | **83%** | 72% | **77%** | **-6pp** |
| single_agent | **83%** | 75% | 71% | -12pp |
| balanced_rotating | 80% | **77%** | 68% | -12pp |
| best_rotating | 81% | 73% | 63% | -18pp |
| balanced_fixed | 68% | 57% | 56% | -12pp |

### adaptive model selection (v8)

| Task Set | Adaptive | Best Fixed | Diff |
|----------|----------|------------|------|
| world_consistency | **66%** | 63% | +3pp |
| math_elementary | **85%** | 83% | +2pp |
| math_middle | 76% | **77%** | -1pp |
| math_high | **81%** | 77% | +4pp |
| **Overall** | **77%** | 75% | **+2pp** |

Routing: easy(14%) → single_agent / medium(43%) → best_fixed / hard(43%) → balanced_rotating

### Key Findings

**Groupthink is real and severe, but model diversity helps.**
v1 had 99/100 tasks converge to CONTRADICTION. Heterogeneous models (v5) reduced this and raised accuracy to 61%.

**The mirror effect: NCA and Self-Consistency have opposite biases.**
Same 3 models: NCA → 82% CONTRADICTION, Self-Consistency → 82% CONSISTENT. The NCA update process itself generates bias.

**Step count is the dominant structural variable (r=0.821 with groupthink).**
Each additional step converts ~9 split decisions into CONTRADICTION unanimity. Steps=3 is optimal.

**Agreement intensity has a non-linear optimum at 60-80%.**
Both extremes (full independence or full conformity) underperform.

**Asymmetric agreement outperforms symmetric.**
One dissenter node at 30% + two nodes at 80% beats uniform agreement.

**Role rotation is a de-biasing mechanism.**
Rotating roles boost CORRECT accuracy by +14–19pp. Logic tasks benefit most: fixed 72% → rotating 100%. Valid range: up to middle school difficulty. At high school level, rotation becomes harmful (INCORRECT drops to 31%).

**Multi-model NCA helps more on ambiguous tasks.**
On structured math, single agent (83%) ties with best NCA. On semantic world_consistency, NCA outperforms single agent by ~10pp.

**The INCORRECT/CONTRADICTION bias is universal.**
LLMs prefer to find fault across both math and semantic domains.

**Operation type, not grade level, determines LLM difficulty.**
Pattern-match (80-100%) > formula+verify (60-80%) > multi-step procedure (40-60%) > symbolic manipulation (20-40%). Stable across all difficulty levels.

**The difficulty wall is at middle school, not high school.**
best_fixed: 83% → 72% → 77%. High school trig/logs are easier than middle school simultaneous equations due to training data coverage.

**Hard task ceiling at 65% across all domains.**
math_middle hard (64%), math_high hard (64%), world_consistency (66%) all cluster at 65%. This is a model capability limit, not an architecture limit — the primary target for v9+.

**Adaptive routing validates the difficulty hierarchy.**
Embedding classifier correctly identifies task difficulty from v7-v7.6 findings. Easy → 86%, Medium → 85%, Hard → 65%.

```
v1: groupthink → 99/100 CONTRADICTION (same-model NCA)
v5: heterogeneous models → 61% (diversity breaks groupthink)
v6: agreement tuning → 63%, steps=3 optimal (r=0.821)
v7: role-division → 83% on math, rotation eliminates logic bias
v7→v7.6: difficulty wall at middle school, operation type determines accuracy
v8: adaptive routing → 77% overall (+2pp), 65% hard ceiling identified
```

---

## Setup

### Requirements

- [Ollama](https://ollama.com/) running locally
- Python 3.10+

```bash
ollama pull qwen2.5:3b qwen2.5:7b llama3:latest llama3.1:8b llama3.2:3b mistral:7b
pip install httpx scipy
```

### Run

```bash
# Single NCA network test (3 tasks)
python nca_network.py

# Full comparison experiment (Fixed vs NCA, 100 tasks each)
python run_experiment_nca.py

# v5: all 56 heterogeneous model combinations
python run_all_combinations.py

# v6: random sampling over agreement intensity and step count
python run_v6_sampling.py --trials 100

# v7: role-division NCA on elementary math tasks
python run_v7.py

# v7.5: role-division NCA on middle school math tasks
python run_v7_5.py

# v7.6: role-division NCA on high school math tasks
python run_v7_6.py

# v8: adaptive model selection (350 tasks, embedding classifier)
python run_v8.py
```

---

## File Structure

```
nca-llm-experiment/
├── nca_network.py                    # NCA network (v1 baseline)
├── nca_network_v6.py                 # v6: agreement intensity per node
├── nca_network_v7.py                 # v7: role-division NCA
├── nca_network_v8.py                 # v8: adaptive routing wrapper
├── run_experiment_nca.py             # Fixed vs NCA v1-v4 runner
├── run_all_combinations.py           # v5: all 56 model combinations
├── run_v6_sampling.py                # v6: random sampling runner
├── run_v7.py                         # v7: role-division runner
├── run_v7_5.py                       # v7.5: middle school tasks runner
├── run_v7_6.py                       # v7.6: high school tasks runner
├── run_v8.py                         # v8: adaptive model selection runner
├── bias_profiler.py                  # Single-model bias profiling
├── embedding_classifier.py           # v8: difficulty classifier
├── math_task_generator.py            # v7: elementary math tasks
├── middle_school_task_generator.py   # v7.5: middle school math tasks
├── high_school_task_generator.py     # v7.6: high school math tasks
├── ideas/                            # Research idea memos
├── reports/                          # Experiment reports
│   ├── v5_report.md
│   ├── v6_report.md
│   ├── v7_report.md
│   ├── v7_5_report.md
│   ├── v7_6_report.md
│   └── v8_report.md
└── results/
    ├── fixed_results.jsonl
    ├── nca_results.jsonl             # v1
    ├── nca_v2_results.jsonl
    ├── nca_v3_results.jsonl
    ├── nca_v4_results.jsonl
    ├── v5/                           # All 56 combination results
    ├── v6/                           # 100 random sampling results
    ├── v7/                           # Role-division elementary math
    ├── v7_5/                         # Middle school math results
    ├── v7_6/                         # High school math results
    └── v8/                           # Adaptive model selection results
```

---

## Baseline

The fixed network baseline is taken directly from [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — a prior experiment on adaptive vs. fixed LLM topologies (p=0.0007, d=4.29).

---

## Related

- [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — Adaptive Artificial Synapse (AAS) experiment
- [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) — Original NCA paper
