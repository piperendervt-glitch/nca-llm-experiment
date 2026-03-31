"""
middle_school_task_generator.py

Generate 75 middle school math tasks for NCA v7.5 experiments.
3 grade levels x 25 each: grade7 (中1), grade8 (中2), grade9 (中3).
All labels computed deterministically in Python.
"""

import math
import random
from dataclasses import dataclass
from typing import List


@dataclass
class Task:
    task_id: int
    question: str
    label: bool  # True = CORRECT, False = INCORRECT
    world_rule: str
    task_type: str
    level: str  # "grade7", "grade8", "grade9"
    difficulty: int  # 1, 2, 3
    answer: str  # ground truth (for logging)


# ── World rules ──────────────────────────────────────────────────────────────

WORLD_RULES = {
    "linear_eq": "This is a linear equation. Determine if the given solution is correct.",
    "ratio": "This is a ratio/proportion problem. Determine if the given answer is correct.",
    "geometry": "This is a geometry problem. Determine if the given answer is correct.",
    "signed_number": "This is a signed number calculation. Determine if the result is correct.",
    "algebraic_expr": "This is an algebraic expression. Determine if the simplification is correct.",
    "simultaneous_eq": "This is a system of equations. Determine if the given solution is correct.",
    "linear_function": "This is a linear function problem. Determine if the given value is correct.",
    "congruence": "These are geometric congruence statements. Determine if they are consistent.",
    "polynomial": "This is a polynomial identity. Determine if the expansion is correct.",
    "inequality": "This is an inequality. Determine if the given solution is correct.",
    "quadratic_eq": "This is a quadratic equation. Determine if the given roots are correct.",
    "square_root": "This is a square root simplification. Determine if it is correct.",
    "quadratic_fn": "This is a quadratic function problem. Determine if the given value is correct.",
    "pythagorean": "This is a Pythagorean theorem problem. Determine if the result is correct.",
    "similarity": "These are geometric similarity statements. Determine if they are consistent.",
}


# ═════════════════════════════════════════════════════════════════════════════
# Grade 7 (中1) — 25 problems
# ═════════════════════════════════════════════════════════════════════════════

def _grade7_linear_eq(rng: random.Random, is_correct: bool) -> Task:
    """ax + b = c, solve for x."""
    a = rng.randint(2, 9)
    b = rng.randint(-10, 10)
    # Ensure integer solution
    x_true = rng.randint(-5, 10)
    c = a * x_true + b

    if is_correct:
        x_shown = x_true
    else:
        x_shown = x_true + rng.choice([-2, -1, 1, 2])

    question = f"Solve: {a}x + {b} = {c}. Is x = {x_shown} correct?"
    answer = f"x = {x_true}"
    return Task(0, question, is_correct, WORLD_RULES["linear_eq"],
                "linear_eq", "grade7", 1, answer)


def _grade7_ratio(rng: random.Random, is_correct: bool) -> Task:
    """x : b = c : d, solve for x."""
    b = rng.randint(2, 10)
    c = rng.randint(1, 8)
    d = rng.randint(2, 8)
    x_true = b * c / d

    # Ensure clean answer
    d = rng.randint(2, 6)
    c = rng.randint(1, 6)
    b = d * rng.randint(1, 4)  # makes x integer
    x_true = b * c // d

    if is_correct:
        x_shown = x_true
    else:
        x_shown = x_true + rng.choice([-2, -1, 1, 2])

    question = f"If x : {b} = {c} : {d}, is x = {x_shown} correct?"
    answer = f"x = {x_true}"
    return Task(0, question, is_correct, WORLD_RULES["ratio"],
                "ratio", "grade7", 1, answer)


def _grade7_geometry(rng: random.Random, is_correct: bool) -> Task:
    """Area/perimeter of basic shapes."""
    shape = rng.choice(["circle_area", "circle_circum", "rectangle_area", "triangle_area"])

    if shape == "circle_area":
        r = rng.randint(2, 10)
        correct_val = r * r  # coefficient of pi
        if is_correct:
            shown = correct_val
        else:
            shown = correct_val + rng.choice([-3, -1, 1, 3])
        question = f"A circle has radius {r}. Is its area = {shown}pi correct?"
        answer = f"area = {correct_val}pi"

    elif shape == "circle_circum":
        r = rng.randint(2, 10)
        correct_val = 2 * r  # coefficient of pi
        if is_correct:
            shown = correct_val
        else:
            shown = correct_val + rng.choice([-2, -1, 1, 2])
        question = f"A circle has radius {r}. Is its circumference = {shown}pi correct?"
        answer = f"circumference = {correct_val}pi"

    elif shape == "rectangle_area":
        w = rng.randint(3, 15)
        h = rng.randint(3, 15)
        correct_val = w * h
        if is_correct:
            shown = correct_val
        else:
            shown = correct_val + rng.choice([-5, -2, 2, 5])
        question = f"A rectangle has width {w} and height {h}. Is its area = {shown} correct?"
        answer = f"area = {correct_val}"

    else:  # triangle_area
        base = rng.randint(4, 16)
        height = rng.randint(4, 16)
        # Ensure even product for clean division
        if (base * height) % 2 != 0:
            base += 1
        correct_val = base * height // 2
        if is_correct:
            shown = correct_val
        else:
            shown = correct_val + rng.choice([-3, -1, 1, 3])
        question = f"A triangle has base {base} and height {height}. Is its area = {shown} correct?"
        answer = f"area = {correct_val}"

    return Task(0, question, is_correct, WORLD_RULES["geometry"],
                "geometry", "grade7", 1, answer)


def _grade7_signed(rng: random.Random, is_correct: bool) -> Task:
    """Signed number operations: (-a) * (-b), (-a) + b, etc."""
    op = rng.choice(["mul", "add", "sub"])
    a = rng.randint(1, 12)
    b = rng.randint(1, 12)

    if op == "mul":
        signs = rng.choice([("neg_neg", -a, -b), ("neg_pos", -a, b), ("pos_neg", a, -b)])
        _, va, vb = signs
        correct_val = va * vb
        expr = f"({va}) * ({vb})"
    elif op == "add":
        va = -a
        vb = b if rng.random() > 0.5 else -b
        correct_val = va + vb
        expr = f"({va}) + ({vb})"
    else:
        va = rng.choice([a, -a])
        vb = rng.choice([b, -b])
        correct_val = va - vb
        expr = f"({va}) - ({vb})"

    if is_correct:
        shown = correct_val
    else:
        # Common sign errors
        shown = -correct_val if rng.random() > 0.5 else correct_val + rng.choice([-2, -1, 1, 2])

    question = f"Is {expr} = {shown} correct?"
    answer = f"{expr} = {correct_val}"
    return Task(0, question, is_correct, WORLD_RULES["signed_number"],
                "signed_number", "grade7", 1, answer)


def _grade7_algebraic(rng: random.Random, is_correct: bool) -> Task:
    """Simplify algebraic expressions: 3a + 2a = 5a, etc."""
    coeff_a = rng.randint(1, 8)
    coeff_b = rng.randint(1, 8)
    var = rng.choice(["a", "b", "x", "y"])
    op = rng.choice(["+", "-"])

    if op == "+":
        correct_coeff = coeff_a + coeff_b
        expr = f"{coeff_a}{var} + {coeff_b}{var}"
    else:
        correct_coeff = coeff_a - coeff_b
        expr = f"{coeff_a}{var} - {coeff_b}{var}"

    if is_correct:
        shown = correct_coeff
    else:
        shown = correct_coeff + rng.choice([-2, -1, 1, 2])

    question = f"Is {expr} = {shown}{var} correct?"
    answer = f"{expr} = {correct_coeff}{var}"
    return Task(0, question, is_correct, WORLD_RULES["algebraic_expr"],
                "algebraic_expr", "grade7", 1, answer)


def generate_grade7(rng: random.Random) -> List[Task]:
    generators = [
        _grade7_linear_eq,
        _grade7_ratio,
        _grade7_geometry,
        _grade7_signed,
        _grade7_algebraic,
    ]
    tasks = []
    # 5 tasks per generator: alternate CORRECT/INCORRECT starting with
    # True for even generators, False for odd => ~50/50 overall
    for gen_idx, gen in enumerate(generators):
        for i in range(5):
            if gen_idx % 2 == 0:
                is_correct = (i % 2 == 0)  # 3 correct, 2 incorrect
            else:
                is_correct = (i % 2 == 1)  # 2 correct, 3 incorrect
            tasks.append(gen(rng, is_correct))
    return tasks


# ═════════════════════════════════════════════════════════════════════════════
# Grade 8 (中2) — 25 problems
# ═════════════════════════════════════════════════════════════════════════════

def _grade8_simultaneous(rng: random.Random, is_correct: bool) -> Task:
    """Simultaneous equations: ax + by = e, cx + dy = f."""
    x_true = rng.randint(-5, 5)
    y_true = rng.randint(-5, 5)
    a = rng.randint(1, 5)
    b = rng.randint(1, 5)
    c = rng.randint(1, 5)
    d = rng.randint(-5, -1)  # ensure different from first eq
    e = a * x_true + b * y_true
    f = c * x_true + d * y_true

    if is_correct:
        x_shown, y_shown = x_true, y_true
    else:
        if rng.random() > 0.5:
            x_shown = x_true + rng.choice([-1, 1])
            y_shown = y_true
        else:
            x_shown = x_true
            y_shown = y_true + rng.choice([-1, 1])

    question = (f"Solve the system: {a}x + {b}y = {e}, {c}x + ({d})y = {f}. "
                f"Is x = {x_shown}, y = {y_shown} correct?")
    answer = f"x = {x_true}, y = {y_true}"
    return Task(0, question, is_correct, WORLD_RULES["simultaneous_eq"],
                "simultaneous_eq", "grade8", 2, answer)


def _grade8_linear_function(rng: random.Random, is_correct: bool) -> Task:
    """y = mx + b, evaluate at x = k."""
    m = rng.randint(-5, 5)
    b = rng.randint(-10, 10)
    k = rng.randint(-5, 5)
    y_true = m * k + b

    if is_correct:
        y_shown = y_true
    else:
        y_shown = y_true + rng.choice([-3, -1, 1, 3])

    if b >= 0:
        fn_str = f"y = {m}x + {b}"
    else:
        fn_str = f"y = {m}x - {abs(b)}"

    question = f"For {fn_str}, when x = {k}, is y = {y_shown} correct?"
    answer = f"y = {y_true}"
    return Task(0, question, is_correct, WORLD_RULES["linear_function"],
                "linear_function", "grade8", 2, answer)


def _grade8_congruence(rng: random.Random, is_correct: bool) -> Task:
    """Triangle congruence logic: SSS, SAS, ASA consistency."""
    if is_correct:
        # Consistent: proper congruence claim
        a = rng.randint(3, 10)
        b = rng.randint(3, 10)
        angle = rng.randint(30, 120)
        question = (
            f"Triangle ABC has AB = {a}, BC = {b}, angle B = {angle} degrees. "
            f"Triangle DEF has DE = {a}, EF = {b}, angle E = {angle} degrees. "
            f"Are these triangles congruent by SAS (Side-Angle-Side)? Answer: CORRECT (they are congruent)."
        )
        answer = "SAS congruence: two sides and included angle match"
    else:
        # Contradiction: non-included angle claimed as SAS
        a = rng.randint(3, 10)
        b = rng.randint(3, 10)
        angle_b = rng.randint(30, 80)
        angle_e = rng.randint(angle_b + 10, 130)
        question = (
            f"Triangle ABC has AB = {a}, BC = {b}, angle B = {angle_b} degrees. "
            f"Triangle DEF has DE = {a}, EF = {b}, angle E = {angle_e} degrees. "
            f"Are these triangles congruent by SAS? Answer: CORRECT (they are congruent)."
        )
        answer = f"NOT congruent: angle B ({angle_b}) != angle E ({angle_e})"

    return Task(0, question, is_correct, WORLD_RULES["congruence"],
                "congruence", "grade8", 2, answer)


def _grade8_polynomial(rng: random.Random, is_correct: bool) -> Task:
    """Polynomial expansion: (x+a)(x+b) = x^2 + (a+b)x + ab."""
    a = rng.randint(-8, 8)
    b = rng.randint(-8, 8)
    correct_mid = a + b
    correct_const = a * b

    if is_correct:
        mid = correct_mid
        const = correct_const
    else:
        # Common error: wrong sign or wrong product
        if rng.random() > 0.5:
            mid = correct_mid
            const = correct_const + rng.choice([-2, -1, 1, 2])
        else:
            mid = correct_mid + rng.choice([-1, 1])
            const = correct_const

    # Format nicely
    def _fmt_term(coeff, var="x"):
        if coeff == 0:
            return ""
        if coeff > 0:
            return f" + {coeff}{var}" if coeff != 1 else f" + {var}"
        return f" - {abs(coeff)}{var}" if coeff != -1 else f" - {var}"

    def _fmt_const(c):
        if c == 0:
            return ""
        return f" + {c}" if c > 0 else f" - {abs(c)}"

    a_str = f"+ {a}" if a >= 0 else f"- {abs(a)}"
    b_str = f"+ {b}" if b >= 0 else f"- {abs(b)}"
    rhs_mid = _fmt_term(mid)
    rhs_const = _fmt_const(const)

    question = f"Is (x {a_str})(x {b_str}) = x^2{rhs_mid}{rhs_const} correct?"
    answer = f"(x {a_str})(x {b_str}) = x^2{_fmt_term(correct_mid)}{_fmt_const(correct_const)}"
    return Task(0, question, is_correct, WORLD_RULES["polynomial"],
                "polynomial", "grade8", 2, answer)


def _grade8_inequality(rng: random.Random, is_correct: bool) -> Task:
    """Solve inequality: ax + b > c."""
    a = rng.choice([i for i in range(-5, 6) if i != 0])
    b = rng.randint(-10, 10)
    c = rng.randint(-10, 10)
    # ax > c - b => x > (c-b)/a (if a>0) or x < (c-b)/a (if a<0)
    diff = c - b

    # Ensure clean integer boundary
    if diff % a != 0:
        c = b + a * rng.randint(-3, 3)
        diff = c - b

    boundary = diff // a
    if a > 0:
        correct_dir = ">"
    else:
        correct_dir = "<"

    if is_correct:
        dir_shown = correct_dir
        bnd_shown = boundary
    else:
        if rng.random() > 0.5:
            dir_shown = "<" if correct_dir == ">" else ">"
            bnd_shown = boundary
        else:
            dir_shown = correct_dir
            bnd_shown = boundary + rng.choice([-1, 1])

    b_str = f"+ {b}" if b >= 0 else f"- {abs(b)}"
    question = f"Solve: {a}x {b_str} > {c}. Is x {dir_shown} {bnd_shown} correct?"
    answer = f"x {correct_dir} {boundary}"
    return Task(0, question, is_correct, WORLD_RULES["inequality"],
                "inequality", "grade8", 2, answer)


def generate_grade8(rng: random.Random) -> List[Task]:
    generators = [
        _grade8_simultaneous,
        _grade8_linear_function,
        _grade8_congruence,
        _grade8_polynomial,
        _grade8_inequality,
    ]
    tasks = []
    for gen_idx, gen in enumerate(generators):
        for i in range(5):
            if gen_idx % 2 == 0:
                is_correct = (i % 2 == 0)
            else:
                is_correct = (i % 2 == 1)
            tasks.append(gen(rng, is_correct))
    return tasks


# ═════════════════════════════════════════════════════════════════════════════
# Grade 9 (中3) — 25 problems
# ═════════════════════════════════════════════════════════════════════════════

def _grade9_quadratic_eq(rng: random.Random, is_correct: bool) -> Task:
    """x^2 + bx + c = 0 with integer roots p, q."""
    p = rng.randint(-8, 8)
    q = rng.randint(-8, 8)
    # x^2 - (p+q)x + pq = 0
    b_coeff = -(p + q)
    c_coeff = p * q
    roots_true = sorted([p, q])

    if is_correct:
        roots_shown = roots_true
    else:
        if rng.random() > 0.5:
            roots_shown = [roots_true[0] + rng.choice([-1, 1]), roots_true[1]]
        else:
            roots_shown = [roots_true[0], roots_true[1] + rng.choice([-1, 1])]
        roots_shown = sorted(roots_shown)

    b_str = f"+ {b_coeff}" if b_coeff >= 0 else f"- {abs(b_coeff)}"
    c_str = f"+ {c_coeff}" if c_coeff >= 0 else f"- {abs(c_coeff)}"
    r_str = f"x = {roots_shown[0]}, {roots_shown[1]}" if roots_shown[0] != roots_shown[1] else f"x = {roots_shown[0]} (double root)"

    question = f"Solve: x^2 {b_str}x {c_str} = 0. Is {r_str} correct?"
    r_true_str = f"x = {roots_true[0]}, {roots_true[1]}" if roots_true[0] != roots_true[1] else f"x = {roots_true[0]}"
    answer = r_true_str
    return Task(0, question, is_correct, WORLD_RULES["quadratic_eq"],
                "quadratic_eq", "grade9", 3, answer)


def _grade9_sqrt(rng: random.Random, is_correct: bool) -> Task:
    """Simplify sqrt(n) = a*sqrt(b)."""
    # Generate n = a^2 * b where b is square-free
    a = rng.randint(2, 6)
    b_choices = [2, 3, 5, 6, 7]
    b = rng.choice(b_choices)
    n = a * a * b

    if is_correct:
        a_shown = a
        b_shown = b
    else:
        if rng.random() > 0.5:
            a_shown = a + rng.choice([-1, 1])
            b_shown = b
        else:
            a_shown = a
            b_shown = rng.choice([x for x in b_choices if x != b])

    if a_shown == 1:
        shown_str = f"sqrt({b_shown})"
    else:
        shown_str = f"{a_shown}*sqrt({b_shown})"

    question = f"Is sqrt({n}) = {shown_str} correct?"
    answer = f"sqrt({n}) = {a}*sqrt({b})"
    return Task(0, question, is_correct, WORLD_RULES["square_root"],
                "square_root", "grade9", 3, answer)


def _grade9_quadratic_fn(rng: random.Random, is_correct: bool) -> Task:
    """y = ax^2 + bx + c, evaluate or find vertex."""
    a_coeff = rng.choice([-3, -2, -1, 1, 2, 3])
    b_coeff = rng.randint(-6, 6)
    c_coeff = rng.randint(-10, 10)
    x_val = rng.randint(-4, 4)
    y_true = a_coeff * x_val * x_val + b_coeff * x_val + c_coeff

    if is_correct:
        y_shown = y_true
    else:
        y_shown = y_true + rng.choice([-3, -2, -1, 1, 2, 3])

    # Format function
    parts = [f"{a_coeff}x^2"]
    if b_coeff > 0:
        parts.append(f"+ {b_coeff}x")
    elif b_coeff < 0:
        parts.append(f"- {abs(b_coeff)}x")
    if c_coeff > 0:
        parts.append(f"+ {c_coeff}")
    elif c_coeff < 0:
        parts.append(f"- {abs(c_coeff)}")
    fn_str = "y = " + " ".join(parts)

    question = f"For {fn_str}, when x = {x_val}, is y = {y_shown} correct?"
    answer = f"y = {y_true}"
    return Task(0, question, is_correct, WORLD_RULES["quadratic_fn"],
                "quadratic_fn", "grade9", 3, answer)


def _grade9_pythagorean(rng: random.Random, is_correct: bool) -> Task:
    """Pythagorean theorem: a^2 + b^2 = c^2."""
    # Known triples scaled
    triples = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]
    base = rng.choice(triples)
    scale = rng.randint(1, 3)
    a, b, c = base[0] * scale, base[1] * scale, base[2] * scale

    query_type = rng.choice(["verify", "find_c", "find_a"])

    if query_type == "verify":
        if is_correct:
            c_shown = c
        else:
            c_shown = c + rng.choice([-1, 1])
        question = f"A right triangle has legs {a} and {b}. Is the hypotenuse = {c_shown} correct?"
        answer = f"hypotenuse = {c}"

    elif query_type == "find_c":
        c_sq = a * a + b * b
        c_true = int(math.isqrt(c_sq))
        if is_correct:
            shown = c_true
        else:
            shown = c_true + rng.choice([-1, 1])
        question = f"A right triangle has legs {a} and {b}. Is the hypotenuse = {shown} correct?"
        answer = f"hypotenuse = {c_true} (sqrt({c_sq}))"

    else:  # find_a
        a_sq = c * c - b * b
        a_true = int(math.isqrt(a_sq))
        if is_correct:
            shown = a_true
        else:
            shown = a_true + rng.choice([-1, 1])
        question = f"A right triangle has hypotenuse {c} and one leg {b}. Is the other leg = {shown} correct?"
        answer = f"other leg = {a_true} (sqrt({c}^2 - {b}^2) = sqrt({a_sq}))"

    return Task(0, question, is_correct, WORLD_RULES["pythagorean"],
                "pythagorean", "grade9", 3, answer)


def _grade9_similarity(rng: random.Random, is_correct: bool) -> Task:
    """Similarity / congruence logic contradictions."""
    if is_correct:
        ratio = rng.randint(2, 4)
        a1 = rng.randint(3, 8)
        b1 = rng.randint(3, 8)
        a2 = a1 * ratio
        b2 = b1 * ratio
        question = (
            f"Triangle ABC has AB = {a1}, BC = {b1}. "
            f"Triangle DEF has DE = {a2}, EF = {b2}. "
            f"The ratio AB:DE = BC:EF = 1:{ratio}. "
            f"Are these triangles similar? Answer: CORRECT (they are similar)."
        )
        answer = f"Similar with ratio 1:{ratio}"
    else:
        a1 = rng.randint(3, 8)
        b1 = rng.randint(3, 8)
        ratio1 = rng.randint(2, 4)
        ratio2 = ratio1 + rng.choice([1, 2])  # different ratio
        a2 = a1 * ratio1
        b2 = b1 * ratio2
        question = (
            f"Triangle ABC has AB = {a1}, BC = {b1}. "
            f"Triangle DEF has DE = {a2}, EF = {b2}. "
            f"Claim: triangles ABC and DEF are similar. "
            f"Is this claim correct?"
        )
        answer = f"NOT similar: AB:DE = {a1}:{a2} but BC:EF = {b1}:{b2}, ratios differ"

    return Task(0, question, is_correct, WORLD_RULES["similarity"],
                "similarity", "grade9", 3, answer)


def generate_grade9(rng: random.Random) -> List[Task]:
    generators = [
        _grade9_quadratic_eq,
        _grade9_sqrt,
        _grade9_quadratic_fn,
        _grade9_pythagorean,
        _grade9_similarity,
    ]
    tasks = []
    for gen_idx, gen in enumerate(generators):
        for i in range(5):
            if gen_idx % 2 == 0:
                is_correct = (i % 2 == 0)
            else:
                is_correct = (i % 2 == 1)
            tasks.append(gen(rng, is_correct))
    return tasks


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════

def generate_middle_school_tasks(seed: int = 42) -> List[Task]:
    """Generate 75 middle school math tasks (25 per grade level)."""
    rng = random.Random(seed)

    tasks = []
    tasks.extend(generate_grade7(rng))
    tasks.extend(generate_grade8(rng))
    tasks.extend(generate_grade9(rng))

    # Shuffle within each grade level to mix task types
    grade7 = [t for t in tasks if t.level == "grade7"]
    grade8 = [t for t in tasks if t.level == "grade8"]
    grade9 = [t for t in tasks if t.level == "grade9"]
    rng.shuffle(grade7)
    rng.shuffle(grade8)
    rng.shuffle(grade9)

    # Reassemble: grade7 first, then grade8, then grade9
    tasks = grade7 + grade8 + grade9
    for i, t in enumerate(tasks):
        t.task_id = i

    return tasks


if __name__ == "__main__":
    tasks = generate_middle_school_tasks()
    correct = sum(1 for t in tasks if t.label)
    incorrect = sum(1 for t in tasks if not t.label)
    print(f"Generated {len(tasks)} tasks: {correct} CORRECT, {incorrect} INCORRECT")

    for level in ["grade7", "grade8", "grade9"]:
        level_tasks = [t for t in tasks if t.level == level]
        c = sum(1 for t in level_tasks if t.label)
        types = set(t.task_type for t in level_tasks)
        print(f"  {level}: {len(level_tasks)} tasks ({c} CORRECT, {len(level_tasks)-c} INCORRECT)")
        print(f"    Types: {', '.join(sorted(types))}")

    print("\nSamples:")
    shown = set()
    for t in tasks:
        key = (t.level, t.task_type)
        if key not in shown:
            label_str = "CORRECT" if t.label else "INCORRECT"
            print(f"  [{t.level}/{t.task_type}] {t.question[:80]}")
            print(f"    Label: {label_str} | Answer: {t.answer}")
            shown.add(key)
