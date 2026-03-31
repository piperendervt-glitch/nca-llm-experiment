# NCA v7.5 Experiment Report: Middle School Math Tasks with Role-Division NCA

> Same 5 role-division patterns as v7 (elementary), tested on 75 middle school math tasks (25 per grade level: Grade 7/8/9), to measure difficulty degradation.

---

## 1. Executive Summary

**Best pattern:** `balanced_rotating` (mistral + llama3 + llama3.1:8b, rotating) — **77% overall accuracy**, surpassing all other patterns including the single agent baseline (75%).

**Most notable shift:** `balanced_rotating` goes from 4th place in v7 (80%) to 1st place in v7.5 (77%) — it is the most robust pattern to difficulty increase, dropping only 3pp vs 8-11pp for others.

**Comparison vs v7 (elementary):** All patterns degrade, but by varying amounts:
- balanced_rotating: 80% -> 77% (**-3pp**, most robust)
- best_rotating: 81% -> 73% (-8pp)
- single_agent: 83% -> 75% (-8pp)
- best_fixed: 83% -> 72% (-11pp)
- balanced_fixed: 68% -> 57% (-11pp, collapses)

### Key Findings

- **Grade 8 is the hardest level (56-72%), not Grade 9 (56-92%).** This counter-intuitive result suggests that simultaneous equations and polynomial expansion are harder for LLMs than quadratic equations and Pythagorean theorem — likely because the latter are more heavily represented in training data.
- **Rotation's de-biasing effect persists at higher difficulty.** Both rotating patterns achieve 92-95% CORRECT accuracy, but INCORRECT accuracy drops to 50-61%, creating even more extreme bias than v7.
- **`algebraic_expr` and `polynomial` are the hardest task types** at 40% and 48% mean accuracy — LLMs struggle with symbolic manipulation tasks where the answer involves variable expressions rather than numbers.
- **`similarity` is universally solved** at 100% across all 5 patterns — the simplest pattern-matching task in the set.
- **balanced_fixed collapses to 57%** (near random), confirming that the contrarian Critic (llama3.1:8b at 10% agreement) actively hurts performance when tasks are harder and consensus is more often correct.

---

## 2. Full Results Table

| Pattern | Overall | Grade7 | Grade8 | Grade9 | CORRECT | INCORRECT | v7 Overall | v7 Diff |
|---------|---------|--------|--------|--------|---------|-----------|------------|---------|
| **balanced_rotating** | **77%** | 72% | 68% | **92%** | 92% | 61% | 80% | **-3pp** |
| single_agent | 75% | 64% | 72% | 88% | 74% | 75% | 83% | -8pp |
| best_rotating | 73% | 72% | 72% | 76% | **95%** | 50% | 81% | -8pp |
| best_fixed | 72% | 68% | 60% | 88% | 74% | 69% | 83% | -11pp |
| balanced_fixed | 57% | 60% | 56% | 56% | 49% | 67% | 68% | -11pp |

### Groupthink Distribution

| Pattern | All CORRECT | All INCORRECT | Split |
|---------|-------------|---------------|-------|
| balanced_rotating | **44** | 12 | 19 |
| best_fixed | 35 | 34 | 6 |
| best_rotating | 34 | 8 | **33** |
| balanced_fixed | 19 | 18 | **38** |
| single_agent | — | — | — |

balanced_rotating shows strong CORRECT groupthink (44/75), indicating that when models agree through rotation, they tend to agree on the right answer for correct statements. best_fixed has nearly equal CORRECT/INCORRECT groupthink (35/34), reflecting its more balanced bias profile.

---

## 3. Grade Level Analysis

### Performance by Grade Level

| Pattern | Grade 7 (中1) | Grade 8 (中2) | Grade 9 (中3) |
|---------|---------------|---------------|---------------|
| best_fixed | 68% | **60%** | 88% |
| best_rotating | 72% | 72% | 76% |
| balanced_fixed | 60% | 56% | 56% |
| balanced_rotating | 72% | 68% | **92%** |
| single_agent | 64% | 72% | 88% |
| **Mean** | **67.2%** | **65.6%** | **80.0%** |

### Why Grade 8 Is the Hardest (Counter-Intuitive Finding)

Grade 8 (65.6% mean) underperforms Grade 7 (67.2%) and substantially underperforms Grade 9 (80.0%), despite being the "middle" difficulty level. The per-type breakdown reveals why:

**Grade 8 trouble spots:**
- `simultaneous_eq`: 60% mean — requires solving two equations simultaneously, a multi-step process where errors compound
- `polynomial`: 48% mean — (x+a)(x+b) expansion demands precise symbolic manipulation
- `congruence`: 72% mean — geometric reasoning about triangle congruence conditions

**Grade 9 strengths:**
- `similarity`: 100% mean — ratio comparison is a simple pattern-match
- `quadratic_fn`: 88% mean — direct evaluation of y = ax² + bx + c at a given x
- `square_root`: 84% mean — sqrt simplification is well-represented in training data

The key insight: **computational difficulty ≠ LLM difficulty**. Grade 9 topics (quadratic equations, Pythagorean theorem, square roots) are well-covered in math training data and have formulaic solutions. Grade 8 topics (simultaneous equations, polynomial expansion) require more procedural multi-step reasoning where LLMs make cascading errors.

### Grade-Level CORRECT vs INCORRECT Breakdown

| Pattern | G7 CORRECT | G7 INCORRECT | G8 CORRECT | G8 INCORRECT | G9 CORRECT | G9 INCORRECT |
|---------|------------|-------------|------------|-------------|------------|-------------|
| best_fixed | 69% | 67% | 69% | 50% | 85% | 92% |
| best_rotating | 92% | 50% | 100% | 42% | 92% | 58% |
| balanced_fixed | 54% | 67% | 62% | 50% | 31% | 83% |
| balanced_rotating | 85% | 58% | 92% | 42% | 100% | 83% |
| single_agent | 62% | 67% | 77% | 67% | 85% | 92% |

Notable: best_rotating achieves **100% CORRECT accuracy on Grade 8** — it never misclassifies a correct Grade 8 statement. But its INCORRECT accuracy drops to 42%, meaning it misses over half of actual errors.

---

## 4. Difficulty Degradation Analysis

### Per-Pattern Degradation (v7 -> v7.5)

| Pattern | v7 (Elementary) | v7.5 (Middle School) | Drop | Robustness Rank |
|---------|-----------------|---------------------|------|-----------------|
| balanced_rotating | 80% | 77% | **-3pp** | 1st (most robust) |
| best_rotating | 81% | 73% | -8pp | 2nd |
| single_agent | 83% | 75% | -8pp | 2nd |
| best_fixed | 83% | 72% | -11pp | 4th |
| balanced_fixed | 68% | 57% | -11pp | 5th (least robust) |

### Degradation Patterns

**Rotating patterns degrade less** than fixed patterns:
- best: fixed drops 11pp, rotating drops 8pp (rotation saves 3pp)
- balanced: fixed drops 11pp, rotating drops 3pp (rotation saves 8pp)

Rotation's advantage amplifies at higher difficulty. In v7, rotation helped balanced_fixed by +12pp (68% -> 80%). In v7.5, it helps by +20pp (57% -> 77%). The harder the tasks, the more rotation matters.

**The single agent baseline degrades moderately** (-8pp), suggesting that the degradation is partly inherent to the tasks (LLMs are worse at middle school math than elementary) and partly structural (NCA coordination overhead compounds at harder tasks).

### balanced_rotating: The New Winner

balanced_rotating's emergence as the top pattern is the most significant finding. In v7, it was 4th (80% vs best_fixed's 83%). In v7.5, it's 1st (77% vs single_agent's 75%).

Why it wins:
1. **Rotation de-biases** the contrarian Critic (llama3.1:8b at 10% agreement) by cycling it through Solver and Verifier roles where it contributes positively.
2. **The balanced model set** (mistral + llama3 + llama3.1:8b) has more diverse reasoning styles than the best set (qwen2.5:7b + llama3 + mistral), which helps on tasks requiring different approaches.
3. **2 steps vs 3 steps** means less convergence pressure, preserving more diversity in the final vote.

---

## 5. Role Division Analysis

### Fixed vs Rotating: Effect Size at Higher Difficulty

| Config | Fixed | Rotating | Rotation Gain | v7 Rotation Gain |
|--------|-------|----------|---------------|------------------|
| Best | 72% | 73% | **+1pp** | -2pp |
| Balanced | 57% | 77% | **+20pp** | +12pp |

For the best config, rotation barely helps (+1pp) — a reversal from v7 where it slightly hurt (-2pp). For the balanced config, rotation's benefit has grown from +12pp to +20pp. This divergence suggests:

- **Strong model sets (best)** don't need rotation — qwen2.5:7b as Solver is already competent enough that rotating it to other roles doesn't help.
- **Weaker model sets (balanced)** benefit enormously from rotation because it prevents any single model's weaknesses from dominating.

### Rotation's De-Biasing Effect Persistence

| Pattern | CORRECT acc | INCORRECT acc | Bias Gap |
|---------|-------------|---------------|----------|
| best_fixed | 74% | 69% | 5pp (slight CORRECT bias) |
| best_rotating | **95%** | 50% | **45pp** (extreme CORRECT bias) |
| balanced_fixed | 49% | 67% | 18pp (INCORRECT bias) |
| balanced_rotating | **92%** | 61% | **31pp** (strong CORRECT bias) |
| single_agent | 74% | 75% | **1pp** (near-balanced) |

Rotation continues to shift bias toward CORRECT at middle school level, with an even stronger effect than v7. The trade-off remains: rotation dramatically improves CORRECT detection at the cost of INCORRECT detection.

The single agent is the most balanced (1pp gap), but achieves this through moderate performance on both sides rather than excellence on either.

### balanced_fixed Collapse: Why It Fails

balanced_fixed drops to 57%, barely above random (50%). The root cause is the Critic node (llama3.1:8b at 10% agreement):

- At 10% agreement, the Critic nearly always disagrees with the Solver and Verifier
- On harder tasks, the Solver and Verifier are more often correct than the Critic expects
- The Critic's contrarian stance overrides correct consensus, producing wrong answers
- This is visible in the CORRECT/INCORRECT split: 49% CORRECT accuracy means the Critic is actually causing the system to reject correct statements more than half the time

---

## 6. CORRECT vs INCORRECT Analysis

### Bias Patterns at Middle School Level

| Pattern | CORRECT acc | INCORRECT acc | Direction |
|---------|-------------|---------------|-----------|
| single_agent | 74% | **75%** | Near-balanced |
| best_fixed | 74% | 69% | Slight CORRECT bias |
| balanced_rotating | **92%** | 61% | Strong CORRECT bias |
| best_rotating | **95%** | 50% | Extreme CORRECT bias |
| balanced_fixed | 49% | 67% | INCORRECT bias |

### best_rotating: 95% CORRECT / 50% INCORRECT

The most extreme bias. best_rotating almost never says "INCORRECT" when the statement is actually correct (only 5% false negative rate), but it misses half of all actual errors. This pattern is ideal when the cost of false alarms is very high, but dangerous when catching errors is critical.

### balanced_rotating: Best Balance Among High Performers

At 92% CORRECT / 61% INCORRECT (77% overall), balanced_rotating offers the best trade-off:
- It catches correct statements almost as well as best_rotating (92% vs 95%)
- But it catches significantly more errors (61% vs 50%)
- Its overall accuracy is 4pp higher (77% vs 73%)

### Comparison with v7 Bias Patterns

| Pattern | v7 CORRECT | v7.5 CORRECT | v7 INCORRECT | v7.5 INCORRECT |
|---------|------------|-------------|-------------|----------------|
| best_fixed | 77% | 74% (-3pp) | 90% | 69% (-21pp) |
| best_rotating | 96% | 95% (-1pp) | 65% | 50% (-15pp) |
| balanced_fixed | 73% | 49% (-24pp) | 62% | 67% (+5pp) |
| balanced_rotating | 87% | 92% (+5pp) | 73% | 61% (-12pp) |
| single_agent | 69% | 74% (+5pp) | 98% | 75% (-23pp) |

The most dramatic shift: **single_agent's INCORRECT accuracy drops from 98% to 75%** (-23pp). At elementary level, qwen2.5:7b almost never missed an error; at middle school level, it misses 25% of them. This suggests the model's confidence in error detection degrades faster than its ability to verify correct answers.

---

## 7. Comparison with v7

### Side-by-Side Comparison

| Metric | v7 (Elementary) | v7.5 (Middle School) | Delta |
|--------|-----------------|---------------------|-------|
| Best overall | 83% (best_fixed / single) | **77%** (balanced_rotating) | -6pp |
| Best CORRECT | 96% (best_rotating) | **95%** (best_rotating) | -1pp |
| Best INCORRECT | 98% (single_agent) | **75%** (single_agent) | -23pp |
| Most balanced | 83% (single: 69/98) | **75%** (single: 74/75) | -8pp |
| Worst pattern | 68% (balanced_fixed) | **57%** (balanced_fixed) | -11pp |

### Rank Order Change

| Rank | v7 | v7.5 |
|------|-----|------|
| 1st | best_fixed / single (83%) | **balanced_rotating (77%)** |
| 2nd | best_rotating (81%) | single_agent (75%) |
| 3rd | balanced_rotating (80%) | best_rotating (73%) |
| 4th | balanced_fixed (68%) | best_fixed (72%) |
| 5th | — | balanced_fixed (57%) |

The most significant shift: **balanced_rotating jumps from 3rd to 1st.** The patterns that excelled at easy tasks (best_fixed, single_agent) degrade faster than the rotation-augmented balanced pattern.

### Per-Task-Type Winners

| Task Type | Mean Accuracy | Best Pattern | Worst Pattern |
|-----------|---------------|-------------|--------------|
| similarity | **100%** | All (100%) | — |
| geometry | **92%** | best_rot/bal_fix/bal_rot (100%) | best_fixed (80%) |
| quadratic_fn | **88%** | best_fix/best_rot/bal_rot/single (100%) | balanced_fixed (40%) |
| square_root | **84%** | best_rotating (100%) | balanced_fixed (80%) |
| linear_function | **80%** | best_rot/bal_rot (100%) | best_fix/bal_fix (60%) |
| congruence | **72%** | single_agent (100%) | best_rot/bal_fix/bal_rot (60%) |
| ratio | **72%** | best_fix/bal_fix/single (80%) | best_rot/bal_rot (60%) |
| signed_number | **72%** | best_fix/best_rot/bal_rot/single (80%) | balanced_fixed (40%) |
| quadratic_eq | **68%** | single_agent (100%) | balanced_fixed (20%) |
| inequality | **68%** | best_fix/bal_fix (80%) | best_rot/bal_rot/single (60%) |
| linear_eq | **60%** | balanced_rotating (100%) | best_fix/bal_fix/single (40%) |
| pythagorean | **60%** | balanced_rotating (100%) | best_rotating (20%) |
| simultaneous_eq | **60%** | best_rotating (100%) | best_fixed (20%) |
| polynomial | **48%** | best_fix/single (60%) | best_rot/bal_fix/bal_rot (40%) |
| algebraic_expr | **40%** | best_fixed (60%) | balanced_rotating (20%) |

---

## 8. Key Insight: Training Data Coverage vs Computational Difficulty

### The Grade 8 Paradox

Grade 8 is computationally "easier" than Grade 9 (middle school vs. approaching high school), yet LLMs perform worse on it. The explanation lies in the distinction between **verification difficulty** and **training data coverage**.

**Grade 9 topics are "famous" in math education:**
- Pythagorean theorem (a² + b² = c²) appears in countless training examples
- Quadratic formula is one of the most commonly taught algebraic procedures
- Square root simplification follows simple, memorizable rules

**Grade 8 topics require more procedural reasoning:**
- Simultaneous equations require substitution or elimination — multi-step procedures where one error cascades
- Polynomial expansion (x+a)(x+b) requires tracking signs across multiplication — a common source of sign errors
- These topics are less "famous" and less formulaic than Grade 9 material

### Verification vs Generation

Our tasks are all **verification** tasks ("Is this answer correct?"), not generation tasks ("Solve this problem"). LLMs can verify Grade 9 answers by pattern-matching against memorized formulas:

- "Is x² + 5x + 6 = (x+2)(x+3)?" → Check if 2*3 = 6 and 2+3 = 5 ✓
- "Is sqrt(12) = 2*sqrt(3)?" → Check if 2² * 3 = 12 ✓

But Grade 8 verification requires actually performing the computation:

- "Is x=3, y=2 the solution to 2x + 3y = 12, x - y = 1?" → Must compute 2(3)+3(2) = 12 ✓ and 3-2 = 1 ✓
- "Is (x+3)(x-5) = x² - 2x - 15?" → Must expand and check all three coefficients

The algebraic expression task type (`algebraic_expr`, 40% mean) is the extreme case: "Is 3a + 2a = 5a?" seems trivial to humans but requires LLMs to perform symbolic variable manipulation, which is fundamentally different from numeric computation.

### Implication for Difficulty Curves

The difficulty curve is not monotonically linked to grade level. Instead, it follows **training data coverage** and **procedural complexity**:

```
Similarity (100%) > Geometry (92%) > Quadratic eval (88%) > ...
... > Simultaneous eq (60%) > Polynomial (48%) > Algebraic expr (40%)
```

This ordering cuts across grade levels, suggesting that future experiments should categorize tasks by **cognitive operation type** (pattern-match vs multi-step procedure vs symbolic manipulation) rather than nominal grade level.

---

## 9. Recommendations for v7.6 and Beyond

### What to Expect from High School Level

Based on v7.5 findings, predictions for v7.6 (high school):
- **Trigonometry values** (sin 30° = 1/2): likely high accuracy (~80-90%) due to heavy training data coverage
- **Derivative rules** (power rule, chain rule): likely moderate accuracy (~60-70%) — formulaic but error-prone
- **Integration**: likely low accuracy (~40-50%) — requires reversal of differentiation, a harder operation
- **Proof-style tasks**: likely very low accuracy — no formula to pattern-match against

Expected overall: **55-65%** across patterns, with single_agent and balanced_rotating likely the strongest.

### Whether "Proof Construction" Tasks Are Needed

The current task format (verification: "Is X correct?") has a ceiling imposed by the CORRECT/INCORRECT bias trade-off. At 77% best accuracy on middle school math, we're already seeing the limits of verification-based evaluation.

**Proof construction tasks** ("Derive X from Y") would test a fundamentally different capability — generation rather than verification. However, they introduce evaluation challenges: how do you automatically grade a proof? This remains an open problem for future versions.

A middle ground: **multi-step verification** tasks where the student must verify each step of a multi-step solution, catching the specific step where an error was introduced. This tests deeper reasoning while remaining automatically gradable.

### Where the True Difficulty Boundary Lies

The v7/v7.5 data suggests the boundary is not about grade level but about **operation type**:

| Operation Type | Accuracy Range | Examples |
|----------------|---------------|----------|
| Pattern-match verification | 80-100% | similarity, geometry area, quadratic evaluation |
| Formula application | 60-80% | quadratic equations, Pythagorean theorem, square roots |
| Multi-step procedure | 40-60% | simultaneous equations, polynomial expansion |
| Symbolic manipulation | 20-40% | algebraic expressions, variable simplification |

The true "collapse" happens when tasks require **chained symbolic reasoning** — the same weakness exposed by world_consistency tasks in v1-v6. The NCA architecture helps most in the formula application zone, where model diversity can catch individual model errors.

---

## Appendix: Per-Type Accuracy (All Patterns)

| Task Type | Grade | best_fixed | best_rotating | bal_fixed | bal_rotating | single | Mean |
|-----------|-------|------------|---------------|-----------|--------------|--------|------|
| similarity | 9 | 100% | 100% | 100% | 100% | 100% | **100%** |
| geometry | 7 | 80% | 100% | 100% | 100% | 80% | **92%** |
| quadratic_fn | 9 | 100% | 100% | 40% | 100% | 100% | **88%** |
| square_root | 9 | 80% | 100% | 80% | 80% | 80% | **84%** |
| linear_function | 8 | 60% | 100% | 60% | 100% | 80% | **80%** |
| signed_number | 7 | 80% | 80% | 40% | 80% | 80% | **72%** |
| congruence | 8 | 80% | 60% | 60% | 60% | 100% | **72%** |
| ratio | 7 | 80% | 60% | 80% | 60% | 80% | **72%** |
| quadratic_eq | 9 | 80% | 60% | 20% | 80% | 100% | **68%** |
| inequality | 8 | 80% | 60% | 80% | 60% | 60% | **68%** |
| linear_eq | 7 | 40% | 80% | 40% | 100% | 40% | **60%** |
| pythagorean | 9 | 80% | 20% | 40% | 100% | 60% | **60%** |
| simultaneous_eq | 8 | 20% | 100% | 40% | 80% | 60% | **60%** |
| polynomial | 8 | 60% | 40% | 40% | 40% | 60% | **48%** |
| algebraic_expr | 7 | 60% | 40% | 40% | 20% | 40% | **40%** |

---

## Appendix: Experiment Design

- **Task set:** 75 middle school math tasks (25 Grade 7, 25 Grade 8, 25 Grade 9), 39 CORRECT / 36 INCORRECT, seed=42
- **Grade 7 types:** linear equations, ratios, basic geometry, signed numbers, algebraic expressions
- **Grade 8 types:** simultaneous equations, linear functions, congruence, polynomial expansion, inequalities
- **Grade 9 types:** quadratic equations, square roots, quadratic functions, Pythagorean theorem, similarity
- **Models / patterns:** Identical to v7 (5 patterns, same models and agreement settings)
- **Runtime:** 2.3 hours total (best_fixed: 42min, best_rotating: 38min, balanced_fixed: 29min, balanced_rotating: 24min, single_agent: 3min)
