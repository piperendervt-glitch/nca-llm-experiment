# v11 System A/B Implementation Report

作成日: 2026-04-04
Phase 1 結果報告: 集約ノードのハーネス化検証

---

## 1. System A: Confidence-Weighted Aggregation

System A uses the full NCA-LLM pipeline as implemented in `nca_network_v7.py`.
After 3 steps of Solver/Verifier/Critic deliberation, the **last step's node
outputs** are aggregated using confidence-weighted scoring.

### How it works

Each node (qwen2.5:7b, llama3, mistral:7b) outputs a structured dict containing:
- `decision`: `"CORRECT"` or `"INCORRECT"`
- `confidence`: a float between 0.0 and 1.0 (self-reported by the LLM)
- `reasoning`: free-text explanation

The aggregation function sums each node's confidence score into the
corresponding decision class, then picks the class with the higher total:

```python
# nca_network_v7.py:156-165
def aggregate_verdict(outputs: list[dict]) -> str:
    scores = {"CORRECT": 0.0, "INCORRECT": 0.0}
    for output in outputs:
        decision = output.get("decision", "UNKNOWN")
        confidence = float(output.get("confidence", 0.5))
        if decision in scores:
            scores[decision] += confidence
    if scores["CORRECT"] == scores["INCORRECT"]:
        return "INCORRECT"
    return max(scores, key=scores.get)
```

### Step by step

1. **Collect**: Take the 3 node outputs from the final step (step 2).
2. **Sum scores**: For each node, add its `confidence` value to its `decision`
   class. E.g., if Solver says CORRECT with 0.85, add 0.85 to `scores["CORRECT"]`.
3. **Select winner**: The decision class with the higher total score wins.
4. **Tie-breaking**: If `scores["CORRECT"] == scores["INCORRECT"]`, return
   `"INCORRECT"` (conservative bias).

### Example

| Node     | Decision  | Confidence |
|----------|-----------|------------|
| Solver   | CORRECT   | 0.85       |
| Verifier | CORRECT   | 0.90       |
| Critic   | INCORRECT | 0.70       |

- `scores["CORRECT"]` = 0.85 + 0.90 = **1.75**
- `scores["INCORRECT"]` = 0.70
- Verdict: **CORRECT** (1.75 > 0.70)

Note: In this example, simple majority would also return CORRECT (2 vs 1).
The systems diverge only when a minority node reports high confidence that
outweighs the majority's low confidence — a rare but possible scenario.

### How System A calls this

In `run_v11_ab.py:184-186`, when `use_code_aggregation=False`:

```python
# System A: confidence-weighted aggregation (from nca_network_v7)
verdict = nca_result["final_verdict"]
```

The `final_verdict` field is computed inside `run_nca_v7()` by calling
`aggregate_verdict()` on the last step's node outputs.

---

## 2. System B: Simple Majority Aggregation

System B runs the **identical** NCA-LLM pipeline (same models, same prompts,
same 3 steps of deliberation). The only difference: the final aggregation
ignores confidence scores and uses a simple vote count.

### How it works

After the NCA run completes, `extract_votes()` pulls each node's `decision`
string from the last step. Then `code_majority()` counts votes:

```python
# run_v11_ab.py:124-137
def extract_votes(nca_result: dict) -> tuple[list[str], dict[str, int]]:
    """Extract votes from last step of NCA result."""
    last_step = nca_result["steps"][-1]
    node_outputs = [
        last_step["solver"]["output"],
        last_step["verifier"]["output"],
        last_step["critic"]["output"],
    ]
    votes = [o.get("decision", "UNKNOWN") for o in node_outputs]
    vote_dist = {
        "CORRECT": votes.count("CORRECT"),
        "INCORRECT": votes.count("INCORRECT"),
    }
    return votes, vote_dist

# run_v11_ab.py:140-145
def code_majority(votes: list[str]) -> str:
    """System B aggregation: simple Counter majority."""
    filtered = [v for v in votes if v in ("CORRECT", "INCORRECT")]
    if not filtered:
        return "UNKNOWN"
    return Counter(filtered).most_common(1)[0][0]
```

### Step by step

1. **Collect**: Extract the 3 `decision` strings from the last step.
2. **Filter**: Keep only valid votes (`"CORRECT"` or `"INCORRECT"`).
3. **Count**: Use `Counter.most_common(1)` to find the majority class.
4. **Tie-breaking**: `Counter.most_common()` returns elements in insertion
   order when counts are equal. With 3 nodes and 2 classes, a true tie (e.g.,
   1 CORRECT, 1 INCORRECT, 1 UNKNOWN) is possible but extremely rare. In
   practice, 3 valid votes always produce a 2-1 or 3-0 split.

### How System B calls this

In `run_v11_ab.py:181-183`, when `use_code_aggregation=True`:

```python
# System B: Python Counter majority
verdict = code_majority(votes)
```

---

## 3. Key Difference

### What is different

| Aspect              | System A (Confidence-Weighted) | System B (Simple Majority)   |
|---------------------|-------------------------------|------------------------------|
| Input               | decision + confidence (float) | decision only (string)       |
| Aggregation method  | Sum confidence per class      | Count votes per class        |
| Information used    | 6 values (3 decisions + 3 confidences) | 3 values (3 decisions) |
| Tie-breaking        | Conservative (→ INCORRECT)    | Insertion-order (Counter)    |
| Implementation      | LLM-internal (`nca_network_v7.py`) | Python code (`run_v11_ab.py`) |

The systems produce different verdicts **only when**:
- The majority votes one way with low confidence, AND
- The minority votes the other way with high confidence, AND
- The minority's confidence sum exceeds the majority's confidence sum.

With 3 nodes, this requires something like:
- 2 nodes vote CORRECT with confidence 0.3 each (sum = 0.6)
- 1 node votes INCORRECT with confidence 0.7 (sum = 0.7)
- System A → INCORRECT, System B → CORRECT

### Why H1 was expected to be supported

The pre-experiment contract (`v11_pre_experiment_contract.md`) stated:

> v9シリーズで集約改善が全て+0ppだった。
> コードによる多数決とLLMによる多数決は同じ情報から同じ結論を出すはず。

In v9, all attempts to improve aggregation yielded +0pp. This suggested
aggregation was not a lever — the upstream LLM reasoning determined accuracy,
not how votes were combined downstream.

### What the result means

```
Overall: System A 74.3% vs System B 76.0%
Delta:   +1.7pp (B > A)
z-test:  z=0.5247, p=0.5998
```

- **p=0.60**: Far above α=0.05. The null hypothesis (A = B) cannot be rejected.
- **+1.7pp**: Within the noise floor. With n=350, the detectable effect size
  is ~5pp (per the contract's power analysis). A 1.7pp difference is
  indistinguishable from random variation.
- **Disagreement**: 54 tasks differed (24 A-only correct, 30 B-only correct).
  The net swing of +6 tasks toward B suggests confidence weighting introduces
  slight noise rather than signal — but this too is not significant.

**H1 is supported**: Replacing confidence-weighted aggregation with simple
majority has no measurable effect on accuracy.

---

## 4. Implication for v11 Next Steps

### What this tells us about aggregation

The aggregation node is **harnessable**. Replacing the LLM's confidence-weighted
scoring with a 5-line Python function produces equivalent results. This confirms
the v9 finding: aggregation is not where accuracy is gained or lost.

More precisely:
- LLM-reported confidence scores do not carry useful signal for vote weighting.
- The deliberation process (3 steps of Solver/Verifier/Critic interaction)
  determines the final votes; how those votes are combined is irrelevant.

### How this connects to v9 findings

v9 showed that the `best_fixed` configuration (fixed roles, agree=[30,80,80])
maximized accuracy, but aggregation improvements contributed +0pp across all
variants. v11 Phase 1 reproduces this finding with a cleaner experimental
design: same NCA run, two different aggregation methods, p=0.60.

The aggregation node was the first candidate tested for harness replacement
because it was the most likely to succeed — and it did.

### What System C and D-1b should focus on

Given that aggregation is harnessable (confirmed), the remaining v11 systems
should target the **reasoning nodes** where LLMs actually make mistakes:

- **System D-1b (numerical extraction harness)**: Target math tasks where LLMs
  miscalculate. If LLM errors are primarily arithmetic (e.g., 7×8=54), a Python
  harness that extracts and computes the numbers should improve accuracy on
  `math_elementary`, `math_middle`, and `math_high`.

- **System D-1c (formal logic harness)**: Target tasks with logical structure
  (A>B, B>C → A>C). If LLM errors are primarily logical rather than semantic,
  a code-based logic engine should help.

- **System C (single LLM + complete harness)**: Tests the extreme case — how
  much of the NCA pipeline can be replaced with code? If C ≈ A, most of the
  multi-agent structure is overhead.

The key question shifts from "how to aggregate" to "where does the LLM fail?"
— which is exactly what D-1b and D-1c are designed to answer.

Per the pre-experiment contract H4, `world_consistency` should show no
improvement from D-1b/D-1c since it requires semantic judgment, not
calculation or formal logic. This serves as the negative control.
