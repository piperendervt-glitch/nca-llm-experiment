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

### `world_consistency` (v1–v6, v8–v9)
Given a world rule and a statement, detect whether the statement contradicts the rule.
- 100 tasks total (50 consistent, 50 contradictory)
- Labels: `CONSISTENT` / `CONTRADICTION`

### `math` (v7–v9)
Elementary to high school math verification tasks.
- Labels: `CORRECT` / `INCORRECT`
- v7: 100 elementary tasks (calculation, logic, word problems, sequences)
- v7.5: 75 middle school tasks (grade 7 / 8 / 9, 25 each)
- v7.6: 75 high school tasks (grade 10 / 11 / 12, 25 each)
- v8: 350 tasks (all of the above) with adaptive model selection
- v9: 350 tasks (all of the above) with aggregation modifications

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

### aggregation modification series (v9)

| Experiment | Method | Overall | Outcomes Changed | Net Impact | Verdict |
|------------|--------|---------|-----------------|------------|---------|
| v9a | MetaAgent on splits | 74.9% | 61 | -1 task | Harmful |
| v9b | Dynamic confidence weighting | 79.1% | 0 | 0 | Equivalent to majority |
| v9c | AntiNode (weight=0.5) | 74.3% | 0 | 0 | Structurally impossible |
| v9d | Veto + Level-K selection | 76.0% | 0 | 0 | Diagnostic value only |

**1,400 total tasks across v9 series. Aggregation hypothesis fully falsified.**

---

## Key Findings

**Groupthink is real and severe, but model diversity helps.**
v1 had 99/100 tasks converge to CONTRADICTION. Heterogeneous models (v5) reduced this and raised accuracy to 61%.

**The mirror effect: NCA and Self-Consistency have opposite biases.**
Same 3 models: NCA → 82% CONTRADICTION, Self-Consistency → 82% CONSISTENT. The NCA update process itself generates bias.

**Step count is the dominant structural variable (r=0.821 with groupthink).**
Each additional step converts ~9 split decisions into CONTRADICTION unanimity. Steps=3 is optimal.

**Role rotation is a de-biasing mechanism.**
Rotating roles boost CORRECT accuracy by +14–19pp. Logic tasks benefit most: fixed 72% → rotating 100%. Valid range: up to middle school difficulty.

**Operation type, not grade level, determines LLM difficulty.**
Pattern-match (80-100%) > formula+verify (60-80%) > multi-step procedure (40-60%) > symbolic manipulation (20-40%).

**The difficulty wall is at middle school, not high school.**
best_fixed: 83% → 72% → 77%. High school trig/logs are easier than middle school simultaneous equations due to training data coverage.

**Hard task ceiling at 65% across all domains.**
unanimous (84%) vs split (57%) — a 27pp gap driven by model capability, not architecture.

**Aggregation cannot break the 65% ceiling.**
Split decisions = all models uncertain = no aggregation strategy can create certainty that doesn't exist. Proven across 1,400 tasks (v9a–v9d).

**Level-K uncertainty flags: a diagnostic signal for task difficulty.**
Flag accuracy gradient: world_consistency 100% → math_elementary 82% → math_middle 59% → math_high 55%. Models know when they don't know — and this signal varies systematically by domain.

**The capability hierarchy (confirmed):**
Role specialization (v7) +20pp > Difficulty routing (v8) +2pp > Aggregation modification (v9) +0pp.

```
v1: groupthink → 99/100 CONTRADICTION (same-model NCA)
v5: heterogeneous models → 61% (diversity breaks groupthink)
v6: agreement tuning → 63%, steps=3 optimal (r=0.821)
v7: role-division → 83% on math, rotation eliminates logic bias
v7→v7.6: difficulty wall at middle school, operation type determines accuracy
v8: adaptive routing → 77% overall (+2pp), 65% hard ceiling identified
v9: aggregation hypothesis falsified across 1,400 tasks, Level-K flags discovered
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

# v9a–v9d: aggregation modification experiments
python run_v9a.py  # MetaAgent
python run_v9b.py  # Dynamic confidence weighting
python run_v9c.py  # Antithesis agent
python run_v9d.py  # Game-theory veto + Level-K
```

---

## File Structure

```
nca-llm-experiment/
├── nca_network.py                    # NCA network (v1 baseline)
├── nca_network_v6.py                 # v6: agreement intensity per node
├── nca_network_v7.py                 # v7: role-division NCA
├── nca_network_v8.py                 # v8: adaptive routing wrapper
├── nca_network_v9a.py                # v9a: MetaAgent
├── nca_network_v9b.py                # v9b: dynamic confidence weighting
├── nca_network_v9c.py                # v9c: antithesis agent
├── nca_network_v9d.py                # v9d: game-theory veto + Level-K
├── run_experiment_nca.py             # Fixed vs NCA v1-v4 runner
├── run_all_combinations.py           # v5: all 56 model combinations
├── run_v6_sampling.py                # v6: random sampling runner
├── run_v7.py                         # v7: role-division runner
├── run_v7_5.py                       # v7.5: middle school tasks runner
├── run_v7_6.py                       # v7.6: high school tasks runner
├── run_v8.py                         # v8: adaptive model selection runner
├── run_v9a.py / run_v9b.py / run_v9c.py / run_v9d.py
├── embedding_classifier.py           # v8: difficulty classifier
├── math_task_generator.py            # v7: elementary math tasks
├── middle_school_task_generator.py   # v7.5: middle school math tasks
├── high_school_task_generator.py     # v7.6: high school math tasks
├── ideas/                            # Research idea memos
├── reports/                          # Experiment reports (v5–v9d + v9 summary)
└── results/
    ├── v5/ v6/ v7/ v7_5/ v7_6/      # Difficulty series results
    ├── v8/                           # Adaptive model selection results
    └── v9a/ v9b/ v9c/ v9d/          # Aggregation modification results
```

---

## Baseline

The fixed network baseline is taken directly from [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — a prior experiment on adaptive vs. fixed LLM topologies (p=0.0007, d=4.29).

---

## Related

- [sdnd-proof](https://github.com/piperendervt-glitch/sdnd-proof) — Adaptive Artificial Synapse (AAS) experiment
- [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) — Original NCA paper
- [AutoHarness](https://arxiv.org/abs/2603.03329) — Lou et al. (2026), harness engineering for LLM agents
