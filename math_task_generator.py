"""
math_task_generator.py

Generate elementary-level math tasks for v7 experiments.
4 types × 25 questions = 100 questions.
Labels are computed by Python (no LLM needed).
"""

import random
from dataclasses import dataclass
from typing import List, Tuple

random.seed(42)

WORLD_RULES = {
    "calculation": "This is a math calculation. Determine if the equation is correct.",
    "logical": "These are logical statements about relative sizes. Determine if they are consistent.",
    "word_problem": "This is a word problem. Determine if the given answer is correct.",
    "sequence": "This is a number sequence. Determine if the sequence follows a consistent pattern.",
}


@dataclass
class Task:
    task_id: int
    question: str
    label: bool
    world_rule: str
    task_type: str


# ---------------------------------------------------------------------------
# Type 1: Calculation verification
# ---------------------------------------------------------------------------

def _make_equation() -> Tuple[str, int]:
    """Return (equation_string_without_answer, correct_answer)."""
    op = random.choice(["+", "-", "×", "÷"])
    if op == "+":
        a, b = random.randint(1, 20), random.randint(1, 20)
        return f"{a} + {b}", a + b
    elif op == "-":
        a, b = sorted([random.randint(1, 20), random.randint(1, 20)], reverse=True)
        return f"{a} - {b}", a - b
    elif op == "×":
        a, b = random.randint(1, 12), random.randint(1, 12)
        return f"{a} × {b}", a * b
    else:  # ÷
        b = random.randint(1, 10)
        answer = random.randint(1, 10)
        a = b * answer
        return f"{a} ÷ {b}", answer


def generate_calculation_tasks(n: int = 25) -> List[Task]:
    """Generate calculation verification tasks."""
    tasks: List[Task] = []
    seen: set = set()
    n_correct = (n + 1) // 2  # 13
    correct_flags = [True] * n_correct + [False] * (n - n_correct)
    random.shuffle(correct_flags)

    for is_correct in correct_flags:
        # Avoid duplicate equations
        for _ in range(100):
            expr, answer = _make_equation()
            if expr not in seen:
                seen.add(expr)
                break

        if is_correct:
            question = f"{expr} = {answer}"
        else:
            offset = random.choice([i for i in range(-5, 6) if i != 0])
            question = f"{expr} = {answer + offset}"

        tasks.append(Task(
            task_id=0,
            question=question,
            label=is_correct,
            world_rule=WORLD_RULES["calculation"],
            task_type="calculation",
        ))
    return tasks


# ---------------------------------------------------------------------------
# Type 2: Logical consistency (ordering relations)
# ---------------------------------------------------------------------------

def _check_consistency(relations: List[Tuple[str, str, str]]) -> bool:
    """Check if a set of (a, rel, b) relations is consistent.

    Relations: '>' means a > b, '<' means a < b, '=' means a == b.
    Uses constraint propagation with inequality tracking.
    """
    from itertools import combinations

    # Build graph: for each pair, track allowed relations
    vars_set: set = set()
    for a, _, b in relations:
        vars_set.update([a, b])
    variables = sorted(vars_set)

    # Try to find a consistent assignment via topological ordering
    # Convert everything to > edges and = edges
    gt_edges: List[Tuple[str, str]] = []  # (a, b) means a > b
    eq_edges: List[Tuple[str, str]] = []

    for a, rel, b in relations:
        if rel == ">":
            gt_edges.append((a, b))
        elif rel == "<":
            gt_edges.append((b, a))
        else:  # =
            eq_edges.append((a, b))

    # Union-find for equality
    parent = {v: v for v in variables}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for a, b in eq_edges:
        union(a, b)

    # Check gt_edges for cycles (using representatives)
    from collections import defaultdict, deque
    graph: dict = defaultdict(set)
    in_degree: dict = defaultdict(int)
    nodes: set = set()

    for a, b in gt_edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False  # a == b but a > b => contradiction
        if rb not in graph[ra]:
            graph[ra].add(rb)
            in_degree.setdefault(ra, 0)
            in_degree[rb] = in_degree.get(rb, 0) + 1
            nodes.update([ra, rb])

    for v in variables:
        nodes.add(find(v))

    # Topological sort to detect cycles
    queue = deque([n for n in nodes if in_degree.get(n, 0) == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return visited == len(nodes)


def generate_logical_tasks(n: int = 25) -> List[Task]:
    """Generate logical consistency tasks."""
    tasks: List[Task] = []
    n_correct = (n + 1) // 2  # 13
    correct_flags = [True] * n_correct + [False] * (n - n_correct)
    random.shuffle(correct_flags)

    all_vars = ["A", "B", "C", "D", "E"]
    rel_words = {">": "is greater than", "<": "is less than", "=": "is equal to"}

    for is_correct in correct_flags:
        num_vars = random.choice([3, 4])
        chosen = random.sample(all_vars, num_vars)

        if is_correct:
            # Generate consistent ordering
            perm = chosen[:]
            random.shuffle(perm)
            # perm[0] > perm[1] > ... > perm[-1]
            relations = []
            for i in range(len(perm) - 1):
                rel = random.choice([">", "<"])
                if rel == ">":
                    relations.append((perm[i], ">", perm[i + 1]))
                else:
                    relations.append((perm[i + 1], "<", perm[i]))
            # Add one more consistent relation
            if len(perm) >= 3:
                i, j = 0, len(perm) - 1
                rel = random.choice([">", "<"])
                if rel == ">":
                    relations.append((perm[i], ">", perm[j]))
                else:
                    relations.append((perm[j], "<", perm[i]))
        else:
            # Generate contradictory (cyclic) ordering
            perm = chosen[:3]
            random.shuffle(perm)
            relations = [
                (perm[0], ">", perm[1]),
                (perm[1], ">", perm[2]),
                (perm[2], ">", perm[0]),  # cycle!
            ]

        random.shuffle(relations)
        sentences = [f"{a} {rel_words[r]} {b}" for a, r, b in relations]
        question = ". ".join(sentences) + "."

        tasks.append(Task(
            task_id=0,
            question=question,
            label=is_correct,
            world_rule=WORLD_RULES["logical"],
            task_type="logical",
        ))
    return tasks


# ---------------------------------------------------------------------------
# Type 3: Word problems
# ---------------------------------------------------------------------------

_ITEMS = ["apples", "oranges", "candies", "cookies", "pencils",
          "books", "marbles", "stickers", "balls", "cards"]

_WORD_TEMPLATES = {
    "+": [
        "You have {a} {item}. You receive {b} more. The total is {ans} {item}.",
        "There are {a} {item} on the table. {b} more are added. Now there are {ans} {item}.",
    ],
    "-": [
        "You have {a} {item}. You give away {b}. You now have {ans} {item}.",
        "There are {a} {item}. {b} are taken away. {ans} {item} remain.",
    ],
    "×": [
        "There are {a} bags, each containing {b} {item}. The total is {ans} {item}.",
        "You buy {a} packs of {item}, with {b} in each pack. You have {ans} {item} in total.",
    ],
    "÷": [
        "You have {a} {item} and divide them equally among {b} friends. Each friend gets {ans} {item}.",
        "{a} {item} are split into {b} equal groups. Each group has {ans} {item}.",
    ],
}


def generate_word_problem_tasks(n: int = 25) -> List[Task]:
    """Generate word problem verification tasks."""
    tasks: List[Task] = []
    n_correct = (n + 1) // 2
    correct_flags = [True] * n_correct + [False] * (n - n_correct)
    random.shuffle(correct_flags)

    for is_correct in correct_flags:
        op = random.choice(["+", "-", "×", "÷"])
        item = random.choice(_ITEMS)
        template = random.choice(_WORD_TEMPLATES[op])

        if op == "+":
            a, b = random.randint(1, 15), random.randint(1, 15)
            correct_ans = a + b
        elif op == "-":
            a = random.randint(2, 20)
            b = random.randint(1, a - 1)
            correct_ans = a - b
        elif op == "×":
            a, b = random.randint(2, 10), random.randint(2, 10)
            correct_ans = a * b
        else:  # ÷
            b = random.randint(2, 10)
            correct_ans = random.randint(1, 10)
            a = b * correct_ans

        if is_correct:
            ans = correct_ans
        else:
            offset = random.choice([i for i in range(-3, 4) if i != 0])
            ans = correct_ans + offset

        question = template.format(a=a, b=b, ans=ans, item=item)

        tasks.append(Task(
            task_id=0,
            question=question,
            label=is_correct,
            world_rule=WORLD_RULES["word_problem"],
            task_type="word_problem",
        ))
    return tasks


# ---------------------------------------------------------------------------
# Type 4: Sequence pattern detection
# ---------------------------------------------------------------------------

def generate_sequence_tasks(n: int = 25) -> List[Task]:
    """Generate sequence pattern detection tasks."""
    tasks: List[Task] = []
    n_correct = (n + 1) // 2
    correct_flags = [True] * n_correct + [False] * (n - n_correct)
    random.shuffle(correct_flags)

    for is_correct in correct_flags:
        pattern_type = random.choice(["arithmetic", "geometric", "fibonacci"])
        length = random.randint(5, 7)

        if pattern_type == "arithmetic":
            start = random.randint(1, 10)
            diff = random.randint(1, 5)
            seq = [start + diff * i for i in range(length)]
            desc = f"(pattern: +{diff})"
        elif pattern_type == "geometric":
            start = random.randint(1, 3)
            ratio = random.randint(2, 3)
            seq = [start * (ratio ** i) for i in range(length)]
            desc = f"(pattern: ×{ratio})"
        else:  # fibonacci-like
            a, b = random.randint(1, 5), random.randint(1, 5)
            seq = [a, b]
            for _ in range(length - 2):
                seq.append(seq[-1] + seq[-2])
            desc = "(pattern: each number is the sum of the two before it)"

        if not is_correct:
            # Corrupt one element (not first or last to make it harder)
            idx = random.randint(1, length - 2)
            offset = random.choice([i for i in range(-5, 6) if i != 0])
            # Make sure corrupted value is different
            seq[idx] = seq[idx] + offset

        seq_str = ", ".join(str(x) for x in seq)
        question = f"Sequence: {seq_str} {desc}"

        tasks.append(Task(
            task_id=0,
            question=question,
            label=is_correct,
            world_rule=WORLD_RULES["sequence"],
            task_type="sequence",
        ))
    return tasks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_math_tasks() -> List[Task]:
    """Generate all 4 types of tasks and combine them."""
    tasks: List[Task] = []
    tasks.extend(generate_calculation_tasks(25))
    tasks.extend(generate_logical_tasks(25))
    tasks.extend(generate_word_problem_tasks(25))
    tasks.extend(generate_sequence_tasks(25))

    for i, task in enumerate(tasks):
        task.task_id = i

    return tasks


def format_prompt(task: Task) -> str:
    """Convert a task to prompt format (same as world_consistency)."""
    return (
        f"Rule: {task.world_rule}\n"
        f"Statement: {task.question}\n"
        f"Is this statement correct and consistent?\n"
        f"Answer with CONSISTENT (correct/no contradiction) or "
        f"CONTRADICTION (incorrect/has contradiction)."
    )


if __name__ == "__main__":
    tasks = generate_math_tasks()
    print(f"Generated tasks: {len(tasks)}")

    for task_type in ["calculation", "logical", "word_problem", "sequence"]:
        type_tasks = [t for t in tasks if t.task_type == task_type]
        correct = sum(1 for t in type_tasks if t.label)
        print(f"  {task_type}: {len(type_tasks)} questions "
              f"(correct {correct} / incorrect {len(type_tasks) - correct})")

    print("\nSample (1 per type):")
    shown: set = set()
    for task in tasks:
        if task.task_type not in shown:
            print(f"\n[{task.task_type}]")
            print(f"  Question: {task.question}")
            print(f"  Label: {'CONSISTENT' if task.label else 'CONTRADICTION'}")
            shown.add(task.task_type)
        if len(shown) == 4:
            break
