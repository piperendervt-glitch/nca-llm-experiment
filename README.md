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

## Task

**`world_consistency`**: Given a world rule and a statement, detect whether the statement contradicts the rule.

- 100 tasks total (50 consistent, 50 contradictory)
- World rules and sentences sourced from [sdnd-proof/task_generator.py](https://github.com/piperendervt-glitch/sdnd-proof/blob/main/src/task_generator.py)
- Labels: `CONSISTENT` (no contradiction) / `CONTRADICTION`

---

## Results

| Version | Overall Acc | CONSISTENT Acc | CONTRADICTION Acc | vs Fixed | Notes |
|---------|------------|----------------|-------------------|----------|-------|
| Fixed Network (baseline) | 45.0% | 2.0% | 88.0% | --- | Sequential Node1→2→3 pipeline |
| NCA v1 | 49.0% | 0.0% | 98.0% | +4.0% | Groupthink: 99/100 tasks converged to CONTRADICTION |
| NCA v2 | 55.0% | 80.0% | 30.0% | +10.0% | Anti-sycophancy prompt — overcorrected |
| NCA v3 | 52.0% | 6.0% | 98.0% | +7.0% | Devil's advocate rule — too weak |
| NCA v4 | 53.0% | 24.0% | 82.0% | +8.0% | Confidence-weighted updates |
| NCA v5 (best) | 61.0% | 40.0% | 82.0% | +16.0% | Heterogeneous models — best same-config result |
| NCA v5 (balanced) | 56.0% | 56.0% | 56.0% | +11.0% | llama3 + llama3.1 + mistral — perfectly symmetric |
| **NCA v6 (best)** | **63.0%** | 30.0% | 96.0% | **+18.0%** | qwen2.5:7b + llama3 + mistral, agree=[30,80,80], steps=3 |
| NCA v6 (balanced) | 60.0% | 62.0% | 58.0% | +15.0% | mistral + llama3 + llama3.1, agree=[80,70,10], steps=2 |

### Groupthink Statistics

| Version | All CONTRADICTION | All CONSISTENT | Split |
|---------|:-----------------:|:--------------:|:-----:|
| NCA v1 | 99 | 0 | 0 |
| NCA v2 | 17 | 65 | 18 |
| NCA v3 | 77 | 2 | 21 |
| NCA v4 | 75 | 17 | 8 |
| NCA v5 best | 57 | 15 | 28 |
| NCA v6 best | 73 | 8 | 19 |
| NCA v6 balanced | 35 | 42 | 23 |

### Key Findings

**Groupthink is real and severe, but model diversity helps.**
v1 had 99/100 tasks converge unanimously to CONTRADICTION. Introducing heterogeneous models (v5) reduced this to 57/100 and raised accuracy to 61%.

**The mirror effect: NCA and Self-Consistency have opposite biases.**
Using the same 3 models, NCA produced 82% CONTRADICTION while Self-Consistency produced 82% CONSISTENT. The NCA update process itself generates CONTRADICTION bias.

**Step count is the dominant structural variable (r=0.821 with groupthink).**
Each additional step converts ~9 split decisions into CONTRADICTION unanimity. Steps=3 is the optimal trade-off between accuracy and bias amplification.

**Agreement intensity has a non-linear optimum at 60-80%.**
Moderate agreement (60-80%) achieves the best overall accuracy. Both extremes (full independence or full conformity) underperform.

**Asymmetric agreement outperforms symmetric.**
Having one node at low agreement (30%) while others are at high agreement (80%) produces better results than uniform agreement across all nodes. The "dissenter" role is structurally valuable.

**mistral:7b is the key balancer model.**
It appears in 7 of the top 10 v6 trials and is essential for achieving high CONSISTENT accuracy. Excluding it consistently degrades balance.

```
v1: [CONTRADICTION, CONTRADICTION, CONTRADICTION] → 99% of the time (groupthink)
v2: [CONSISTENT,    CONSISTENT,    CONSISTENT   ] → overcorrected
v5: heterogeneous models → 61% (best single config)
v6: agreement tuning → 63% (new record), 60% balanced (all-time best balance)
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
```

---

## File Structure

```
nca-llm-experiment/
├── nca_network.py           # NCA network (v1 baseline)
├── nca_network_v6.py        # v6: agreement intensity per node
├── run_experiment_nca.py    # Fixed vs NCA v1-v4 runner
├── run_all_combinations.py  # v5: all 56 model combinations
├── run_v6_sampling.py       # v6: random sampling runner
├── bias_profiler.py         # Single-model bias profiling
├── ideas/                   # Research idea memos
├── reports/                 # Experiment reports
│   ├── v5_report.md
│   └── v6_report.md
└── results/
    ├── fixed_results.jsonl
    ├── nca_results.jsonl        # v1
    ├── nca_v2_results.jsonl
    ├── nca_v3_results.jsonl
    ├── nca_v4_results.jsonl
    ├── v5/                      # All 56 combination results
    └── v6/                      # 100 random sampling results
```

---

## Baseline

The fixed network baseline is taken directly from [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — a prior experiment on adaptive vs. fixed LLM topologies (p=0.0007, d=4.29).

---

## Related

- [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — Adaptive Artificial Synapse (AAS) experiment
- [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) — Original NCA paper
