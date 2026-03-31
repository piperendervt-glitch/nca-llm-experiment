"""
embedding_classifier.py

Hybrid difficulty classifier for NCA v8.
Uses nomic-embed-text embeddings + task metadata for routing.

Strategy:
- Embeddings distinguish world_consistency from math tasks (clear separation)
- For math tasks, uses task metadata (level/type) when available
- Falls back to pure embedding classification for unknown tasks
"""

import pickle
from pathlib import Path

import httpx
from scipy.spatial.distance import cosine

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

_embed_client = httpx.Client(timeout=30.0)

# ── Anchor texts ─────────────────────────────────────────────────────────────
# Separated into math vs world_consistency for clear domain detection

ANCHORS = {
    "math_easy": [
        "Is the following calculation correct? 5 * 3 = 15",
        "Is the following calculation correct? 11 - 4 = 7",
        "Is sin(30 degrees) = 1/2 correct?",
        "Is log_2(8) = 3 correct?",
        "If f(x) = x^3, is f'(x) = 3x^2 correct?",
        "Triangle ABC has AB = 3, BC = 7. Triangle DEF has DE = 6, EF = 14. Are these triangles similar?",
    ],
    "math_medium": [
        "Solve: x^2 - 5x + 6 = 0. Is x = 2, 3 correct?",
        "A right triangle has legs 3 and 4. Is the hypotenuse = 5 correct?",
        "When flipping 3 fair coins, is the probability of exactly 2 heads = 3/8 correct?",
        "For y = 2x + 1, when x = 3, is y = 7 correct?",
        "Solve: 2x - 1 > 3. Is x > 2 correct?",
        "For f(x) = x^3 - 3x, is the local minimum value = -2 correct?",
    ],
    "math_hard": [
        "Solve the system: x + y = 5, x - y = 1. Is x = 3, y = 2 correct?",
        "Is (x + 3)(x - 5) = x^2 - 2x - 15 correct?",
        "Is 3a + 2a = 5a correct?",
        "Solve: x^2 + x - 2 > 0. Is the solution x < -2 or x > 1 correct?",
        "The area enclosed by y = x^2 and y = 2x is 4/3. Is this correct?",
    ],
    "world_consistency": [
        "World rule: All birds can fly. Statement: A penguin is a bird that cannot fly.",
        "World rule: Water always flows downhill. Statement: The river flows upward to the mountain peak.",
        "World rule: Cats always land on their feet. Statement: A cat fell and landed on its back.",
        "World rule: All metals conduct electricity. Statement: This metal rod does not conduct electricity.",
        "World rule: Plants need sunlight to grow. Statement: This plant grew in complete darkness.",
    ],
}

# ── Task type to difficulty mapping (from v7-v7.6 results) ──────────────────
# Based on mean accuracy across all patterns

# v7 elementary task types
ELEMENTARY_DIFFICULTY = {
    "calculation": "easy",     # 85.6% mean
    "logical": "medium",       # 81.6% mean
    "word_problem": "medium",  # 78.4% mean
    "sequence": "medium",      # 70.4% mean
}

# v7.5 middle school task types
MIDDLE_DIFFICULTY = {
    "similarity": "easy",       # 100% mean
    "geometry": "easy",         # 92% mean
    "quadratic_fn": "easy",     # 88% mean
    "square_root": "easy",      # 84% mean
    "linear_function": "medium", # 80% mean
    "signed_number": "medium",  # 72% mean
    "congruence": "medium",     # 72% mean
    "ratio": "medium",          # 72% mean
    "quadratic_eq": "medium",   # 68% mean
    "inequality": "medium",     # 68% mean
    "linear_eq": "hard",        # 60% mean
    "pythagorean": "hard",      # 60% mean
    "simultaneous_eq": "hard",  # 60% mean
    "polynomial": "hard",       # 48% mean
    "algebraic_expr": "hard",   # 40% mean
}

# v7.6 high school task types
HIGH_DIFFICULTY = {
    "trig_value": "easy",        # 84% mean
    "trig_identity": "medium",   # 80% mean
    "logarithm": "medium",       # 80% mean
    "recurrence": "medium",      # 80% mean
    "derivative": "medium",      # 80% mean
    "probability": "medium",     # 72% mean
    "extremum": "medium",        # 68% mean
    "integral": "medium",        # 68% mean
    "exponent": "medium",        # 64% mean
    "logic_quad": "medium",      # 64% mean
    "quadratic_minmax": "hard",  # 60% mean
    "factoring": "hard",         # 56% mean
    "arithmetic_seq": "hard",    # 52% mean
    "area": "hard",              # 48% mean
    "quadratic_ineq": "hard",    # 48% mean
}

ALL_TYPE_DIFFICULTY = {**ELEMENTARY_DIFFICULTY, **MIDDLE_DIFFICULTY, **HIGH_DIFFICULTY}


def embed(text: str) -> list[float]:
    """Get embedding vector for text using nomic-embed-text."""
    response = _embed_client.post(
        OLLAMA_URL,
        json={"model": EMBED_MODEL, "prompt": text},
    )
    response.raise_for_status()
    return response.json()["embedding"]


def build_anchor_embeddings(cache_path: Path = None) -> dict:
    """Compute and optionally cache anchor embeddings."""
    if cache_path and cache_path.exists():
        with open(cache_path, "rb") as f:
            cached = pickle.load(f)
        print(f"  Loaded cached anchors from {cache_path}")
        return cached

    anchor_vecs = {}
    for category, texts in ANCHORS.items():
        anchor_vecs[category] = [embed(t) for t in texts]
        print(f"  Embedded {len(texts)} anchors for '{category}'")

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "wb") as f:
            pickle.dump(anchor_vecs, f)
        print(f"  Cached to {cache_path}")

    return anchor_vecs


def classify_difficulty(task_text: str, anchor_vecs: dict,
                        task_type: str = None, task_set: str = None) -> tuple[str, dict]:
    """Classify task difficulty using hybrid approach.

    Priority:
    1. If task_type is known and in our mapping, use the mapping
    2. If task_set is "world_consistency", always route to "hard"
    3. Fall back to embedding-based classification

    Returns: (difficulty_label, metadata_dict)
    """
    method = "unknown"

    # Strategy 1: Known task type mapping
    if task_type and task_type in ALL_TYPE_DIFFICULTY:
        difficulty = ALL_TYPE_DIFFICULTY[task_type]
        method = "type_mapping"
        return difficulty, {"method": method, "task_type": task_type}

    # Strategy 2: World consistency always hard
    if task_set == "world_consistency":
        difficulty = "hard"
        method = "task_set"
        return difficulty, {"method": method, "task_set": task_set}

    # Strategy 3: Embedding-based classification
    task_vec = embed(task_text)

    # First: is this a world_consistency task?
    wc_sims = [1 - cosine(task_vec, av) for av in anchor_vecs.get("world_consistency", [])]
    math_sims = []
    for cat in ["math_easy", "math_medium", "math_hard"]:
        math_sims.extend([1 - cosine(task_vec, av) for av in anchor_vecs.get(cat, [])])

    avg_wc = sum(wc_sims) / len(wc_sims) if wc_sims else 0
    avg_math = sum(math_sims) / len(math_sims) if math_sims else 0

    if avg_wc > avg_math:
        difficulty = "hard"
        method = "embedding_domain"
        return difficulty, {"method": method, "wc_sim": avg_wc, "math_sim": avg_math}

    # Math task: classify by difficulty
    scores = {}
    for level in ["easy", "medium", "hard"]:
        cat = f"math_{level}"
        if cat in anchor_vecs:
            sims = [1 - cosine(task_vec, av) for av in anchor_vecs[cat]]
            scores[level] = sum(sims) / len(sims)

    difficulty = max(scores, key=scores.get)
    method = "embedding_difficulty"
    return difficulty, {"method": method, "scores": scores}


if __name__ == "__main__":
    print("Building anchor embeddings...")
    anchor_vecs = build_anchor_embeddings()

    print("\nTest classifications (with type mapping):")
    test_with_type = [
        ("2 + 3 = 5", "calculation", "easy"),
        ("Solve x^2 - 4 = 0", "quadratic_eq", "medium"),
        ("Is 3a + 2a = 5a?", "algebraic_expr", "hard"),
    ]
    for text, task_type, expected in test_with_type:
        difficulty, meta = classify_difficulty(text, anchor_vecs, task_type=task_type)
        match = "OK" if difficulty == expected else "MISS"
        print(f"  [{match}] {difficulty:6s} (exp={expected:6s}) method={meta['method']} | {text[:50]}")

    print("\nTest classifications (embedding fallback):")
    test_embedding = [
        ("Is 5 * 3 = 15 correct?", "easy"),
        ("Solve: x^2 - 5x + 6 = 0. Is x = 2, 3 correct?", "medium"),
        ("World rule: Cats land on feet. Statement: Cat landed on back.", "hard"),
    ]
    for text, expected in test_embedding:
        difficulty, meta = classify_difficulty(text, anchor_vecs)
        match = "OK" if difficulty == expected else "MISS"
        print(f"  [{match}] {difficulty:6s} (exp={expected:6s}) method={meta['method']} | {text[:50]}")
