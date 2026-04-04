"""v10 CFR comparison analysis."""
import json
import math
from collections import defaultdict

# Load data - skip malformed lines
rows = []
with open("results/v10/v10_cfr_results.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # skip fragment lines

# Deduplicate by task_id (first occurrence)
seen = set()
unique = []
for r in rows:
    if r["task_id"] not in seen:
        seen.add(r["task_id"])
        unique.append(r)

# Group by task_set
groups = defaultdict(list)
for r in unique:
    groups[r["task_set"]].append(r)

# Clopper-Pearson CI
try:
    from scipy import stats as sp_stats
    def clopper_pearson(k, n, alpha=0.05):
        lo = sp_stats.beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
        hi = sp_stats.beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
        return lo, hi
    def norm_cdf(x):
        return sp_stats.norm.cdf(x)
except ImportError:
    def clopper_pearson(k, n, alpha=0.05):
        p = k / n if n > 0 else 0
        se = math.sqrt(p * (1 - p) / n) if n > 0 else 0
        return max(0, p - 1.96 * se), min(1, p + 1.96 * se)
    def norm_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

# Debug: show task_sets found
print(f"Total rows loaded: {len(rows)}, Unique tasks: {len(unique)}")
print(f"Task sets found: {sorted(groups.keys())}")
for ts in sorted(groups.keys()):
    print(f"  {ts}: {len(groups[ts])} tasks")

# Calculate metrics per task_set
results = {}
for ts in sorted(groups.keys()):
    tasks = groups[ts]
    n_total = len(tasks)
    n_unanimous = sum(1 for t in tasks if t["is_unanimous"])
    n_wrong_unanimous = sum(1 for t in tasks if t["is_unanimous"] and not t["is_correct"])
    cfr = n_wrong_unanimous / n_unanimous if n_unanimous > 0 else 0
    lo, hi = clopper_pearson(n_wrong_unanimous, n_unanimous)
    results[ts] = dict(
        n_total=n_total, n_unanimous=n_unanimous,
        n_wrong_unanimous=n_wrong_unanimous, cfr=cfr, ci_lo=lo, ci_hi=hi,
    )

# Two-proportion z-test
mid = results["math_middle"]
high = results["math_high"]
p1, n1, x1 = mid["cfr"], mid["n_unanimous"], mid["n_wrong_unanimous"]
p2, n2, x2 = high["cfr"], high["n_unanimous"], high["n_wrong_unanimous"]

p_pool = (x1 + x2) / (n1 + n2)
se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
z = (p1 - p2) / se if se > 0 else 0
p_value = 2 * (1 - norm_cdf(abs(z)))
sig = "YES" if p_value < 0.05 else "NO"

# Case
if p_value < 0.05 and p1 > p2:
    case = "A"
elif p_value >= 0.05:
    case = "B"
else:
    case = "C"

# Output
print()
print("=" * 64)
print("v10 CFR Comparison Results")
print("=" * 64)
header = f"{'Task Set':<13}| {'n_tasks':>7} | {'n_unani':>7} | {'n_wrong':>7} | {'CFR':>6} | 95% CI"
print(header)
print(f"{'-'*13}|{'-'*9}|{'-'*9}|{'-'*9}|{'-'*8}|{'-'*16}")
for ts in ["math_middle", "math_high"]:
    r = results[ts]
    ci_str = f"[{r['ci_lo']:.1%}, {r['ci_hi']:.1%}]"
    print(f"{ts:<13}| {r['n_total']:>7} | {r['n_unanimous']:>7} | {r['n_wrong_unanimous']:>7} | {r['cfr']:>5.1%} | {ci_str}")
print("=" * 64)
print(f"z-statistic: {z:.4f}")
print(f"p-value:     {p_value:.4f}")
print(f"Significant at alpha=0.05: {sig}")
print("=" * 64)
print("Comparison with v9d:")
print(f"  math_middle: v9d=27.4% -> v10={mid['cfr']:.1%}")
print(f"  math_high:   v9d=21.1% -> v10={high['cfr']:.1%}")
print("=" * 64)
print("Conclusion:")
print(f"  [{'X' if case == 'A' else ' '}] Case A: math_middle > math_high (confirmed)")
print(f"  [{'X' if case == 'B' else ' '}] Case B: No significant difference")
print(f"  [{'X' if case == 'C' else ' '}] Case C: Unexpected reversal")
print("=" * 64)

# Save summary
summary = {
    "experiment": "v10",
    "description": "CFR comparison: math_middle vs math_high (new task sets)",
    "results": results,
    "z_test": {"z_statistic": z, "p_value": p_value, "significant": bool(p_value < 0.05)},
    "v9d_comparison": {
        "math_middle": {"v9d": 0.274, "v10": mid["cfr"]},
        "math_high": {"v9d": 0.211, "v10": high["cfr"]},
    },
    "conclusion": f"Case {case}",
}

with open("results/v10/v10_summary.jsonl", "w", encoding="utf-8") as f:
    f.write(json.dumps(summary, ensure_ascii=False) + "\n")
print("\nSummary saved to results/v10/v10_summary.jsonl")
