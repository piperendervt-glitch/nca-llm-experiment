# NCA v9a Experiment Report: MetaAgent-Only Addition

> One-variable experiment: best_fixed + MetaAgent (split-only intervention). All other parameters identical to best_fixed. 350 tasks across 4 task sets. MetaAgent uses qwen2.5:7b to arbitrate when the 3-node network disagrees.

---

## 1. Executive Summary

**Overall: 74.9% [70.0%, 79.3%] vs v8 adaptive 77% (-2pp, z=-0.618, p=0.54, not significant).**

MetaAgent had effectively zero impact on accuracy. On the 109 split decisions where it intervened, MetaAgent achieved 56.9% accuracy vs majority voting at 57.8% --- a net impact of **-1 task** (p=0.89). The -2pp gap vs v8 is fully explained by the absence of adaptive routing, not by MetaAgent's aggregation.

### Key Findings

- **MetaAgent does not break the 65% ceiling.** Split tasks (where MetaAgent intervenes) have 56.9% accuracy regardless of aggregation method. The ceiling is knowledge-based, not aggregation-based.
- **The -2pp vs v8 is a routing effect, not a MetaAgent effect.** v9a uses best_fixed uniformly; v8 routes easy tasks to single_agent and hard tasks to balanced_rotating. This separation --- validated in v7-v7.6 --- accounts for the gap.
- **world_consistency bias reversal.** best_fixed produces CORRECT 52% / INCORRECT 86%, the exact mirror of v8's balanced_rotating profile (94% / 38%). Changing the aggregation pattern flips the bias direction, confirming the v6 mirror effect.
- **MetaAgent overrides are coin flips.** Of 61 cases where MetaAgent overrode the majority, 30 were correct and 31 were wrong (49.2% accuracy). The MetaAgent has no edge over majority voting.

---

## 2. Full Results Table

| Task Set | v9a | 95% CI | v8 | Diff | z | p |
|----------|-----|--------|----|------|---|---|
| world_consistency | **69.0%** | [59.0%, 77.9%] | 66% | +3pp | 0.453 | 0.651 (n.s.) |
| math_elementary | 81.0% | [71.9%, 88.2%] | **85%** | -4pp | -0.753 | 0.452 (n.s.) |
| math_middle | 73.3% | [61.9%, 82.9%] | **76%** | -3pp | -0.375 | 0.707 (n.s.) |
| math_high | 76.0% | [64.7%, 85.1%] | **81%** | -5pp | -0.797 | 0.425 (n.s.) |
| **Overall** | **74.9%** | **[70.0%, 79.3%]** | **77%** | **-2pp** | **-0.618** | **0.536 (n.s.)** |

### CORRECT vs INCORRECT Accuracy

| Task Set | CORRECT acc | INCORRECT acc | v8 CORRECT | v8 INCORRECT |
|----------|-------------|---------------|------------|--------------|
| world_consistency | 52% | **86%** | **94%** | 38% |
| math_elementary | 69% | **94%** | 75% | 96% |
| math_middle | 72% | **75%** | 82% | 69% |
| math_high | 64% | **89%** | 90% | 72% |

All differences are statistically non-significant (all p > 0.4). The wide confidence intervals (typical range ~20pp) reflect sample sizes of 75-100 per task set.

---

## 3. MetaAgent Intervention Analysis

### Overview

| Metric | Value |
|--------|-------|
| Total interventions | 109 / 350 (31%) |
| Intervention accuracy | 56.9% [47.0%, 66.3%] |
| Majority-only accuracy (same 109 tasks) | 57.8% [48.0%, 67.2%] |
| MetaAgent net impact | **-1 task** (-0.3pp on overall) |
| MetaAgent vs majority (z-test) | z=-0.137, p=0.891 (n.s.) |

### Vote Distribution on Split Decisions

| Vote Pattern | N | MetaAgent acc | Majority acc |
|-------------|---|---------------|--------------|
| 2 CORRECT : 1 INCORRECT | 60 | 53.3% | 56.7% |
| 1 CORRECT : 2 INCORRECT | 49 | 61.2% | 59.2% |

MetaAgent performs marginally worse than majority on 2:1 CORRECT splits and marginally better on 1:2 INCORRECT splits. Neither difference is meaningful.

### MetaAgent Override Analysis

When MetaAgent disagreed with the majority vote:

| Metric | Value |
|--------|-------|
| Overrides (MetaAgent != majority) | 61 / 109 (56%) |
| Override correct | 30 |
| Override wrong | 31 |
| **Override accuracy** | **49.2%** (worse than random) |

The high override rate (56%) indicates MetaAgent frequently disagrees with majority --- but its overrides are essentially coin flips. This is the core failure: MetaAgent does not have access to better information than the nodes it is arbitrating.

### Per-Task-Set Intervention Breakdown

| Task Set | Interventions | Rate | Meta acc | Majority acc | Overrides | Override acc |
|----------|--------------|------|----------|-------------|-----------|-------------|
| world_consistency | 57 / 100 | **57%** | 61.4% | 59.6% | 27 | 51.9% |
| math_elementary | 20 / 100 | 20% | 45.0% | 50.0% | 13 | 46.2% |
| math_middle | 14 / 75 | 19% | 57.1% | 71.4% | 8 | 37.5% |
| math_high | 18 / 75 | 24% | 55.6% | 50.0% | 13 | 53.8% |

world_consistency has the highest intervention rate (57%) because best_fixed frequently produces split decisions on semantic reasoning tasks. Math tasks produce more unanimous decisions and thus fewer MetaAgent interventions.

### Why MetaAgent Cannot Break the 65% Ceiling

The 65% ceiling on hard tasks is a **knowledge ceiling**, not an aggregation ceiling:

1. Split decisions occur when models are genuinely uncertain about the answer.
2. MetaAgent uses the same model family (qwen2.5:7b) and sees the same reasoning.
3. When all three nodes lack the knowledge to solve a task, a fourth call to the same model family cannot manufacture that knowledge.
4. The override accuracy of 49.2% confirms: MetaAgent has no information advantage over the nodes.

---

## 4. The Routing Effect (Key Finding)

### Why v9a is -2pp Below v8

v9a uses best_fixed uniformly for all 350 tasks. v8 uses adaptive routing:

| Difficulty | v8 Route | v8 Accuracy | v9a Route | v9a Accuracy |
|------------|----------|-------------|-----------|--------------|
| Easy (50 tasks) | single_agent | 86% | best_fixed | best_fixed uniform |
| Medium (150 tasks) | best_fixed | 85% | best_fixed | best_fixed uniform |
| Hard (150 tasks) | balanced_rotating | 65% | best_fixed | best_fixed uniform |

v8's advantage comes from routing easy tasks to single_agent (86% accuracy) rather than running the full 3-node debate (which adds noise on simple tasks). The -2pp is entirely attributable to this routing, not to any MetaAgent effect.

### Experimental Decomposition

| Factor | Effect | Evidence |
|--------|--------|----------|
| Adaptive routing (v8) | +2pp | v8 77% vs v9a 75% |
| MetaAgent aggregation | ~0pp | MetaAgent acc = majority acc on splits, p=0.89 |
| Combined | Net -2pp | Routing gain missing, MetaAgent adds nothing |

**Implication**: v8's +2pp over best-fixed baseline was driven entirely by routing, not by coordination quality. This reframes the value of the v7-v7.6 difficulty classification: it is genuinely useful for routing, but the coordination patterns themselves cannot be improved through better aggregation alone.

---

## 5. world_consistency Bias Reversal

### The Mirror Effect Extended

| Metric | v8 (balanced_rotating) | v9a (best_fixed + MetaAgent) | v6 Trial 16 |
|--------|------------------------|------------------------------|-------------|
| Overall | 66% | **69%** | 63% |
| CORRECT acc | **94%** | 52% | 30% |
| INCORRECT acc | 38% | **86%** | **96%** |
| Bias direction | CONSISTENT | CONTRADICTION | CONTRADICTION |

Changing the aggregation pattern from balanced_rotating to best_fixed reverses the bias direction completely:

- **balanced_rotating** (v8): Consensus pressure from rotating roles drives toward "CORRECT" --- 94% CORRECT but only 38% INCORRECT.
- **best_fixed** (v9a): Fixed roles with the Solver at low agreement (30%) creates a dissenter effect that drives toward "INCORRECT" --- 86% INCORRECT but only 52% CORRECT.

### MetaAgent Intervention by Label (world_consistency)

| Ground Truth | N | Meta Interventions | Meta acc | Non-meta acc |
|-------------|---|-------------------|----------|-------------|
| CORRECT (label=True) | 50 | 27 (54%) | 33.3% | 73.9% |
| INCORRECT (label=False) | 50 | 30 (60%) | 86.7% | 85.0% |

On CORRECT tasks, MetaAgent intervention **hurts** --- 33.3% accuracy when intervening vs 73.9% when unanimous. The MetaAgent inherits best_fixed's CONTRADICTION bias and amplifies it on uncertain CORRECT tasks.

### Connection to Prior Findings

This extends the bias pattern observed across all versions:

| Version | Pattern | CORRECT acc | INCORRECT acc | Dominant Bias |
|---------|---------|-------------|---------------|---------------|
| v1-v5 | Various | 20-40% | 80-96% | CONTRADICTION |
| v6 Trial 16 | Fixed (30,80,80) | 30% | 96% | CONTRADICTION |
| v6 Trial 29 | Fixed (80,70,10) | 62% | 58% | Balanced |
| v8 | balanced_rotating | 94% | 38% | CONSISTENT |
| **v9a** | **best_fixed + MetaAgent** | **52%** | **86%** | **CONTRADICTION** |

The bias is a property of the aggregation pattern, not the task. MetaAgent cannot neutralize it because it inherits the same bias through the node outputs it reviews.

---

## 6. Hard Task Ceiling Analysis

### Unanimous vs Split Accuracy

| Task Set | Unanimous acc (N) | Split acc (N) | Gap |
|----------|-------------------|---------------|-----|
| world_consistency | 79.1% (43) | 61.4% (57) | -18pp |
| math_elementary | 90.0% (80) | 45.0% (20) | -45pp |
| math_middle | 77.0% (61) | 57.1% (14) | -20pp |
| math_high | 82.5% (57) | 55.6% (18) | -27pp |
| **Overall** | **84.2% (241)** | **56.9% (109)** | **-27pp** |

Unanimous decisions are dramatically more accurate than split decisions across all task sets. This 27pp gap confirms: when models agree, they are almost always right. When they disagree, accuracy drops to near-chance.

### Groupthink Distribution

| Groupthink | N | Accuracy | MetaAgent Interventions |
|------------|---|----------|------------------------|
| all_correct | 117 | 86.3% | 0 |
| all_incorrect | 124 | 79.8% | 0 |
| split | 109 | 56.9% | **109** (100%) |

The split tasks are where the ceiling lives. MetaAgent intervenes on exactly these tasks and achieves 56.9% --- no better than majority voting (57.8%). The ceiling is defined by the boundary between "tasks all models can handle" and "tasks that exceed model capability."

### Why the Ceiling Cannot Be Broken by Aggregation

The 65% hard ceiling (from v8) and the 57% split ceiling (from v9a) are manifestations of the same phenomenon:

1. **If models know the answer**, they agree (unanimous) and accuracy is 84%.
2. **If models don't know the answer**, they disagree (split) and accuracy is ~57%.
3. No aggregation strategy --- majority, confidence-weighted, or MetaAgent --- can exceed ~57% on split tasks because the information needed to decide correctly is not present in the model outputs.

Breaking the ceiling requires either:
- **Better models** (larger, more capable) that convert some split tasks to unanimous
- **Different information sources** (retrieval, tools, chain-of-thought forcing) that provide the missing knowledge
- **Task-specific architectures** that exploit domain structure rather than generic debate

---

## 7. Comparison with v1-v8 Trajectory

### world_consistency Performance

| Version | Architecture | Overall | CORRECT | INCORRECT | Key Change |
|---------|-------------|---------|---------|-----------|------------|
| v1 | Simple NCA (3 nodes) | 45% | ~20% | ~70% | Baseline |
| v2 | Agreement tuning | 49% | ~25% | ~73% | +agreement_pct |
| v3 | 4-node expansion | 55% | ~30% | ~80% | +1 node |
| v4 | Model selection | 53% | ~28% | ~78% | Best model combos |
| v5 | Optimized 3-node | 61% | ~35% | ~87% | Pruned to 3 |
| v6 | Random sampling (100 trials) | 63% | 30% | 96% | Systematic search |
| v8 | Adaptive routing | 66% | 94% | 38% | Difficulty routing |
| **v9a** | **best_fixed + MetaAgent** | **69%** | **52%** | **86%** | **+MetaAgent** |

### Math Performance (v7 Series + v8/v9a)

| Version | Task Set | Overall | Key Change |
|---------|----------|---------|------------|
| v7 | Elementary | 83% | Role-division NCA |
| v7.5 | Middle school | 77% | Same patterns, harder tasks |
| v7.6 | High school | 77% | Same patterns, hardest tasks |
| v8 | All combined | 77% | Adaptive routing |
| **v9a** | **All combined** | **75%** | **Uniform best_fixed + MetaAgent** |

### Overall Trajectory on world_consistency

45% -> 49% -> 55% -> 53% -> 61% -> 63% -> 66% -> **69%**

v9a's 69% on world_consistency is the highest ever, but this reflects best_fixed's CONTRADICTION bias being more profitable than balanced_rotating's CONSISTENT bias on a 50/50 dataset --- not a genuine capability improvement.

---

## 8. Implications for v9b and v9c

### v9b: Dynamic Confidence Weighting

v9b proposes weighting each model's vote by historical accuracy on similar task types. Based on v9a findings:

**Prognosis: Likely limited effect.**

- Dynamic weighting is an aggregation improvement, same category as MetaAgent.
- v9a showed aggregation changes produce ~0pp improvement on split decisions.
- However, confidence weighting could help on **unanimous-but-wrong** cases (20% of all_correct and all_incorrect are wrong). If weighting can flip some of these, there is a potential 2-3pp gain.

**Recommendation**: Proceed, but set expectations at +1-2pp improvement at best. The ceiling on split tasks will remain.

### v9c: Antithesis Agent (Devil's Advocate)

v9c proposes adding a dedicated contrarian agent that argues against the majority. Based on v9a findings:

**Prognosis: Potentially addresses bias reversal.**

- The core problem revealed by v9a is that all aggregation patterns produce directional bias (CORRECT or INCORRECT).
- An antithesis agent could counterbalance the dominant bias by forcing consideration of the opposing view.
- For world_consistency specifically, combining best_fixed's INCORRECT detection (86%) with balanced_rotating's CORRECT detection (94%) via an antithesis mechanism could yield balanced accuracy.

**Recommendation**: v9c should target the bias balance problem, not the ceiling problem. A successful v9c would achieve ~70% CORRECT / ~70% INCORRECT on world_consistency (balanced), even if overall accuracy doesn't improve much.

### What "Success" Looks Like

| Version | Success Criterion | Rationale |
|---------|------------------|-----------|
| v9b | +1-2pp on overall, validated by p < 0.1 | Even small aggregation gains are real progress |
| v9c | Balanced CORRECT/INCORRECT within 10pp | Eliminating directional bias is more valuable than raw accuracy |
| v10+ | > 70% on hard/split tasks | Requires architectural change, not aggregation tuning |

---

## 9. Recommendations

### Should v9b Proceed as Planned?

**Yes, but with adjusted expectations.** v9a demonstrated that aggregation improvements have limited ceiling potential. v9b's confidence weighting should be tested because:

1. It targets a different failure mode (unanimous-but-wrong) than MetaAgent (split decisions).
2. The implementation cost is low (no additional LLM calls, just reweighting existing outputs).
3. Even +1pp would be additive to v8's routing gains.

### Revised Hypothesis for Breaking the 65% Ceiling

The v9a experiment falsifies the hypothesis that "better aggregation can break the hard task ceiling." The revised hypothesis:

**The ceiling is defined by the weakest-link capability of the model pool.** To raise it:

1. **Add a stronger model** (e.g., qwen2.5:14b or llama3:70b) --- even one capable model in the pool could convert split decisions to unanimous-correct.
2. **Task decomposition** --- break hard tasks into easier sub-tasks that fall below the ceiling individually.
3. **Retrieval augmentation** --- provide relevant reference material so models have the knowledge needed for hard tasks.

Aggregation strategies (MetaAgent, confidence weighting, antithesis agents) can only rearrange existing accuracy, not create new knowledge. Future versions should invest in **capability** rather than **coordination**.

---

## Appendix: Experimental Setup

- **Models**: qwen2.5:7b (Solver) + llama3:latest (Verifier) + mistral:7b (Critic)
- **Agreement**: [30, 80, 80] (Solver=dissenter, Verifier/Critic=conformist)
- **Steps**: 3 (fixed roles, sequential: Solver -> Verifier -> Critic)
- **MetaAgent**: qwen2.5:7b, intervenes on split decisions only
- **Tasks**: 350 total (100 world_consistency, 100 math_elementary, 75 math_middle, 75 math_high)
- **Baseline**: v8 adaptive routing (77% overall)
- **Runtime**: 3.2 hours (350 tasks, avg 33s/task)
- **Statistical tests**: Clopper-Pearson 95% CI, two-proportion z-test
