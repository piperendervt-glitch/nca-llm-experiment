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

| Version | Overall Acc | CONSISTENT Acc | CONTRADICTION Acc | Notes |
|---------|------------|----------------|-------------------|-------|
| Fixed Network (baseline) | 45.0% | 2.0% | 88.0% | Sequential Node1→2→3 pipeline |
| NCA v1 | 49.0% | 0.0% | 98.0% | **Groupthink**: 99/100 tasks converged to CONTRADICTION |
| NCA v2 | 55.0% | 80.0% | 30.0% | Anti-sycophancy prompt broke bias but overcorrected |
| NCA v3 | 🔄 running | — | — | Devil's advocate rule to balance both directions |
| NCA v4 | 🔄 pending | — | — | Confidence-weighted neighbor influence |

### Key Findings (v1 vs v2)

**Groupthink is real and severe.**
In v1, 99 out of 100 tasks had all 3 nodes unanimously converge to CONTRADICTION — regardless of the correct answer. Local neighbor influence amplified the initial bias instead of correcting it.

**Anti-sycophancy prompts work, but overshoot.**
v2 introduced a rule forcing nodes to reconsider when all neighbors agreed. CONSISTENT accuracy jumped from 0% → 80%, but CONTRADICTION accuracy collapsed from 98% → 30%. The pendulum swung the other way.

```
v1: [CONTRADICTION, CONTRADICTION, CONTRADICTION] → 99% of the time
v2: [CONSISTENT,    CONSISTENT,    CONSISTENT   ] → overcorrected
v3: targeting balanced convergence
```

---

## Setup

### Requirements

- [Ollama](https://ollama.com/) running locally with `qwen2.5:3b`
- Python 3.10+

```bash
ollama pull qwen2.5:3b
pip install httpx scipy
```

### Run

```bash
# Single NCA network test (3 tasks)
python nca_network.py

# Full comparison experiment (Fixed vs NCA, 100 tasks each)
python run_experiment_nca.py
```

---

## File Structure

```
nca-llm-experiment/
├── nca_network.py          # NCA network (current version)
├── nca_network_v1.py       # v1: baseline NCA
├── nca_network_v2.py       # v2: anti-sycophancy prompts
├── run_experiment_nca.py   # Comparison experiment runner
├── results/
│   ├── fixed_results.jsonl     # Baseline results
│   ├── nca_results.jsonl       # NCA v1 results
│   ├── nca_v2_results.jsonl    # NCA v2 results
│   ├── nca_v3_results.jsonl    # NCA v3 results (in progress)
│   └── nca_v4_results.jsonl    # NCA v4 results (pending)
└── requirements.txt
```

---

## Baseline

The fixed network baseline is taken directly from [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — a prior experiment on adaptive vs. fixed LLM topologies (p=0.0007, d=4.29).

---

## Related

- [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — Adaptive Artificial Synapse (AAS) experiment
- [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) — Original NCA paper
