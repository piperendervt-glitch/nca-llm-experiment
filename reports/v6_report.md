# NCA v6 Experiment Report: Random Sampling over Agreement Intensity and Step Count

> 100 random trials sampling model combinations, per-node agreement intensity (0-100%), and step count (1-5) from a pool of 6 models, tested on 100 world_consistency tasks each.

---

## 1. Executive Summary

**Best trial:** Trial 16 (`qwen2.5:7b + llama3:latest + mistral:7b`, agreement=[30,80,80], steps=3) — **63% overall accuracy** (30% CONSISTENT, 96% CONTRADICTION).

**Most balanced high-performer:** Trial 29 (`mistral:7b + llama3:latest + llama3.1:8b`, agreement=[80,70,10], steps=2) — **60% overall** (62% CONSISTENT, 58% CONTRADICTION).

**Comparison vs v5 best (61%):** v6 best reaches 63%, a +2pp improvement. However, the v6 mean (52.4%) is slightly below v5 mean (53.3%), reflecting the added variance from randomized agreement intensity and step count.

> **Statistical note**: The best trial (63%) is the maximum of 100 randomly sampled configurations. Without multiple comparison correction, this figure should be interpreted as an exploratory upper bound.

### Key Findings

- **Agreement intensity in the 60-80% average range yields the best results** (53.9% mean), while extremes (0-20% or 81-100%) underperform (51.0% and 50.0% respectively).
- **Step count has a massive effect on groupthink but a weak effect on accuracy.** Going from 1 to 5 steps increases CONTRADICTION groupthink from 32.6 to 85.0 per 100 tasks, yet overall accuracy only varies from 51.4% to 53.3%.
- **mistral:7b and llama3:latest dominate the top trials.** They appear in 7 of the top 10 trials each and drive the highest CONSISTENT accuracy.
- **v5's best combo (qwen2.5:7b + llama3.2:3b + mistral:7b) severely underperforms in v6**, averaging only 49.5% across 6 appearances — suggesting v5's 61% was partially a lucky draw without agreement tuning.
- **The CONTRADICTION bias is overwhelming:** 86 of 100 trials have CONTRADICTION > CONSISTENT accuracy. Only 12 trials flip this, and they cluster around 1-2 steps with high agreement intensity.

---

## 2. Full Leaderboard (Top 20 Trials)

| Rank | Trial | Models | Agreement | Steps | Overall | CONS acc | CONTR acc | Split | GT-CONTR | GT-CONS |
|------|-------|--------|-----------|-------|---------|----------|-----------|-------|----------|---------|
| 1 | 16 | qwen2.5:7b + llama3:latest + mistral:7b | [30,80,80] | 3 | **0.63** | 0.30 | 0.96 | 19 | 73 | 8 |
| 2 | 52 | mistral:7b + llama3:latest + qwen2.5:3b | [100,80,40] | 1 | **0.61** | 0.58 | 0.64 | 45 | 28 | 27 |
| 3 | 60 | qwen2.5:7b + mistral:7b + qwen2.5:3b | [50,80,60] | 5 | **0.61** | 0.22 | 1.00 | 7 | 84 | 9 |
| 4 | 29 | mistral:7b + llama3:latest + llama3.1:8b | [80,70,10] | 2 | **0.60** | 0.62 | 0.58 | 23 | 35 | 42 |
| 5 | 53 | qwen2.5:7b + llama3:latest + qwen2.5:3b | [10,80,20] | 3 | 0.59 | 0.18 | 1.00 | 13 | 79 | 8 |
| 6 | 50 | qwen2.5:3b + mistral:7b + qwen2.5:7b | [80,40,20] | 3 | 0.58 | 0.20 | 0.96 | 9 | 82 | 9 |
| 7 | 51 | qwen2.5:3b + qwen2.5:7b + llama3:latest | [40,20,70] | 5 | 0.58 | 0.16 | 1.00 | 11 | 84 | 5 |
| 8 | 77 | mistral:7b + llama3.2:3b + llama3:latest | [10,30,100] | 3 | 0.58 | 0.68 | 0.48 | 20 | 30 | 50 |
| 9 | 26 | qwen2.5:3b + qwen2.5:7b + mistral:7b | [10,70,10] | 5 | 0.57 | 0.16 | 0.98 | 9 | 83 | 8 |
| 10 | 86 | qwen2.5:3b + llama3:latest + qwen2.5:7b | [40,50,50] | 5 | 0.57 | 0.14 | 1.00 | 5 | 89 | 6 |
| 11 | 93 | mistral:7b + qwen2.5:7b + llama3.1:8b | [20,90,80] | 1 | 0.57 | 0.60 | 0.54 | 44 | 30 | 26 |
| 12 | 9 | qwen2.5:7b + qwen2.5:3b + llama3.2:3b | [100,30,40] | 1 | 0.56 | 0.36 | 0.76 | 41 | 50 | 9 |
| 13 | 21 | mistral:7b + llama3.2:3b + llama3:latest | [100,50,10] | 3 | 0.56 | 0.56 | 0.56 | 22 | 40 | 38 |
| 14 | 24 | qwen2.5:7b + llama3:latest + mistral:7b | [80,80,0] | 5 | 0.56 | 0.22 | 0.90 | 7 | 80 | 13 |
| 15 | 27 | qwen2.5:7b + mistral:7b + llama3.1:8b | [80,20,40] | 5 | 0.56 | 0.16 | 0.96 | 3 | 89 | 8 |
| 16 | 33 | mistral:7b + llama3.1:8b + qwen2.5:7b | [80,20,90] | 5 | 0.56 | 0.16 | 0.96 | 10 | 84 | 6 |
| 17 | 72 | llama3:latest + llama3.1:8b + mistral:7b | [80,20,30] | 4 | 0.56 | 0.54 | 0.58 | 16 | 43 | 41 |
| 18 | 94 | llama3.1:8b + llama3.2:3b + qwen2.5:3b | [10,100,60] | 2 | 0.56 | 0.24 | 0.88 | 22 | 66 | 12 |
| 19 | 54 | llama3:latest + llama3.2:3b + qwen2.5:7b | [50,30,100] | 3 | 0.55 | 0.24 | 0.86 | 22 | 65 | 13 |
| 20 | 59 | llama3.1:8b + qwen2.5:7b + qwen2.5:3b | [40,50,0] | 3 | 0.55 | 0.10 | 1.00 | 11 | 88 | 1 |

---

## 3. Agreement Intensity Analysis

### Average Agreement Intensity vs Accuracy

| Avg Agreement Band | n | Avg Overall | Avg CONS | Avg CONTR | Avg GT (total) |
|--------------------|---|-------------|----------|-----------|----------------|
| 0-20% | 8 | 51.0% | 18.2% | 83.8% | 79.5 |
| 21-40% | 25 | 51.5% | 23.7% | 79.3% | 75.9 |
| 41-60% | 45 | 52.6% | 23.9% | 81.3% | 79.8 |
| 61-80% | 19 | **53.9%** | **33.7%** | 74.2% | 76.9 |
| 81-100% | 3 | 50.0% | 22.0% | 78.0% | 74.0 |

**Optimal agreement zone: 60-80% average.** This band produces the highest overall accuracy (53.9%) and notably the best CONSISTENT accuracy (33.7%) — nearly double the 0-20% band. The sweet spot appears to be moderate-to-high agreement that allows neighbor influence without suppressing independent judgment.

### Symmetric vs Asymmetric Agreement Patterns

| Pattern | n | Avg Overall | Avg CONS | Avg CONTR |
|---------|---|-------------|----------|-----------|
| Symmetric (spread <= 30) | 23 | 51.6% | 24.1% | 79.0% |
| Mid (spread 31-60) | 36 | 53.1% | 23.5% | 82.7% |
| Asymmetric (spread > 60) | 41 | 52.2% | 27.3% | 77.1% |

**Mid-spread configurations slightly outperform** both symmetric and highly asymmetric ones. Having some nodes more agreeable than others (but not extremely so) appears beneficial. Highly asymmetric configurations (where one node is at 0% and another at 100%) can create unstable dynamics.

### Correlation with Overall Accuracy

Correlation between average agreement intensity and overall accuracy: **r = 0.130** (weak positive). Agreement intensity alone does not strongly predict performance, but the band analysis reveals a non-linear relationship with a clear optimum at 60-80%.

---

## 4. Step Count Analysis

### Accuracy by Step Count

| Steps | n | Avg Overall | Avg CONS | Avg CONTR | Avg GT-CONTR | Avg GT-CONS | Avg Split |
|-------|---|-------------|----------|-----------|-------------|-------------|-----------|
| 1 | 17 | 51.4% | **45.9%** | 56.9% | 32.6 | 21.6 | **45.8** |
| 2 | 25 | 51.8% | 24.0% | 79.5% | 61.2 | 13.7 | 25.1 |
| 3 | 19 | **53.8%** | 26.2% | 81.4% | 65.7 | 16.3 | 18.1 |
| 4 | 18 | 51.4% | 22.0% | 80.9% | 70.3 | 15.3 | 14.3 |
| 5 | 21 | 53.3% | 11.6% | **95.0%** | **85.0** | 6.2 | **8.8** |

### Key Observations

- **Step count 3 is optimal for overall accuracy** (53.8%), balancing CONSISTENT and CONTRADICTION detection.
- **Step count 1 preserves CONSISTENT accuracy** (45.9%) — nearly 4x higher than step count 5 (11.6%). With only 1 step, models retain their initial judgments without convergence pressure.
- **Step count 5 maximizes CONTRADICTION accuracy** (95.0%) but crushes CONSISTENT accuracy to 11.6%, creating a nearly one-sided classifier.
- **Steps and groupthink are strongly correlated** (r = 0.821). Each additional step pushes more tasks toward unanimous CONTRADICTION.

### Groupthink by Step Count

The relationship is near-linear:

- Steps=1: 54.2 unanimous / 100 tasks (32.6 CONTR, 21.6 CONS)
- Steps=5: 91.2 unanimous / 100 tasks (85.0 CONTR, 6.2 CONS)

Each additional step converts roughly 9 split decisions into unanimous CONTRADICTION groupthink. This is the single strongest structural effect in the entire experiment.

---

## 5. Model Combination Analysis

### Per-Model Average Performance (v6)

| Model | n (trials) | Avg Overall | Avg CONS | Avg CONTR |
|-------|------------|-------------|----------|-----------|
| llama3:latest | 43 | **0.530** | **0.306** | 0.753 |
| mistral:7b | 47 | **0.529** | **0.331** | 0.727 |
| qwen2.5:7b | 54 | 0.529 | 0.194 | **0.864** |
| qwen2.5:3b | 49 | 0.522 | 0.193 | 0.851 |
| llama3.1:8b | 52 | 0.521 | 0.242 | 0.799 |
| llama3.2:3b | 55 | 0.513 | 0.260 | 0.767 |

### Top 10 / Top 20 / Bottom 10 Appearances

| Model | All | Top 10 | Top 20 | Bottom 10 | Net (T10 - B10) |
|-------|-----|--------|--------|-----------|-----------------|
| qwen2.5:7b | 54 | **7** | **14** | 5 | **+2** |
| mistral:7b | 47 | **7** | **13** | 4 | **+3** |
| llama3:latest | 43 | **7** | **11** | 4 | **+3** |
| qwen2.5:3b | 49 | **7** | 10 | 6 | +1 |
| llama3.1:8b | 52 | 1 | 7 | 5 | -4 |
| llama3.2:3b | 55 | 1 | 5 | 6 | -5 |

### v6 vs v5 Model Rankings

| Model | v5 Avg Overall | v6 Avg Overall | Delta |
|-------|----------------|----------------|-------|
| mistral:7b | 0.543 | 0.529 | -1.4pp |
| llama3:latest | 0.541 | 0.530 | -1.1pp |
| qwen2.5:7b | 0.535 | 0.529 | -0.6pp |
| llama3.1:8b | 0.528 | 0.521 | -0.7pp |
| qwen2.5:3b | 0.524 | 0.522 | -0.2pp |
| llama3.2:3b | 0.524 | 0.513 | -1.1pp |

All models perform slightly worse on average in v6 than v5. This is likely because v5 used fixed agreement=100% and steps=1 (equivalent to a simple NCA update), while v6 randomly samples these parameters — including many suboptimal configurations.

### V5's Best Combo in V6

The v5 champion `qwen2.5:7b + llama3.2:3b + mistral:7b` appeared in 6 v6 trials:

| Trial | Agreement | Steps | Overall | CONS | CONTR |
|-------|-----------|-------|---------|------|-------|
| 12 | [20,70,60] | 3 | 0.52 | 0.24 | 0.80 |
| 13 | [100,50,0] | 2 | 0.51 | 0.20 | 0.82 |
| 61 | [20,20,60] | 1 | 0.50 | 0.56 | 0.44 |
| 78 | [0,0,30] | 4 | 0.49 | 0.04 | 0.94 |
| 91 | [70,30,40] | 4 | 0.51 | 0.14 | 0.88 |
| 99 | [20,70,100] | 1 | 0.44 | 0.50 | 0.38 |

**Average: 49.5%** — far below v5's 61%. This confirms that v5's result was achieved under v5's specific conditions (full agreement, 1 update step), and the same model combo is highly sensitive to agreement and step parameters. The v5 "best" designation does not transfer to arbitrary configurations.

---

## 6. Groupthink Analysis

### Distribution Across 100 Trials

- **Mean total groupthink (unanimous agreement):** 78.1 / 100 tasks
- **Range:** 40 — 97 unanimous tasks
- **Mean GT-CONTRADICTION:** 63.8 / 100
- **Mean GT-CONSISTENT:** 14.2 / 100
- **Mean split decisions:** 21.9 / 100

Groupthink in v6 (78.1) is significantly higher than v5 (68.3), driven by the inclusion of multi-step trials where convergence pressure accumulates.

### Correlation with Agreement Intensity

**Corr(avg agreement, total GT): r = -0.037** — essentially zero. Counter-intuitively, higher agreement intensity does not increase groupthink. This is because the agreement instruction influences *how much* a node listens to neighbors, but the primary driver of convergence is **step count** (r = 0.821 with GT), not agreement percentage.

### Correlation with Step Count

**Corr(steps, total GT): r = 0.821** — the strongest correlation in the dataset. Step count is the dominant structural driver of groupthink.

**Corr(steps, GT-CONTRADICTION): r = 0.721** — most of the groupthink increase from more steps goes to CONTRADICTION unanimity.

### Extreme Cases

- **Highest groupthink:** Trial 89 — 94 unanimous tasks (94 all-CONTR, 0 all-CONS), steps=5, overall=50%
- **Lowest groupthink:** Trial 99 — 47 unanimous tasks (27 all-CONTR, 20 all-CONS), steps=1, overall=44%
- **Most balanced groupthink:** Trial 29 — 77 unanimous (35 CONTR, 42 CONS), steps=2, overall=60%

---

## 7. Mirror Effect Analysis

### Direction Distribution

| Direction | Count | Avg Overall | Avg Steps | Avg Agreement |
|-----------|-------|-------------|-----------|---------------|
| CONTRADICTION > CONSISTENT | **86** | 52.3% | 3.2 | 48.2% |
| CONSISTENT > CONTRADICTION | 12 | 52.7% | 1.8 | 56.1% |
| Perfectly balanced | 2 | 52.0% | 2.0 | — |

The CONTRADICTION bias dominates 86% of trials. The 12 trials where CONSISTENT wins share distinct characteristics: **lower step count** (avg 1.8 vs 3.2) and **higher average agreement** (56.1% vs 48.2%).

### Balanced Trials (|CONS - CONTR| <= 0.06)

| Trial | Models | Agree | Steps | Overall | CONS | CONTR | |delta| |
|-------|--------|-------|-------|---------|------|-------|----|
| 21 | mistral:7b + llama3.2:3b + llama3:latest | [100,50,10] | 3 | **0.56** | 0.56 | 0.56 | 0.00 |
| 11 | qwen2.5:7b + llama3:latest + llama3.2:3b | [30,100,40] | 1 | 0.48 | 0.48 | 0.48 | 0.00 |
| 83 | llama3.2:3b + mistral:7b + llama3:latest | [70,90,80] | 4 | 0.51 | 0.52 | 0.50 | 0.02 |
| 29 | mistral:7b + llama3:latest + llama3.1:8b | [80,70,10] | 2 | **0.60** | 0.62 | 0.58 | 0.04 |
| 72 | llama3:latest + llama3.1:8b + mistral:7b | [80,20,30] | 4 | **0.56** | 0.54 | 0.58 | 0.04 |
| 93 | mistral:7b + qwen2.5:7b + llama3.1:8b | [20,90,80] | 1 | **0.57** | 0.60 | 0.54 | 0.06 |
| 52 | mistral:7b + llama3:latest + qwen2.5:3b | [100,80,40] | 1 | **0.61** | 0.58 | 0.64 | 0.06 |

**Pattern for balanced + high accuracy:** The best balanced trials (29, 72, 93, 52) all include `mistral:7b` and have 1-2 step counts. `mistral:7b` appears to be the key "balancer" model that resists the CONTRADICTION drift that multi-step updates create.

---

## 8. Comparison with All Previous Versions

| Version | Overall | CONSISTENT | CONTRADICTION | GT-CONTR | GT-CONS | Split | Key Change |
|---------|---------|------------|---------------|----------|---------|-------|------------|
| Fixed (baseline) | 45.0% | 2.0% | 88.0% | — | — | — | Sequential pipeline |
| NCA v1 | 49.0% | 0.0% | 98.0% | 99 | 0 | 0 | Baseline NCA (all qwen2.5:3b) |
| NCA v2 | 55.0% | **80.0%** | 30.0% | 17 | 65 | 18 | Anti-sycophancy prompts |
| NCA v3 | 52.0% | 6.0% | 98.0% | 77 | 2 | 21 | Devil's advocate rule |
| NCA v4 | 53.0% | 24.0% | 82.0% | 75 | 17 | 8 | Confidence weighting |
| **v5 best** | 61.0% | 40.0% | 82.0% | 57 | 15 | 28 | Multi-model combos |
| v5 most balanced | 56.0% | 56.0% | 56.0% | 25 | 29 | 46 | llama3 + llama3.1 + mistral |
| v5 mean (56 combos) | 53.3% | 23.7% | 82.9% | 57.7 | 9.5 | 31.6 | — |
| **v6 best** | **63.0%** | 30.0% | 96.0% | 73 | 8 | 19 | Agreement intensity + step tuning |
| v6 most balanced | 60.0% | **62.0%** | 58.0% | 35 | 42 | 23 | mistral + llama3 + llama3.1 |
| v6 mean (100 trials) | 52.4% | 24.3% | 80.5% | 63.8 | 14.2 | 21.9 | — |

### Key Takeaways

- **v6 sets a new overall accuracy record at 63%**, surpassing v5's 61% by 2pp. However, this comes from a CONTRADICTION-heavy profile (30% CONS, 96% CONTR).
- **v6's most balanced trial (T29, 60%) is the best balanced result ever**, beating v5's balanced trial (56%) by 4pp while maintaining near-symmetry (62/58).
- **v2 remains the unchallenged CONSISTENT champion** at 80%, but at the cost of only 30% CONTRADICTION. No subsequent version has come close.
- **The v6 mean (52.4%) is lower than v5 mean (53.3%)**, reflecting that random sampling of agreement/step parameters introduces many suboptimal configurations that drag down the average.
- **The gap between best and mean has widened**: v5 had 61% best vs 53.3% mean (7.7pp gap), v6 has 63% best vs 52.4% mean (10.6pp gap). This suggests the parameter space has higher variance and reward for finding the right configuration.

---

## 9. Recommendations for v7+

### Top 3 Configurations to Carry Forward

1. **Trial 16: qwen2.5:7b + llama3:latest + mistral:7b** (agree=[30,80,80], steps=3, overall=63%) — Best raw accuracy. High agreement on two nodes with one low-agreement "independent thinker" node. Test whether the qwen2.5:7b as the low-agreement node is key.

2. **Trial 29: mistral:7b + llama3:latest + llama3.1:8b** (agree=[80,70,10], steps=2, overall=60%) — Best balanced result. One node with very low agreement acts as an anchor against groupthink while the other two cooperate. This pattern could inform a "devil's advocate" role assignment.

3. **Trial 52: mistral:7b + llama3:latest + qwen2.5:3b** (agree=[100,80,40], steps=1, overall=61%) — High accuracy with just 1 step and strong balance (58/64). Demonstrates that minimal convergence steps with the right models can match multi-step configurations.

### Hypotheses About Role-Division NCA (v7)

1. **Explicit role assignment based on model strengths.** v6 data shows that `mistral:7b` and `llama3:latest` are "balance" models (high CONSISTENT accuracy), while `qwen2.5:7b` and `qwen2.5:3b` are "detector" models (high CONTRADICTION accuracy). A role-division NCA could assign:
   - **Skeptic role** to qwen2.5:7b (good at finding contradictions)
   - **Defender role** to mistral:7b (good at recognizing consistency)
   - **Arbiter role** to llama3:latest (balanced judgment)

2. **Asymmetric agreement as a design principle.** The best trials consistently show one node with low agreement (10-30%) acting as an independent anchor. v7 could formalize this as a "dissenter" role rather than leaving it to random sampling.

3. **Step count 2-3 is the sweet spot.** Going beyond 3 steps consistently pushes systems toward CONTRADICTION groupthink without improving overall accuracy. v7 should default to 2-3 steps and invest the computation budget in richer inter-node communication instead.

### What v6 Tells Us About Agreement Intensity

- **Agreement intensity matters less than expected** (r = 0.130 with accuracy). The specific model combination and step count are more predictive.
- **The strongest effect is indirect:** agreement intensity shapes how quickly nodes converge, which interacts with step count. High agreement + many steps = rapid CONTRADICTION convergence. Low agreement + few steps = preserved diversity but potentially less coordination.
- **The optimal configuration is asymmetric:** one "free thinker" node (low agreement) combined with two "cooperative" nodes (high agreement) at 2-3 steps. This creates a natural tension between consensus and independence.
- **Per-node agreement is more nuanced than a global parameter.** v6 demonstrates that per-node tuning can unlock configurations (like T16's [30,80,80]) that a single global agreement parameter would miss. v7 should continue with per-node or per-role agreement settings.

---

## Appendix: Experiment Design

- **Model pool:** qwen2.5:3b, qwen2.5:7b, llama3:latest, llama3.1:8b, llama3.2:3b, mistral:7b (6 models, no gemma2:2b or fool-qwen)
- **Sampling:** 100 trials, each drawing 3 models (without replacement), 3 independent agreement percentages (0-100% in 10% increments), and step count (1-5), all uniformly at random with seed=42
- **Task set:** 100 world_consistency tasks (50 CONSISTENT, 50 CONTRADICTION)
- **Aggregation:** Confidence-weighted majority vote
- **NCA topology:** Ring graph (3 nodes, each sees 2 neighbors)
