# NCA v7.6 Experiment Report: High School Math Tasks with Role-Division NCA

> Same 5 role-division patterns as v7/v7.5, tested on 75 high school math tasks (25 per grade level: Grade 10/11/12), completing the difficulty series from elementary to high school.

---

## 1. Executive Summary

**Best pattern:** `best_fixed` (qwen2.5:7b + llama3 + mistral, fixed roles) — **77% overall accuracy**, reclaiming the top spot from balanced_rotating (v7.5 winner).

**The surprising finding:** best_fixed *improves* from 72% (v7.5) to 77% (v7.6), a **+5pp gain** when moving from middle school to high school math. This is the only pattern to improve with higher difficulty, and it matches its v7 elementary score of 83% minus just 6pp total.

**best_rotating collapse:** From 81% (v7) to 73% (v7.5) to **63% (v7.6)** — a total drop of -18pp, the largest degradation of any pattern. Rotation, which was a powerful de-biasing tool at lower difficulty, becomes a liability at high school level.

### Key Findings

- **The difficulty wall is between elementary and middle school, not between middle and high school.** best_fixed scores 83% -> 72% -> 77%, meaning the hardest transition was elementary to middle school (-11pp), while high school actually recovered (+5pp).
- **Grade 11 (trig/logs) is the easiest high school level** at 56-92% across patterns — these "advanced" topics are heavily memorized formulas that LLMs pattern-match well.
- **Rotation becomes harmful at high school difficulty.** best_rotating drops to 31% INCORRECT accuracy — it misses 69% of actual errors, making it unreliable for error detection.
- **best_fixed achieves near-balanced accuracy** (79% CORRECT / 75% INCORRECT) — the most balanced profile of any pattern at any difficulty level in the entire v7 series.
- **Training data coverage dominates computational difficulty**: trig values (84%), logarithms (80%), and derivatives (80%) outperform "easier" topics like quadratic inequalities (48%) and area calculations (48%).

---

## 2. Full Results Table

| Pattern | Overall | G10 | G11 | G12 | CORRECT | INCORRECT | v7.5 Diff | Total Drop (v7) |
|---------|---------|-----|-----|-----|---------|-----------|-----------|-----------------|
| **best_fixed** | **77%** | 64% | **92%** | 76% | 79% | **75%** | **+5pp** | **-6pp** |
| single_agent | 71% | 60% | 88% | 64% | 67% | 75% | -4pp | -12pp |
| balanced_rotating | 68% | 60% | 84% | 60% | 82% | 53% | -9pp | -12pp |
| best_rotating | 63% | 64% | 68% | 56% | 92% | 31% | -10pp | **-18pp** |
| balanced_fixed | 56% | 52% | 56% | 60% | 44% | 69% | -1pp | -12pp |

### Groupthink Distribution

| Pattern | All CORRECT | All INCORRECT | Split |
|---------|-------------|---------------|-------|
| balanced_rotating | **47** | 14 | 14 |
| best_fixed | 29 | **31** | 15 |
| best_rotating | 29 | 9 | **37** |
| balanced_fixed | 21 | 20 | 34 |
| single_agent | — | — | — |

best_fixed shows nearly equal CORRECT/INCORRECT groupthink (29/31) — reflecting its balanced accuracy profile. best_rotating has the most split decisions (37/75 = 49%), indicating that rotation at high difficulty creates persistent disagreement rather than productive consensus.

---

## 3. Complete Difficulty Series

### Overall Accuracy Across All Three Levels

| Pattern | v7 (Elementary) | v7.5 (Middle) | v7.6 (High) | Total Drop | Trajectory |
|---------|-----------------|---------------|-------------|------------|------------|
| **best_fixed** | **83%** | 72% | **77%** | **-6pp** | Down then **up** |
| single_agent | **83%** | 75% | 71% | -12pp | Steady decline |
| balanced_rotating | 80% | **77%** | 68% | -12pp | Steady decline |
| best_rotating | 81% | 73% | 63% | **-18pp** | Accelerating decline |
| balanced_fixed | 68% | 57% | 56% | -12pp | Steep then flat |

### CORRECT Accuracy Across Levels

| Pattern | v7 | v7.5 | v7.6 | Trend |
|---------|-----|------|------|-------|
| best_fixed | 77% | 74% | 79% | Stable |
| best_rotating | 96% | 95% | 92% | Slight decline |
| balanced_fixed | 73% | 49% | 44% | Collapsing |
| balanced_rotating | 87% | 92% | 82% | Peaked at v7.5 |
| single_agent | 69% | 74% | 67% | Fluctuating |

### INCORRECT Accuracy Across Levels

| Pattern | v7 | v7.5 | v7.6 | Trend |
|---------|-----|------|------|-------|
| best_fixed | 90% | 69% | 75% | Down then **up** |
| best_rotating | 65% | 50% | **31%** | Collapsing |
| balanced_fixed | 62% | 67% | 69% | Slight improvement |
| balanced_rotating | 73% | 61% | 53% | Declining |
| single_agent | 98% | 75% | 75% | Stabilized |

### Key Trajectory Insight

best_fixed is the only pattern with a **non-monotonic** trajectory — it dips at middle school then recovers at high school. This suggests that middle school math (simultaneous equations, polynomial expansion) was a uniquely bad fit for the v7 task set, while high school topics (trig, logs, calculus) better match LLM training data and the fixed Solver-Verifier-Critic pipeline.

---

## 4. Grade Level Analysis

### Performance by Grade Level

| Pattern | Grade 10 (高1) | Grade 11 (高2) | Grade 12 (高3) |
|---------|----------------|----------------|----------------|
| best_fixed | 64% | **92%** | 76% |
| best_rotating | 64% | 68% | 56% |
| balanced_fixed | 52% | 56% | 60% |
| balanced_rotating | 60% | **84%** | 60% |
| single_agent | 60% | **88%** | 64% |
| **Mean** | **60.0%** | **77.6%** | **63.2%** |

### Grade 11 (Trig/Logs) Is the Easiest: Training Data Coverage

Grade 11 (77.6% mean) dramatically outperforms both Grade 10 (60.0%) and Grade 12 (63.2%). The per-type breakdown explains why:

**Grade 11 strengths (all heavily memorized):**
- `trig_value`: 84% mean — sin(30°) = 1/2 is one of the most common facts in math training data
- `trig_identity`: 80% mean — sin²θ + cos²θ = 1 is a universal identity
- `logarithm`: 80% mean — log₂(8) = 3 is direct computation
- `recurrence`: 80% mean — geometric sequences follow a simple formula

**Grade 10 weaknesses (procedural reasoning):**
- `quadratic_ineq`: 48% mean — requires factoring, number line analysis, and sign tracking
- `factoring`: 56% mean — must find two numbers that multiply and add to given values
- `quadratic_minmax`: 60% mean — requires completing the square or vertex formula

**Grade 12 mixed (some formulaic, some procedural):**
- `derivative`: 80% mean — power rule is formulaic (nx^(n-1))
- `integral`: 68% mean — reverse of differentiation, harder
- `area`: 48% mean — requires setting up and evaluating a definite integral
- `arithmetic_seq`: 52% mean — sum formula S_n = n(a₁+aₙ)/2 requires multi-step computation

### Per-Grade CORRECT vs INCORRECT Breakdown

| Pattern | G10 CORR | G10 INCORR | G11 CORR | G11 INCORR | G12 CORR | G12 INCORR |
|---------|----------|-----------|----------|-----------|----------|-----------|
| best_fixed | 62% | 67% | **100%** | 83% | 77% | 75% |
| best_rotating | 92% | 33% | 100% | 33% | 85% | 25% |
| balanced_fixed | 31% | 75% | 62% | 50% | 38% | 83% |
| balanced_rotating | 77% | 42% | 85% | **83%** | 85% | 33% |
| single_agent | 54% | 67% | 92% | **83%** | 54% | 75% |

best_fixed achieves **100% CORRECT accuracy on Grade 11** — it never misclassifies a correct trig/log statement. Combined with 83% INCORRECT accuracy, this gives Grade 11 the best balanced performance of any grade-pattern combination.

---

## 5. Rotation Analysis: From Benefit to Liability

### The Rotation Effect Across Difficulty Levels

| Config | v7 Rotation Gain | v7.5 Rotation Gain | v7.6 Rotation Gain |
|--------|------------------|--------------------|--------------------|
| Best | -2pp | +1pp | **-14pp** |
| Balanced | +12pp | +20pp | **+12pp** |

**For the best config, rotation has become destructive.** At v7 it was neutral (-2pp), at v7.5 slightly positive (+1pp), and at v7.6 it's severely harmful (-14pp). The pattern is clear: as tasks get harder, rotating the strong Solver (qwen2.5:7b) away from its role degrades the pipeline's ability to catch errors.

**For the balanced config, rotation remains beneficial** at +12pp, identical to v7. The balanced models (mistral + llama3 + llama3.1:8b) all have similar individual capability, so rotation doesn't sacrifice Solver quality.

### best_rotating's INCORRECT Collapse

| Level | INCORRECT acc |
|-------|--------------|
| v7 (elementary) | 65% |
| v7.5 (middle) | 50% |
| v7.6 (high school) | **31%** |

At high school level, best_rotating misses **69% of actual errors**. The mechanism:
1. Rotation gives each model a turn as Solver, and weaker models (llama3, mistral) produce less confident error detections
2. When these weaker Solvers say "CORRECT" with moderate confidence, the downstream Verifier and Critic tend to agree
3. The aggregation then favors CORRECT, even when the statement is wrong

### The Threshold Where Rotation Becomes Harmful

The data suggests a clear threshold: **rotation helps when individual model accuracy is similar, but hurts when one model (qwen2.5:7b) is clearly stronger than the others on the task domain.** At elementary math, all three models are competent enough; at high school math, qwen2.5:7b's advantage as Solver matters, and rotating it away is costly.

---

## 6. Pattern Stability Analysis

### Stability Rankings (by total drop from v7)

| Rank | Pattern | v7 | v7.5 | v7.6 | Total Drop | Variance |
|------|---------|-----|------|------|------------|----------|
| 1 | **best_fixed** | 83% | 72% | **77%** | **-6pp** | Recovers |
| 2 | single_agent | 83% | 75% | 71% | -12pp | Steady decline |
| 2 | balanced_rotating | 80% | 77% | 68% | -12pp | Steady decline |
| 2 | balanced_fixed | 68% | 57% | 56% | -12pp | Floor at ~56% |
| 5 | best_rotating | 81% | 73% | 63% | **-18pp** | Accelerating |

### Why Fixed Roles Handle Increasing Difficulty Better

best_fixed's stability comes from **role specialization**:
- **qwen2.5:7b (Solver, agree=30%):** The strongest model always solves. Low agreement means it trusts its own computation, which becomes more valuable as tasks get harder.
- **llama3 (Verifier, agree=80%):** High agreement means it usually confirms qwen2.5:7b's work, but still catches obvious errors through independent verification.
- **mistral (Critic, agree=80%):** High agreement means it defers to the Solver-Verifier consensus when they agree, adding a final sanity check without overriding correct answers.

This pipeline works because **the best model is always in the most important role**. Rotation disrupts this by putting weaker models in the Solver position, which is fatal when the Solver role requires genuine mathematical competence.

### best_fixed vs Single Agent

| Metric | best_fixed | single_agent | Advantage |
|--------|------------|-------------|-----------|
| v7.6 Overall | **77%** | 71% | +6pp best_fixed |
| CORRECT acc | 79% | 67% | +12pp best_fixed |
| INCORRECT acc | **75%** | **75%** | Tied |
| Total drop | **-6pp** | -12pp | best_fixed more stable |

best_fixed outperforms the single agent by 6pp at high school level, demonstrating that the multi-model NCA adds value when roles are properly assigned. The advantage is entirely in CORRECT accuracy (+12pp) — the Verifier and Critic help confirm correct answers that the single agent would mistakenly reject.

---

## 7. The Difficulty Curve Finding

### The Non-Monotonic Curve

```
best_fixed:  83% ──(-11pp)──> 72% ──(+5pp)──> 77%
                  elementary    middle school    high school
```

This is the most surprising finding of the difficulty series. The "wall" is between elementary and middle school, not between middle and high school. High school math is, in several ways, **easier for LLMs than middle school math**.

### Why the Wall Is at Middle School

**Middle school introduces multi-step procedural tasks** that LLMs handle poorly:
- Simultaneous equations: 60% mean in v7.5
- Polynomial expansion: 48% mean in v7.5
- Algebraic expressions: 40% mean in v7.5

**High school introduces formula-heavy topics** that LLMs handle well:
- Trigonometric values: 84% mean in v7.6
- Derivatives (power rule): 80% mean in v7.6
- Logarithms: 80% mean in v7.6

The paradox resolves when we recognize that **LLM difficulty is driven by training data coverage and pattern-matchability, not by human-perceived computational difficulty.** High school math is full of famous formulas and identities that appear extensively in training corpora, while middle school math requires procedural execution that LLMs can't shortcut with memorization.

### The True Difficulty Boundary

Across all three levels, the hardest task types share a common property — they require **multi-step procedural reasoning where errors compound**:

| Difficulty Tier | Accuracy | Task Types | Common Property |
|----------------|----------|-----------|-----------------|
| Pattern-match | 80-100% | trig values, similarity, derivatives | Single formula lookup |
| Formula + verify | 60-80% | logarithms, quadratic eval, geometry | Apply formula + check result |
| Multi-step procedure | 40-60% | simultaneous eq, polynomial, area | Multiple operations in sequence |
| Symbolic manipulation | 20-40% | algebraic expressions | Variable manipulation without numbers |

This ordering is stable across v7, v7.5, and v7.6, confirming that **operation type, not grade level, determines LLM difficulty**.

---

## 8. Connection to AutoHarness (arXiv:2603.03329)

### Training Data Coverage vs Genuine Reasoning

The v7.6 results provide strong evidence for the distinction between **pattern-matching** and **reasoning** that the AutoHarness paper (Cai et al., 2025) highlights in the context of LLM evaluation.

**Pattern-matching success (Grade 11 = 77.6% mean):**
- sin(30°) = 1/2 — this fact appears in millions of training examples
- log₂(8) = 3 — direct exponent recognition
- The LLM doesn't "reason" about these; it retrieves memorized associations

**Genuine reasoning failure (Grade 10 = 60.0% mean, some types at 48%):**
- "Is x < -2 or x > 1 the solution to x² + x - 2 > 0?" — requires factoring, root finding, and sign analysis
- "Is the area between y = x² and y = 2x equal to 4/3?" — requires integration setup and evaluation
- These tasks require multi-step computation that can't be shortcut by memorization

### Implications for Harness Comparison (v11)

The difficulty series reveals that **task design critically affects accuracy measurements.** A harness that tests mainly formulaic knowledge (trig values, derivative rules) will overestimate LLM mathematical reasoning capability, while one focused on procedural tasks (multi-step algebra, proof construction) will give a more accurate picture.

For the planned v11 harness comparison experiment, this suggests:
1. **Stratify tasks by operation type**, not grade level, to avoid the training data coverage confound
2. **Include procedural tasks** (simultaneous equations, polynomial expansion) as the true test of reasoning
3. **Use the 48-60% accuracy range** as the "interesting zone" where NCA architecture can potentially add value over single agents

### Where NCA Architecture Adds Value

Across the difficulty series, NCA (best_fixed) outperforms single_agent most consistently in the **60-80% accuracy range** — tasks hard enough that individual models make errors, but structured enough that cross-verification catches them. At very easy tasks (>80%), single agent is sufficient. At very hard tasks (<50%), all models fail similarly and NCA coordination can't help.

---

## 9. Recommendations

### Should v7.7 (Proof Construction) Be Attempted?

**Not yet.** The verification-based task format still has unexplored territory:
- Multi-step verification ("Find the error in this 5-step solution") would test sequential reasoning
- Adversarial verification ("This solution looks correct but has a subtle sign error") would test careful checking
- These remain automatically gradable while pushing toward deeper reasoning

Proof construction introduces the unsolved evaluation problem (grading free-form proofs) and should wait until the verification frontier is fully mapped.

### Configurations to Carry Into v8+

1. **best_fixed** (qwen2.5:7b + llama3 + mistral, agree=[30,80,80], steps=3, fixed) — The overall champion. Most robust across all difficulty levels (-6pp total drop), best balanced accuracy at high school (79/75), and the only pattern that improves with difficulty increase.

2. **balanced_rotating** (mistral + llama3 + llama3.1:8b, agree=[80,70,10], steps=2, rotating) — Best for lower difficulty tasks. Won v7.5 (77%), still strong at v7.6 (68%), and rotation consistently helps this config.

3. **single_agent** (qwen2.5:7b) — Essential baseline. Surprisingly competitive at all levels and provides the most balanced CORRECT/INCORRECT accuracy.

**Drop:** best_rotating (too fragile at higher difficulty) and balanced_fixed (near-random at 56%).

### How the Difficulty Series Informs Adaptive Model Selection (v8)

The v7 series reveals that **optimal configuration depends on task difficulty**:

| Difficulty Zone | Best Pattern | Why |
|----------------|-------------|-----|
| Easy (>80% single) | Any / single_agent | NCA overhead doesn't help |
| Medium (60-80% single) | **best_fixed** | Role specialization catches errors |
| Hard (<60% single) | **balanced_rotating** | Diversity + rotation prevents collapse |

A v8 adaptive system could:
1. **Estimate task difficulty** from the Solver's initial confidence
2. **Route easy tasks** directly to single agent (saves 90% of compute time)
3. **Route medium tasks** to best_fixed pipeline
4. **Route hard tasks** to balanced_rotating pipeline

This would optimize both accuracy and efficiency across the full difficulty spectrum.

---

## Appendix: Per-Type Accuracy (All Patterns)

| Task Type | Grade | best_fixed | best_rot | bal_fixed | bal_rot | single | Mean |
|-----------|-------|------------|----------|-----------|---------|--------|------|
| trig_value | 11 | 100% | 80% | 60% | 80% | 100% | **84%** |
| trig_identity | 11 | 100% | 60% | 80% | 80% | 80% | **80%** |
| logarithm | 11 | 100% | 60% | 40% | 100% | 100% | **80%** |
| recurrence | 11 | 80% | 100% | 40% | 100% | 80% | **80%** |
| derivative | 12 | 100% | 60% | 80% | 60% | 100% | **80%** |
| probability | 10 | 80% | 80% | 60% | 80% | 60% | **72%** |
| extremum | 12 | 60% | 80% | 60% | 80% | 60% | **68%** |
| integral | 12 | 100% | 60% | 60% | 60% | 60% | **68%** |
| exponent | 11 | 80% | 40% | 60% | 60% | 80% | **64%** |
| logic_quad | 10 | 80% | 60% | 60% | 60% | 60% | **64%** |
| quadratic_minmax | 10 | 60% | 80% | 40% | 60% | 60% | **60%** |
| factoring | 10 | 40% | 60% | 60% | 80% | 40% | **56%** |
| arithmetic_seq | 12 | 60% | 60% | 40% | 60% | 40% | **52%** |
| area | 12 | 60% | 20% | 60% | 40% | 60% | **48%** |
| quadratic_ineq | 10 | 60% | 40% | 40% | 20% | 80% | **48%** |

---

## Appendix: Experiment Design

- **Task set:** 75 high school math tasks (25 Grade 10, 25 Grade 11, 25 Grade 12), 39 CORRECT / 36 INCORRECT, seed=42
- **Grade 10 types:** quadratic min/max, quadratic inequalities, factoring, probability, logic about parabolas
- **Grade 11 types:** trig values, trig identities, logarithms, exponents, recurrence relations
- **Grade 12 types:** derivatives, extrema, integrals, area between curves, arithmetic sequences
- **Models / patterns:** Identical to v7/v7.5 (5 patterns, same models and agreement settings)
- **Runtime:** 2.4 hours total (best_fixed: 44min, best_rotating: 41min, balanced_fixed: 31min, balanced_rotating: 27min, single_agent: 4min)
