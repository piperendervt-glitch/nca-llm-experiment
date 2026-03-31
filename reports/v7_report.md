# NCA v7 Experiment Report: Math Tasks with Role-Division NCA

> 4 role-division patterns (best/balanced x fixed/rotating) + single agent baseline, tested on 100 elementary math tasks (4 types x 25 each).

---

## 1. Executive Summary

**Best pattern:** `best_fixed` and `single_agent` tie at **83% overall accuracy**. The role-division NCA matches but does not surpass a single qwen2.5:7b agent on overall accuracy.

**Most balanced pattern:** `best_rotating` — **81% overall** with **96% CORRECT / 65% INCORRECT**, achieving the highest CORRECT accuracy of any pattern.

**Comparison:** v7 math accuracy (83%) far exceeds v6 world_consistency accuracy (63%), a +20pp gap. This confirms that LLMs are substantially better at verifiable math tasks than semantic contradiction detection.

### Key Findings

- **Role rotation is a powerful de-biasing mechanism.** Rotation boosts CORRECT accuracy by +14-19pp in both configurations, at the cost of -8 to -25pp on INCORRECT — it shifts bias from "everything is wrong" to "everything is right."
- **The single agent is a surprisingly strong baseline.** At 83%, qwen2.5:7b alone matches the best 3-model NCA, suggesting the overhead of multi-model coordination does not help on well-structured math tasks.
- **Logic tasks benefit most from rotation:** best_fixed scores 72% on logic but best_rotating hits 100% — a +28pp gain driven by rotation eliminating false-contradiction bias on consistent inequality chains.
- **The balanced config (mistral + llama3 + llama3.1:8b) transfers poorly to math** at 68% fixed, but rotation rescues it to 80% (+12pp). The v6 balanced config was optimized for world_consistency, not arithmetic.
- **Zero tasks are universally wrong** — every task is solved correctly by at least one pattern, demonstrating ensemble diversity.

---

## 2. Full Results Table

| Pattern | Models | Agree | Steps | Role | Overall | CORRECT | INCORRECT | Calc | Logic | Word | Seq |
|---------|--------|-------|-------|------|---------|---------|-----------|------|-------|------|-----|
| best_fixed | qwen2.5:7b + llama3 + mistral | [30,80,80] | 3 | fixed | **83%** | 77% | 90% | 92% | 72% | 92% | 76% |
| best_rotating | qwen2.5:7b + llama3 + mistral | [30,80,80] | 3 | rotating | 81% | **96%** | 65% | 92% | **100%** | 72% | 60% |
| balanced_fixed | mistral + llama3 + llama3.1:8b | [80,70,10] | 2 | fixed | 68% | 73% | 62% | 80% | 68% | 68% | 56% |
| balanced_rotating | mistral + llama3 + llama3.1:8b | [80,70,10] | 2 | rotating | 80% | 87% | 73% | 88% | 84% | 76% | 72% |
| single_agent | qwen2.5:7b | [100] | 1 | none | **83%** | 69% | **98%** | 76% | 84% | 84% | 88% |

### Groupthink Distribution

| Pattern | All CORRECT | All INCORRECT | Split |
|---------|-------------|---------------|-------|
| best_fixed | 34 | 46 | 20 |
| best_rotating | 45 | 26 | 29 |
| balanced_fixed | 40 | 30 | 30 |
| balanced_rotating | 46 | 25 | 29 |
| single_agent | — | — | — |

Rotation shifts groupthink direction: INCORRECT unanimity drops (46->26, 30->25) while CORRECT unanimity rises (34->45, 40->46). Split decisions also increase, indicating rotation preserves more disagreement.

---

## 3. Role Division Analysis

### Fixed vs Rotating: What Changes

| Metric | best_fixed | best_rotating | Delta |
|--------|------------|---------------|-------|
| Overall | 83% | 81% | -2pp |
| CORRECT acc | 77% | 96% | **+19pp** |
| INCORRECT acc | 90% | 65% | **-25pp** |
| Split decisions | 20 | 29 | +9 |

| Metric | balanced_fixed | balanced_rotating | Delta |
|--------|----------------|-------------------|-------|
| Overall | 68% | 80% | **+12pp** |
| CORRECT acc | 73% | 87% | **+14pp** |
| INCORRECT acc | 62% | 73% | **+11pp** |
| Split decisions | 30 | 29 | -1 |

### Rotation as a De-Biasing Mechanism

In fixed mode, roles are permanently assigned: qwen2.5:7b always solves, llama3 always verifies, mistral always critiques. This creates a **static information flow** where the Solver's initial bias propagates through the chain.

In rotating mode, each model takes every role across steps:
- Step 0: Node0=Solver, Node1=Verifier, Node2=Critic
- Step 1: Node1=Solver, Node2=Verifier, Node0=Critic
- Step 2: Node2=Solver, Node0=Verifier, Node1=Critic

This means:
1. **Each model solves independently** in one step, preventing a single model's bias from dominating.
2. **Each model critiques** the others, breaking sycophantic verification chains.
3. **Disagreements surface naturally** — if qwen2.5:7b solves differently from mistral, the next step's critic sees the conflict.

The effect is asymmetric: rotation dramatically boosts CORRECT detection (because it breaks the "default to INCORRECT" chain) but reduces INCORRECT detection (because more diverse opinions create more false negatives on actual errors).

For balanced config, rotation helps both directions (+14pp CORRECT, +11pp INCORRECT), suggesting it's especially beneficial when models are weaker individually — it compensates for individual model limitations.

### Which Task Types Benefit Most from Rotation

| Task Type | best_fixed | best_rotating | Delta |
|-----------|------------|---------------|-------|
| Calculation | 92% | 92% | 0pp |
| Logic | 72% | **100%** | **+28pp** |
| Word Problem | 92% | 72% | **-20pp** |
| Sequence | 76% | 60% | **-16pp** |

| Task Type | balanced_fixed | balanced_rotating | Delta |
|-----------|----------------|-------------------|-------|
| Calculation | 80% | 88% | +8pp |
| Logic | 68% | 84% | **+16pp** |
| Word Problem | 68% | 76% | +8pp |
| Sequence | 56% | 72% | **+16pp** |

**Logic benefits most from rotation** in both configs. This is because logic tasks (transitive inequality chains) have a strong false-contradiction bias in fixed mode — the Solver often wrongly flags consistent chains as contradictions, and the Verifier/Critic follow. Rotation breaks this chain by letting different models solve independently.

For the best config, rotation hurts word problems (-20pp) and sequences (-16pp) because these INCORRECT-detection tasks lose accuracy when the bias shifts toward CORRECT.

---

## 4. Task Type Analysis

### Overall Performance by Task Type

| Task Type | best_fixed | best_rotating | bal_fixed | bal_rotating | single_agent | Mean |
|-----------|------------|---------------|-----------|--------------|--------------|------|
| Calculation | **92%** | **92%** | 80% | 88% | 76% | 85.6% |
| Logic | 72% | **100%** | 68% | 84% | 84% | 81.6% |
| Word Problem | **92%** | 72% | 68% | 76% | 84% | 78.4% |
| Sequence | 76% | 60% | 56% | 72% | **88%** | 70.4% |

### Difficulty Ranking (hardest to easiest, by mean)

1. **Sequence (70.4%)** — hardest. Pattern detection requires tracking multi-element relationships, and models struggle with corrupted geometric/Fibonacci sequences.
2. **Word Problem (78.4%)** — moderate. Natural language parsing adds a layer of complexity over raw calculation.
3. **Logic (81.6%)** — moderate. Transitive inequality reasoning is tricky but well-structured.
4. **Calculation (85.6%)** — easiest. Direct arithmetic verification is closest to LLM training data.

### Why Logic Benefits Most from Rotation (72% -> 100%)

The CORRECT/INCORRECT breakdown reveals the mechanism:

| Config | Logic CORRECT acc | Logic INCORRECT acc |
|--------|-------------------|---------------------|
| best_fixed | **46%** | 100% |
| best_rotating | **100%** | 100% |

In fixed mode, logic CORRECT accuracy is only 46% — the NCA correctly identifies all contradictions (100%) but misclassifies over half of consistent inequality chains as contradictions. This is because the fixed Solver (qwen2.5:7b) has a strong "find problems" bias on logic tasks, and the downstream Verifier/Critic follow.

Rotation eliminates this completely: 100% on both CORRECT and INCORRECT logic tasks, the only perfect score in the entire experiment. When each model gets to solve logic tasks independently and then critique others' work, the false-contradiction bias disappears.

---

## 5. Bias Analysis

### CORRECT vs INCORRECT Accuracy Gap

| Pattern | CORRECT acc | INCORRECT acc | Gap | Bias Direction |
|---------|-------------|---------------|-----|----------------|
| single_agent | 69% | **98%** | 29pp | Strong INCORRECT bias |
| best_fixed | 77% | 90% | 13pp | Moderate INCORRECT bias |
| best_rotating | **96%** | 65% | 31pp | Strong CORRECT bias |
| balanced_fixed | 73% | 62% | 11pp | Mild CORRECT bias |
| balanced_rotating | 87% | 73% | 14pp | Moderate CORRECT bias |

### Single Agent Bias

The single qwen2.5:7b agent shows the most extreme INCORRECT bias (69% vs 98%). It almost never misses an actual error (98%), but incorrectly flags 31% of correct statements as wrong. This mirrors the CONTRADICTION bias seen in v6 world_consistency — LLMs have a systematic tendency to "find problems" even when none exist.

### How Rotation Shifts Bias

Rotation consistently shifts bias toward CORRECT:
- best: 77%/90% -> 96%/65% (bias flips from INCORRECT to CORRECT)
- balanced: 73%/62% -> 87%/73% (strengthens existing CORRECT bias)

The mechanism: in fixed mode, the Solver's initial judgment dominates the pipeline. If the Solver leans INCORRECT, the Verifier and Critic follow. In rotating mode, each model solves independently in different steps, and models that lean CORRECT get equal influence. The result is a more CORRECT-leaning consensus.

**Implication:** Neither fixed nor rotating mode achieves unbiased classification. The ideal system would combine fixed mode's INCORRECT detection (90%) with rotating mode's CORRECT detection (96%), but no single configuration achieves both.

---

## 6. Model Configuration Analysis

### Best Config (qwen2.5:7b + llama3 + mistral)

This v6-optimal combination performs strongly on math:
- Fixed: 83% overall (77% CORRECT, 90% INCORRECT)
- Rotating: 81% overall (96% CORRECT, 65% INCORRECT)
- Calculation accuracy: 92% in both modes — the strongest task type

The agreement setting [30, 80, 80] gives qwen2.5:7b (Solver) low agreement (30%) — it maintains independent judgment even when neighbors disagree. The Verifier and Critic have high agreement (80%), meaning they tend to follow the majority. This creates a "strong independent solver + cooperative verification" dynamic.

### Balanced Config Transfer Failure

| Metric | v6 world_consistency | v7 math (fixed) | Delta |
|--------|---------------------|------------------|-------|
| Overall | 60% | 68% | +8pp |
| CORRECT/CONS | 62% | 73% | +11pp |
| INCORRECT/CONTR | 58% | 62% | +4pp |

The balanced config (mistral + llama3 + llama3.1:8b) was v6's most balanced trial at 60% overall. On math tasks it reaches 68% fixed / 80% rotating — better absolute numbers due to easier tasks, but still 15pp below the best config in fixed mode.

**Why it underperforms:** The balanced config uses llama3.1:8b with only 10% agreement as the Critic. On math tasks, this ultra-independent Critic often overrides correct Solver+Verifier consensus, introducing errors. The best config's [30,80,80] is better calibrated: the Solver thinks independently while the Critic is cooperative.

However, rotation rescues the balanced config dramatically (+12pp) because it ensures llama3.1:8b also gets to solve and verify, not just critique from its contrarian position.

### Single Agent Surprise

The single qwen2.5:7b agent matching the best 3-model NCA at 83% is notable. Possible explanations:

1. **Math tasks are well-structured** — there's less ambiguity than world_consistency, so a single model's reasoning is often sufficient.
2. **The NCA pipeline introduces error propagation** — the Solver's mistakes can pollute the Verifier and Critic.
3. **qwen2.5:7b is the strongest individual model** — its per-model average in v6 (52.9%) was already top-tier, and math plays to its quantitative strengths.

---

## 7. Comparison with Previous Versions

| Version | Task Domain | Overall | CORRECT/CONS | INCORRECT/CONTR | Key Innovation |
|---------|-------------|---------|-------------|-----------------|----------------|
| Fixed baseline | world_consistency | 45% | 2% | 88% | Sequential pipeline |
| NCA v1 | world_consistency | 49% | 0% | 98% | Baseline NCA |
| NCA v2 | world_consistency | 55% | 80% | 30% | Anti-sycophancy prompts |
| NCA v4 | world_consistency | 53% | 24% | 82% | Confidence weighting |
| NCA v5 best | world_consistency | 61% | 40% | 82% | Multi-model combos |
| NCA v6 best | world_consistency | 63% | 30% | 96% | Agreement + step tuning |
| NCA v6 balanced | world_consistency | 60% | 62% | 58% | Best balanced world_cons |
| **v7 best_fixed** | **math** | **83%** | 77% | 90% | Role-division (fixed) |
| **v7 best_rotating** | **math** | **81%** | **96%** | 65% | Role-division (rotating) |
| **v7 single_agent** | **math** | **83%** | 69% | 98% | Single model baseline |

**Cross-version trajectory on accuracy:** 45% -> 49% -> 55% -> 53% -> 61% -> 63% -> 83%

The v7 jump from 63% to 83% is the largest single-version improvement (+20pp), but **the comparison is not apples-to-apples**: v7 uses elementary math tasks while v1-v6 used world_consistency. The improvement reflects task difficulty more than architectural progress.

---

## 8. Key Insight: Math vs World_Consistency Gap

### The 20pp Gap

| Metric | v6 best (world_cons) | v7 best (math) | Delta |
|--------|---------------------|-----------------|-------|
| Overall | 63% | 83% | **+20pp** |
| CORRECT/CONS | 30% | 77% | **+47pp** |
| INCORRECT/CONTR | 96% | 90% | -6pp |

The gap is almost entirely in CORRECT/CONSISTENT accuracy. LLMs detect errors (INCORRECT/CONTRADICTION) at similar rates (90-98%) across both domains, but they are dramatically better at confirming correctness in math (77%) than in semantic consistency (30%).

### Connection to the External Verifier Argument

Math tasks have a key property that world_consistency tasks lack: **verifiability**. Given "3 x 7 = 21", a model can compute 3 x 7 independently and check whether the result matches. This is an internal verification step that LLMs can perform reliably.

World_consistency tasks ("The world rule says cats always land on their feet. Statement: A cat fell and landed on its back") require **semantic reasoning** about real-world knowledge, where LLMs lack a clear verification procedure and default to pattern-matching.

This supports the hypothesis that **NCA architectures are most effective when individual nodes can independently verify claims**, not just pattern-match. Future versions should explore tasks with intermediate verifiability (e.g., multi-step logic proofs) to map the accuracy frontier between pure computation and pure semantics.

### What This Tells Us About LLM Capabilities

1. **LLMs are strong calculators but weak semantic reasoners** — at least at the 3B-8B scale used here.
2. **The CONTRADICTION/INCORRECT bias is universal** — it appears in both math (69% CORRECT vs 98% INCORRECT for single agent) and world_consistency (30% CONSISTENT vs 96% CONTRADICTION for v6 best). LLMs prefer to find fault.
3. **Multi-model NCA helps more on ambiguous tasks** — the gap between single agent and best NCA is tiny on math (83% vs 83%) but substantial on world_consistency (single model ~52% vs NCA 63%). Coordination pays off when individual models are uncertain.

---

## 9. Recommendations for v8+

### Should Rotation Be Default?

**Yes, for balanced accuracy. No, for maximum overall accuracy.**

Rotation is the single most effective de-biasing technique discovered in this project. It consistently boosts CORRECT/CONSISTENT accuracy by 14-19pp. However, it does so at the expense of INCORRECT/CONTRADICTION accuracy.

**Recommendation:** Make rotation the default for new experiments, with a configurable option. For production use, the choice depends on the cost asymmetry: if false negatives (missing real errors) are costly, use fixed mode; if false positives (flagging correct items as wrong) are costly, use rotating mode.

### Configurations to Carry Forward

1. **best_rotating (qwen2.5:7b + llama3 + mistral, agree=[30,80,80], steps=3, rotating)** — Best CORRECT accuracy (96%), strong logic performance (100%), and a good template for de-biased reasoning.

2. **best_fixed (same models, fixed)** — Best overall accuracy (83%), strong INCORRECT detection (90%), and the simplest pipeline for deployment.

3. **balanced_rotating (mistral + llama3 + llama3.1:8b, agree=[80,70,10], steps=2, rotating)** — Surprisingly strong at 80% with a different model set. Demonstrates that rotation can rescue weaker configurations.

### Hypotheses About Adaptive Model Selection (v8)

1. **Task-type routing:** Route calculation tasks to fixed mode (where it's already 92%) and logic tasks to rotating mode (where it hits 100%). A simple task classifier could select the optimal mode per task.

2. **Adaptive step count:** Use fewer steps for easy tasks (calculations) and more for hard tasks (sequences, logic). v6 showed that step count is the dominant structural variable; v7 confirms that different task types have different optimal step counts.

3. **Confidence-based early stopping:** If all three nodes agree with high confidence after step 1, skip remaining steps. This would dramatically reduce runtime (from ~30s to ~10s per task) without sacrificing accuracy on easy tasks.

4. **Hybrid fixed+rotating:** Run step 0 in fixed mode (Solver -> Verifier -> Critic) then switch to rotating for subsequent steps. This gives the pipeline a strong initial signal while still benefiting from rotation's de-biasing effect.

5. **World_consistency re-test with rotation:** Apply v7's role-division architecture back to world_consistency tasks. If rotation boosts CONSISTENT accuracy on semantic tasks as much as it does on math (+19pp), it could push world_consistency accuracy beyond 70%.

---

## Appendix: Detailed Per-Type Per-Label Accuracy

### best_fixed

| Type | CORRECT acc (n) | INCORRECT acc (n) | Overall |
|------|-----------------|-------------------|---------|
| Calculation | 92% (13) | 92% (12) | 92% |
| Logic | 46% (13) | 100% (12) | 72% |
| Word Problem | 85% (13) | 100% (12) | 92% |
| Sequence | 85% (13) | 67% (12) | 76% |

### best_rotating

| Type | CORRECT acc (n) | INCORRECT acc (n) | Overall |
|------|-----------------|-------------------|---------|
| Calculation | 100% (13) | 83% (12) | 92% |
| Logic | 100% (13) | 100% (12) | **100%** |
| Word Problem | 85% (13) | 58% (12) | 72% |
| Sequence | 100% (13) | 17% (12) | 60% |

### balanced_fixed

| Type | CORRECT acc (n) | INCORRECT acc (n) | Overall |
|------|-----------------|-------------------|---------|
| Calculation | 69% (13) | 92% (12) | 80% |
| Logic | 38% (13) | 100% (12) | 68% |
| Word Problem | 85% (13) | 50% (12) | 68% |
| Sequence | 100% (13) | 8% (12) | 56% |

### balanced_rotating

| Type | CORRECT acc (n) | INCORRECT acc (n) | Overall |
|------|-----------------|-------------------|---------|
| Calculation | 77% (13) | 100% (12) | 88% |
| Logic | 100% (13) | 67% (12) | 84% |
| Word Problem | 85% (13) | 67% (12) | 76% |
| Sequence | 85% (13) | 58% (12) | 72% |

### single_agent

| Type | CORRECT acc (n) | INCORRECT acc (n) | Overall |
|------|-----------------|-------------------|---------|
| Calculation | 62% (13) | 92% (12) | 76% |
| Logic | 69% (13) | 100% (12) | 84% |
| Word Problem | 69% (13) | 100% (12) | 84% |
| Sequence | 77% (13) | 100% (12) | 88% |

### Rotation Fix/Break Analysis

- **best_rotating** fixes 10 tasks that best_fixed gets wrong, but breaks 12 tasks (net: -2)
- **balanced_rotating** fixes 24 tasks that balanced_fixed gets wrong, but breaks 12 tasks (net: +12)
- **Zero tasks are wrong across all 5 patterns** — every task is solved by at least one configuration

---

## Appendix: Experiment Design

- **Task set:** 100 elementary math tasks (25 calculation, 25 logic inequality, 25 word problems, 25 sequences), 52 CORRECT / 48 INCORRECT, seed=42
- **Models:** qwen2.5:7b, llama3:latest, mistral:7b, llama3.1:8b (from v6 top configs)
- **Role pipeline:** Solver -> Verifier -> Critic (sequential within each step)
- **Aggregation:** Confidence-weighted majority vote across all 3 node outputs
- **Runtime:** 2.7 hours total (best_fixed: 50min, best_rotating: 44min, balanced_fixed: 34min, balanced_rotating: 29min, single_agent: 3min)
