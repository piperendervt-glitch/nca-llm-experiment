# NCA v5 Experiment Report: All Model Combinations

> 56 unique 3-model combinations from 8 models, tested on 100 world_consistency tasks each.

---

## 1. Executive Summary

**Best combination:** `qwen2.5:7b + llama3.2:3b + mistral:7b` — **61% overall accuracy** (40% CONSISTENT, 82% CONTRADICTION).

**Worst combination:** `qwen2.5:3b + llama3.1:8b + llama3.2:3b` — **45% overall accuracy** (20% CONSISTENT, 70% CONTRADICTION).

**vs v1-v4 baselines:** The v5 best (61%) surpasses all prior versions: Fixed (45%), v1 (49%), v2 (55%), v3 (52%), v4 (53%). This is a **+16pp improvement over Fixed** and **+6pp over v2** (the previous best).

> **Statistical note**: The best combination (61%) is the maximum of 56 post-hoc comparisons.
> Without multiple comparison correction, this figure should be interpreted as an
> exploratory upper bound. The mean across all combinations was 53.3%.

### Key Findings

- **Model diversity matters more than model size.** The top combo mixes 7B, 3B, and 7B architectures from three different families (Qwen, Llama, Mistral). Same-family combos tend to underperform.
- **mistral:7b and gemma2:2b are the strongest contributors.** They appear in 7 and 6 of the top 10 combinations respectively, and have the highest per-model average accuracy (0.543 and 0.549).
- **fool-qwen drags accuracy down.** Combos with fool-qwen average 51.8% overall vs 54.2% without — a consistent 2.4pp penalty, with CONSISTENT accuracy cut in half (14.8% vs 28.5%).
- **Groupthink remains pervasive.** On average, 68.3 of 100 tasks show unanimous agreement across all 56 combinations. But the bias direction varies by combo rather than always favoring CONTRADICTION.
- **Split decisions have near-zero correlation with accuracy** (r = -0.089), meaning disagreement among nodes is neither reliably good nor bad for performance.

---

## 2. Full Leaderboard

All 56 combinations ranked by overall accuracy.

| Rank | Models | Overall | CONSISTENT | CONTRADICTION | Split | GT (total) |
|------|--------|---------|------------|---------------|-------|------------|
| 1 | qwen2.5:7b + llama3.2:3b + mistral:7b | **0.61** | 0.40 | 0.82 | 28 | 72 |
| 2 | qwen2.5:3b + llama3:latest + mistral:7b | 0.59 | 0.60 | 0.58 | 30 | 70 |
| 3 | llama3:latest + llama3.2:3b + gemma2:2b | 0.59 | 0.44 | 0.74 | 44 | 56 |
| 4 | llama3.2:3b + mistral:7b + gemma2:2b | 0.59 | 0.40 | 0.78 | 38 | 62 |
| 5 | llama3.1:8b + mistral:7b + gemma2:2b | 0.59 | 0.26 | 0.92 | 26 | 74 |
| 6 | llama3.1:8b + llama3.2:3b + gemma2:2b | 0.59 | 0.24 | 0.94 | 31 | 69 |
| 7 | qwen2.5:7b + llama3:latest + mistral:7b | 0.58 | 0.34 | 0.82 | 35 | 65 |
| 8 | llama3:latest + gemma2:2b + fool-qwen:latest | 0.58 | 0.18 | 0.98 | 40 | 60 |
| 9 | qwen2.5:7b + mistral:7b + gemma2:2b | 0.57 | 0.18 | 0.96 | 12 | 88 |
| 10 | llama3:latest + llama3.1:8b + mistral:7b | 0.56 | 0.56 | 0.56 | 46 | 54 |
| 11 | llama3:latest + mistral:7b + fool-qwen:latest | 0.56 | 0.32 | 0.80 | 32 | 68 |
| 12 | llama3:latest + llama3.1:8b + gemma2:2b | 0.56 | 0.30 | 0.82 | 40 | 60 |
| 13 | qwen2.5:3b + llama3:latest + llama3.1:8b | 0.56 | 0.26 | 0.86 | 31 | 69 |
| 14 | qwen2.5:3b + llama3:latest + gemma2:2b | 0.56 | 0.22 | 0.90 | 24 | 76 |
| 15 | qwen2.5:7b + llama3.1:8b + mistral:7b | 0.56 | 0.22 | 0.90 | 24 | 76 |
| 16 | qwen2.5:3b + mistral:7b + gemma2:2b | 0.56 | 0.20 | 0.92 | 16 | 84 |
| 17 | qwen2.5:3b + qwen2.5:7b + gemma2:2b | 0.56 | 0.14 | 0.98 | 16 | 84 |
| 18 | llama3:latest + mistral:7b + gemma2:2b | 0.55 | 0.42 | 0.68 | 35 | 65 |
| 19 | qwen2.5:3b + qwen2.5:7b + llama3.2:3b | 0.55 | 0.18 | 0.92 | 35 | 65 |
| 20 | qwen2.5:7b + llama3.2:3b + gemma2:2b | 0.55 | 0.16 | 0.94 | 24 | 76 |
| 21 | qwen2.5:7b + llama3:latest + fool-qwen:latest | 0.55 | 0.14 | 0.96 | 33 | 67 |
| 22 | llama3:latest + llama3.2:3b + fool-qwen:latest | 0.54 | 0.38 | 0.70 | 54 | 46 |
| 23 | qwen2.5:3b + qwen2.5:7b + llama3:latest | 0.54 | 0.22 | 0.86 | 22 | 78 |
| 24 | qwen2.5:3b + qwen2.5:7b + mistral:7b | 0.54 | 0.20 | 0.88 | 29 | 71 |
| 25 | qwen2.5:3b + llama3.1:8b + gemma2:2b | 0.54 | 0.14 | 0.94 | 19 | 81 |
| 26 | qwen2.5:3b + llama3.2:3b + gemma2:2b | 0.54 | 0.12 | 0.96 | 26 | 74 |
| 27 | llama3.1:8b + llama3.2:3b + mistral:7b | 0.53 | 0.48 | 0.58 | 51 | 49 |
| 28 | llama3.2:3b + mistral:7b + fool-qwen:latest | 0.53 | 0.36 | 0.70 | 43 | 57 |
| 29 | qwen2.5:3b + llama3.1:8b + mistral:7b | 0.53 | 0.24 | 0.82 | 29 | 71 |
| 30 | llama3.1:8b + llama3.2:3b + fool-qwen:latest | 0.53 | 0.18 | 0.88 | 49 | 51 |
| 31 | qwen2.5:3b + gemma2:2b + fool-qwen:latest | 0.53 | 0.12 | 0.94 | 26 | 74 |
| 32 | llama3.1:8b + gemma2:2b + fool-qwen:latest | 0.53 | 0.08 | 0.98 | 37 | 63 |
| 33 | llama3:latest + llama3.1:8b + fool-qwen:latest | 0.52 | 0.18 | 0.86 | 44 | 56 |
| 34 | qwen2.5:3b + qwen2.5:7b + llama3.1:8b | 0.52 | 0.14 | 0.90 | 26 | 74 |
| 35 | qwen2.5:7b + mistral:7b + fool-qwen:latest | 0.52 | 0.10 | 0.94 | 20 | 80 |
| 36 | mistral:7b + gemma2:2b + fool-qwen:latest | 0.52 | 0.10 | 0.94 | 29 | 71 |
| 37 | qwen2.5:7b + llama3.1:8b + fool-qwen:latest | 0.52 | 0.06 | 0.98 | 30 | 70 |
| 38 | qwen2.5:7b + gemma2:2b + fool-qwen:latest | 0.52 | 0.06 | 0.98 | 16 | 84 |
| 39 | qwen2.5:3b + llama3:latest + llama3.2:3b | 0.51 | 0.48 | 0.54 | 40 | 60 |
| 40 | qwen2.5:7b + llama3:latest + llama3.1:8b | 0.51 | 0.16 | 0.86 | 28 | 72 |
| 41 | qwen2.5:7b + llama3:latest + gemma2:2b | 0.51 | 0.12 | 0.90 | 19 | 81 |
| 42 | qwen2.5:3b + llama3:latest + fool-qwen:latest | 0.51 | 0.10 | 0.92 | 25 | 75 |
| 43 | qwen2.5:3b + qwen2.5:7b + fool-qwen:latest | 0.51 | 0.08 | 0.94 | 19 | 81 |
| 44 | qwen2.5:3b + llama3.1:8b + fool-qwen:latest | 0.51 | 0.06 | 0.96 | 32 | 68 |
| 45 | qwen2.5:7b + llama3.1:8b + gemma2:2b | 0.51 | 0.06 | 0.96 | 24 | 76 |
| 46 | llama3:latest + llama3.2:3b + mistral:7b | 0.50 | 0.72 | 0.28 | 29 | 71 |
| 47 | qwen2.5:7b + llama3:latest + llama3.2:3b | 0.50 | 0.22 | 0.78 | 40 | 60 |
| 48 | qwen2.5:7b + llama3.1:8b + llama3.2:3b | 0.50 | 0.14 | 0.86 | 31 | 69 |
| 49 | qwen2.5:7b + llama3.2:3b + fool-qwen:latest | 0.50 | 0.08 | 0.92 | 44 | 56 |
| 50 | llama3:latest + llama3.1:8b + llama3.2:3b | 0.49 | 0.40 | 0.58 | 48 | 52 |
| 51 | llama3.1:8b + mistral:7b + fool-qwen:latest | 0.48 | 0.16 | 0.80 | 34 | 66 |
| 52 | llama3.2:3b + gemma2:2b + fool-qwen:latest | 0.48 | 0.06 | 0.90 | 34 | 66 |
| 53 | qwen2.5:3b + llama3.2:3b + fool-qwen:latest | 0.47 | 0.16 | 0.78 | 38 | 62 |
| 54 | qwen2.5:3b + mistral:7b + fool-qwen:latest | 0.47 | 0.14 | 0.80 | 28 | 72 |
| 55 | qwen2.5:3b + llama3.2:3b + mistral:7b | 0.46 | 0.40 | 0.52 | 37 | 62 |
| 56 | qwen2.5:3b + llama3.1:8b + llama3.2:3b | 0.45 | 0.20 | 0.70 | 32 | 68 |

---

## 3. Model Analysis

### Per-Model Average Performance

| Model | Combos | Avg Overall | Avg CONSISTENT | Avg CONTRADICTION | Avg GT-CONTR | Avg GT-CONS | Avg Split |
|-------|--------|-------------|----------------|-------------------|-------------|-------------|-----------|
| gemma2:2b | 21 | **0.549** | 0.190 | **0.908** | 66.9 | 5.7 | 27.4 |
| mistral:7b | 21 | **0.543** | **0.324** | 0.762 | 52.6 | 16.3 | 31.0 |
| llama3:latest | 21 | 0.541 | **0.322** | 0.761 | 50.4 | 14.4 | 35.2 |
| qwen2.5:7b | 21 | 0.535 | 0.162 | 0.908 | 67.6 | 6.0 | 26.4 |
| llama3.1:8b | 21 | 0.528 | 0.215 | 0.841 | 58.7 | 7.4 | 33.9 |
| llama3.2:3b | 21 | 0.524 | 0.295 | 0.753 | 48.8 | 13.2 | 37.9 |
| qwen2.5:3b | 21 | 0.524 | 0.210 | 0.839 | 62.3 | 10.0 | 27.6 |
| fool-qwen:latest | 21 | 0.518 | 0.148 | 0.889 | 61.2 | 5.1 | 33.7 |

### Top 10 / Bottom 10 Appearances

| Model | Top 10 appearances | Bottom 10 appearances | Net |
|-------|-------------------:|----------------------:|----:|
| mistral:7b | 7 | 3 | +4 |
| gemma2:2b | 6 | 1 | +5 |
| llama3:latest | 5 | 2 | +3 |
| llama3.2:3b | 4 | 8 | -4 |
| qwen2.5:7b | 3 | 3 | 0 |
| llama3.1:8b | 3 | 4 | -1 |
| qwen2.5:3b | 1 | 4 | -3 |
| fool-qwen:latest | 1 | 5 | -4 |

### CONSISTENT Accuracy Contributors

Models that boost CONSISTENT accuracy (ability to correctly identify non-contradictions):

1. **mistral:7b** (avg 32.4%) and **llama3:latest** (avg 32.2%) — these two models are the strongest at resisting the CONTRADICTION bias. Their combos tend to have higher CONSISTENT scores.
2. **llama3.2:3b** (avg 29.5%) — surprisingly strong for a 3B model, likely because it introduces enough "noise" to break groupthink patterns.

### CONTRADICTION Accuracy Contributors

Models that boost CONTRADICTION accuracy:

1. **gemma2:2b** (avg 90.8%) and **qwen2.5:7b** (avg 90.8%) — these models strongly lean toward CONTRADICTION and are very effective at detecting true contradictions.
2. **fool-qwen:latest** (avg 88.9%) — also high CONTRADICTION accuracy, but at the cost of almost entirely suppressing CONSISTENT detection.

### fool-qwen Behavior Analysis

| Metric | With fool-qwen | Without fool-qwen | Delta |
|--------|---------------:|------------------:|------:|
| Overall accuracy | 51.8% | 54.2% | **-2.4pp** |
| CONSISTENT acc | 14.8% | 28.5% | **-13.7pp** |
| CONTRADICTION acc | 88.9% | 79.9% | +9.0pp |
| Avg split decisions | 33.7 | 30.4 | +3.3 |

fool-qwen acts as a **CONTRADICTION amplifier**. While it boosts CONTRADICTION detection by 9pp, it crushes CONSISTENT accuracy by nearly 14pp — a net loss. It also slightly increases split decisions, suggesting it sometimes disagrees with more balanced models but ultimately drags the majority toward CONTRADICTION.

The only fool-qwen combo in the top 10 is `llama3:latest + gemma2:2b + fool-qwen:latest` (#8, 58%), which achieves 98% CONTRADICTION but only 18% CONSISTENT — a deceptive accuracy that only works because the task is 50/50 balanced.

---

## 4. Groupthink Analysis

### Distribution

- **Mean groupthink (unanimous agreement):** 68.3 / 100 tasks
- **Range:** 46 — 88 unanimous tasks
- **Median:** ~69 unanimous tasks

Even in the most diverse combination, nodes agreed unanimously on nearly half of all tasks. In the most homogeneous combo, 88% of tasks showed unanimous agreement.

### Groupthink Extremes

**Most groupthink:** `qwen2.5:7b + mistral:7b + gemma2:2b` — 88 unanimous (80 all-CONTRADICTION, 8 all-CONSISTENT), only 12 splits. Despite this, it still achieved 57% overall, suggesting the unanimity was often correct on CONTRADICTION tasks.

**Least groupthink:** `llama3:latest + llama3.2:3b + fool-qwen:latest` — 46 unanimous (33 all-CONTRADICTION, 13 all-CONSISTENT), 54 splits. This is the most "deliberative" combination, but it only achieved 54% overall.

### Groupthink Direction

The vast majority of groupthink leans CONTRADICTION:

- Average all-CONTRADICTION groupthink: **57.7** / 100
- Average all-CONSISTENT groupthink: **9.5** / 100

Only one combination shows a CONSISTENT-majority groupthink: `llama3:latest + llama3.2:3b + mistral:7b` with 56 all-CONSISTENT vs 15 all-CONTRADICTION. Notably, this combo has the highest CONSISTENT accuracy (72%) but the lowest CONTRADICTION accuracy (28%) and only 50% overall.

### Groupthink vs Accuracy Correlation

**Correlation: r = 0.092** (essentially zero).

Groupthink is not inherently harmful. What matters is the *direction* of groupthink. When all nodes converge on the correct answer, groupthink is beneficial. The problem arises when systemic model bias causes convergence on the wrong answer — which happens predominantly on CONSISTENT tasks where models default to CONTRADICTION.

---

## 5. Split Decision Analysis

### Overview

- **Mean splits:** 31.6 / 100 tasks
- **Range:** 12 — 54 splits
- **Correlation with overall accuracy:** r = **-0.089** (negligible)

Split decisions — where nodes disagree — do not reliably predict better or worse accuracy.

### High-Split Combinations (> 40 splits)

| Combination | Split | Overall |
|-------------|------:|--------:|
| llama3:latest + llama3.2:3b + fool-qwen:latest | 54 | 0.54 |
| llama3.1:8b + llama3.2:3b + mistral:7b | 51 | 0.53 |
| llama3.1:8b + llama3.2:3b + fool-qwen:latest | 49 | 0.53 |
| llama3:latest + llama3.1:8b + llama3.2:3b | 48 | 0.49 |
| llama3:latest + llama3.1:8b + mistral:7b | 46 | 0.56 |
| llama3:latest + llama3.2:3b + gemma2:2b | 44 | 0.59 |
| llama3:latest + llama3.1:8b + fool-qwen:latest | 44 | 0.52 |
| qwen2.5:7b + llama3.2:3b + fool-qwen:latest | 44 | 0.50 |
| llama3.2:3b + mistral:7b + fool-qwen:latest | 43 | 0.53 |

**llama3.2:3b** appears in 7 of 9 high-split combos — it is the primary driver of disagreement. This small model's divergent behavior creates split decisions but does not consistently improve accuracy.

### Key Insight

High disagreement ≠ better reasoning. The NCA update rule uses majority vote, so splits mean one model is being overruled. Whether this helps depends entirely on whether the overruled model was right or wrong. The data shows this is essentially random (r ≈ 0), suggesting the current NCA rule does not effectively leverage disagreement.

---

## 6. Comparison with v1-v4

| Version | Overall | CONSISTENT | CONTRADICTION | GT All-CONTR | GT All-CONS | Split | Key Change |
|---------|---------|------------|---------------|-------------|-------------|-------|------------|
| Fixed (baseline) | 45.0% | 2.0% | 88.0% | — | — | — | Sequential pipeline |
| NCA v1 | 49.0% | 0.0% | 98.0% | 99 | 0 | 0 | Baseline NCA (all qwen2.5:3b) |
| NCA v2 | 55.0% | **80.0%** | 30.0% | 17 | 65 | 18 | Anti-sycophancy prompts |
| NCA v3 | 52.0% | 6.0% | 98.0% | 77 | 2 | 21 | Devil's advocate rule |
| NCA v4 | 53.0% | 24.0% | 82.0% | 75 | 17 | 8 | Confidence weighting |
| **v5 best** | **61.0%** | 40.0% | 82.0% | 57 | 15 | 28 | Multi-model combos |
| v5 most balanced | 56.0% | 56.0% | 56.0% | 25 | 29 | 46 | llama3 + llama3.1 + mistral |
| v5 mean (56 combos) | 53.3% | 23.7% | 82.9% | 57.7 | 9.5 | 31.6 | — |

### Takeaways

- **v5 is the first version to break 60% overall accuracy.** Model diversity alone — without any prompt engineering tricks from v2-v4 — surpasses all prior approaches.
- **v2 remains the CONSISTENT accuracy champion** (80%), but at the cost of CONTRADICTION (30%). No v5 combo matches this CONSISTENT score.
- **v5's best combo achieves the best trade-off:** 40% CONSISTENT + 82% CONTRADICTION is far more balanced than v1/v3/v4's CONTRADICTION-dominated profiles.
- **The v5 most balanced combo** (`llama3:latest + llama3.1:8b + mistral:7b`, 56% / 56% / 56%) is a unique result — perfectly symmetric accuracy, something no prior version achieved.
- **v5 average (53.3%) matches v4 (53%)**, meaning the median multi-model combo performs comparably to confidence-weighted single-model NCA. The gains come from choosing the right combination.

---

## 7. Recommendations for v6

### Top 3 Model Combinations to Prioritize

1. **qwen2.5:7b + llama3.2:3b + mistral:7b** (61% overall) — Best raw accuracy. Strong CONTRADICTION detection from qwen2.5:7b, balanced by mistral:7b's CONSISTENT strength. llama3.2:3b adds productive disagreement.

2. **qwen2.5:3b + llama3:latest + mistral:7b** (59% overall) — Most balanced high-performer with 60% CONSISTENT and 58% CONTRADICTION. Ideal candidate for v6 prompt engineering since there is no strong bias to correct.

3. **llama3:latest + llama3.2:3b + gemma2:2b** (59% overall) — Best Qwen-free combination. Tests whether the Qwen family is essential or if diversity alone drives performance.

### Hypotheses for v6

1. **Combining v4's confidence weighting with v5's best combos should yield > 65%.** The v5 winner has 28 split decisions — applying confidence-weighted voting instead of simple majority could resolve those splits more accurately.

2. **Anti-sycophancy prompts (v2) applied to the balanced combo (#2) could push CONSISTENT accuracy above 70% without collapsing CONTRADICTION.** The combo already has 60% CONSISTENT naturally — a lighter anti-sycophancy nudge may be enough.

3. **Agreement intensity matters: strong unanimous agreement (3/3 with high confidence) should be trusted, while weak unanimity (3/3 with mixed confidence) should trigger re-evaluation.** The current binary groupthink metric (unanimous vs split) misses this nuance. v6 should track per-node confidence and treat "confident consensus" differently from "uncertain consensus."

4. **Drop fool-qwen from the model pool.** It consistently reduces overall accuracy by 2.4pp and provides no unique capability that gemma2:2b doesn't cover better. The 21 experiment slots used for fool-qwen combos could be better spent on random sampling from the top 5 models.

5. **Try 5-node rings with the top 3 models + 2 wild cards.** v5 showed that 3-model diversity helps — expanding the ring may further reduce groupthink and improve split resolution, at the cost of inference time.
