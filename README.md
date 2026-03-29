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
| **NCA v2** | **55.0%** | **80.0%** | 30.0% | **+10.0%** | Anti-sycophancy prompt — best overall, but overcorrected |
| NCA v3 | 52.0% | 6.0% | 98.0% | +7.0% | Devil's advocate rule — CONTRADICTION bias persisted |
| NCA v4 | 53.0% | 24.0% | 82.0% | +8.0% | Confidence-weighted updates — best balance between both |

> **Note on v5 results**: The best combination (61.0%, qwen2.5:7b + llama3.2:3b + mistral:7b)
> was selected post-hoc from 56 unique combinations. This constitutes a multiple comparison
> without correction. The result should be interpreted as the upper bound of performance
> under heterogeneous model selection, not as a statistically validated single hypothesis.
> The v5 mean accuracy across all 56 combinations was 53.3%.

### Groupthink Statistics

| Version | All CONTRADICTION | All CONSISTENT | Split |
|---------|:-----------------:|:--------------:|:-----:|
| NCA v1 | 99 | 0 | 0 |
| NCA v2 | 17 | 65 | 18 |
| NCA v3 | 77 | 2 | 21 |
| NCA v4 | 75 | 17 | 8 |

### Key Findings

**Groupthink is real and severe.**
In v1, 99 out of 100 tasks had all 3 nodes unanimously converge to CONTRADICTION — regardless of the correct answer. Local neighbor influence amplified the initial bias instead of correcting it.

**Anti-sycophancy prompts work, but overshoot.**
v2 introduced a rule forcing nodes to reconsider when all neighbors agreed. CONSISTENT accuracy jumped from 0% → 80%, but CONTRADICTION accuracy collapsed from 98% → 30%.

**Devil's advocate (v3) wasn't strong enough.**
The prompt-level intervention couldn't override qwen2.5:3b's inherent CONTRADICTION bias. 77/100 tasks still converged unanimously to CONTRADICTION.

**Confidence weighting (v4) is the best balance.**
By downweighting uncertain neighbors, v4 achieved 24% CONSISTENT and 82% CONTRADICTION — the most balanced result, with only 8 split decisions.

**Root cause: model-level bias amplified by NCA propagation.**
qwen2.5:3b has a strong tendency toward CONTRADICTION. NCA's local update steps propagate and reinforce this bias through neighbor influence, making it harder to overcome than in a fixed pipeline.

```
v1: [CONTRADICTION, CONTRADICTION, CONTRADICTION] → 99% of the time (groupthink)
v2: [CONSISTENT,    CONSISTENT,    CONSISTENT   ] → overcorrected
v3: [CONTRADICTION, CONTRADICTION, CONTRADICTION] → devil's advocate too weak
v4:  more balanced, but CONTRADICTION bias still dominates
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
├── nca_network.py          # NCA network (latest: v4)
├── nca_network_v1.py       # v1: baseline NCA
├── nca_network_v2.py       # v2: anti-sycophancy prompts
├── nca_network_v3.py       # v3: devil's advocate rule
├── run_experiment_nca.py   # Comparison experiment runner
├── results/
│   ├── fixed_results.jsonl      # Baseline results
│   ├── nca_results.jsonl        # NCA v1 results
│   ├── nca_v2_results.jsonl     # NCA v2 results
│   ├── nca_v3_results.jsonl     # NCA v3 results
│   └── nca_v4_results.jsonl     # NCA v4 results
└── requirements.txt
```

---

## Baseline

The fixed network baseline is taken directly from [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — a prior experiment on adaptive vs. fixed LLM topologies (p=0.0007, d=4.29).

---

## Related Work

### Direct comparisons

- **Multi-Agent Debate (MAD)** — Du et al. (2023) [arXiv:2305.14325](https://arxiv.org/abs/2305.14325).
  Multiple LLM instances propose and debate responses over multiple rounds.
  Key difference: MAD uses fully-connected topology; this work uses a fixed ring with
  synchronous NCA-style updates. MAD focuses on accuracy improvement; this work
  additionally studies bias propagation and groupthink structure.

- **Encouraging Divergent Thinking via MAD** — Liang et al. (2024) [EMNLP 2024](https://aclanthology.org/2024.emnlp-main.992/).
  Introduces the Degeneration-of-Thought (DoT) problem and tit-for-tat dynamics.
  The groupthink observed in v1 (99/100 tasks converging to CONTRADICTION) is a
  direct instance of DoT in a ring topology.

- **Mixture of Agents (MoA)** — Wang et al. (2024) [arXiv:2406.04692](https://arxiv.org/abs/2406.04692).
  Heterogeneous LLM agents in a layered, fully-broadcast architecture.
  Key difference: MoA uses hierarchical layers with full broadcast; this work uses
  a flat ring with local-only neighbor communication. v5's heterogeneous model
  combinations are directly comparable to MoA's diversity findings.

- **Should we be going MAD?** — Smit et al. (2024) [ICML 2024](https://proceedings.mlr.press/v235/smit24a.html).
  Benchmarks MAD strategies and finds that agreement intensity is a critical
  hyperparameter. v6 of this work directly tests agreement intensity via random
  sampling, providing small-model (3b-8b) evidence for Smit et al.'s findings.

### Related architectures

- **Reflexion** — Shinn et al. (2023) [arXiv:2303.11366](https://arxiv.org/abs/2303.11366).
  LLM agents with dynamic memory and self-reflection. The proposed aas-v2
  (past-log-aware AAS) shares the core insight of using historical performance
  to inform future decisions.

- **Growing Neural Cellular Automata** — Mordvintsev et al. (2020) [Distill](https://distill.pub/2020/growing-ca/).
  The conceptual inspiration for applying local update rules to node networks.
  Note: this work is NCA-*inspired*, not a direct implementation — LLM outputs
  are discrete text, weights are not shared, and topology is fixed rather than emergent.

- **CAMEL** — Li et al. (2023) [arXiv:2303.17760](https://arxiv.org/abs/2303.17760).
  Communicative agents for LLM society exploration. General multi-agent framework;
  this work differs in its focus on fixed-topology synchronous update rules.

### Bias and groupthink in LLMs

- **Contrastive Chain-of-Thought** — Related to the systematic CONTRADICTION bias
  observed across v1-v6. The mirror effect (NCA → 82% CONTRADICTION vs
  Self-Consistency → 82% CONSISTENT with identical models) suggests that
  aggregation mechanism, not model priors alone, drives output distribution.
