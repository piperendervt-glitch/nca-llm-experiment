"""
high_school_task_generator.py

Generate 75 high school math tasks for NCA v7.6 experiments.
3 grade levels x 25 each: grade10 (高1), grade11 (高2), grade12 (高3).
All labels computed deterministically in Python using math module.
"""

import math
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import List


@dataclass
class Task:
    task_id: int
    question: str
    label: bool  # True = CORRECT, False = INCORRECT
    world_rule: str
    task_type: str
    level: str  # "grade10", "grade11", "grade12"
    difficulty: int  # 4, 5, 6
    answer: str  # ground truth (for logging)


WORLD_RULES = {
    "quadratic_minmax": "This is a quadratic function minimum/maximum problem. Determine if the answer is correct.",
    "quadratic_ineq": "This is a quadratic inequality. Determine if the solution set is correct.",
    "factoring": "This is a factoring problem. Determine if the factorization is correct.",
    "probability": "This is a probability problem. Determine if the given probability is correct.",
    "logic_quad": "These are statements about quadratic functions. Determine if they are consistent.",
    "trig_value": "This is a trigonometric value problem. Determine if the answer is correct.",
    "trig_identity": "This is a trigonometric identity problem. Determine if the answer is correct.",
    "logarithm": "This is a logarithm problem. Determine if the answer is correct.",
    "exponent": "This is an exponent calculation. Determine if the answer is correct.",
    "recurrence": "This is a recurrence relation problem. Determine if the answer is correct.",
    "derivative": "This is a derivative problem. Determine if the answer is correct.",
    "extremum": "This is an extremum (local min/max) problem. Determine if the answer is correct.",
    "integral": "This is an integral problem. Determine if the answer is correct.",
    "area": "This is an area calculation problem. Determine if the answer is correct.",
    "arithmetic_seq": "This is an arithmetic sequence problem. Determine if the answer is correct.",
}


# ═════════════════════════════════════════════════════════════════════════════
# Grade 10 (高1) — 25 problems
# ═════════════════════════════════════════════════════════════════════════════

def _g10_quadratic_minmax(rng: random.Random, is_correct: bool) -> Task:
    """y = a(x-h)^2 + k, find min or max."""
    a = rng.choice([-3, -2, -1, 1, 2, 3])
    h = rng.randint(-5, 5)
    k = rng.randint(-10, 10)
    # y = a*x^2 - 2ah*x + a*h^2 + k
    b_coeff = -2 * a * h
    c_coeff = a * h * h + k

    if a > 0:
        extremum_type = "minimum"
        extremum_val = k
    else:
        extremum_type = "maximum"
        extremum_val = k

    if is_correct:
        shown = extremum_val
    else:
        shown = extremum_val + rng.choice([-3, -2, -1, 1, 2, 3])

    # Format y = ax^2 + bx + c
    parts = []
    if a == 1:
        parts.append("x^2")
    elif a == -1:
        parts.append("-x^2")
    else:
        parts.append(f"{a}x^2")
    if b_coeff > 0:
        parts.append(f"+ {b_coeff}x")
    elif b_coeff < 0:
        parts.append(f"- {abs(b_coeff)}x")
    if c_coeff > 0:
        parts.append(f"+ {c_coeff}")
    elif c_coeff < 0:
        parts.append(f"- {abs(c_coeff)}")

    fn_str = " ".join(parts)
    question = f"For y = {fn_str}, is the {extremum_type} value = {shown} correct?"
    answer = f"{extremum_type} = {extremum_val} at x = {h}"
    return Task(0, question, is_correct, WORLD_RULES["quadratic_minmax"],
                "quadratic_minmax", "grade10", 4, answer)


def _g10_quadratic_ineq(rng: random.Random, is_correct: bool) -> Task:
    """x^2 + bx + c > 0 or < 0, find solution set."""
    # Roots p, q with p < q
    p = rng.randint(-6, 2)
    q = rng.randint(p + 1, 6)
    # x^2 - (p+q)x + pq > 0 => x < p or x > q
    b_coeff = -(p + q)
    c_coeff = p * q

    b_str = f"+ {b_coeff}" if b_coeff >= 0 else f"- {abs(b_coeff)}"
    c_str = f"+ {c_coeff}" if c_coeff >= 0 else f"- {abs(c_coeff)}"

    ineq_type = rng.choice([">", "<"])
    if ineq_type == ">":
        correct_sol = f"x < {p} or x > {q}"
        if is_correct:
            shown_sol = correct_sol
        else:
            shown_sol = f"x < {p + rng.choice([-1, 1])} or x > {q}"
    else:
        correct_sol = f"{p} < x < {q}"
        if is_correct:
            shown_sol = correct_sol
        else:
            shown_sol = f"{p} < x < {q + rng.choice([-1, 1])}"

    question = f"Solve: x^2 {b_str}x {c_str} {ineq_type} 0. Is the solution '{shown_sol}' correct?"
    answer = f"Roots: {p}, {q}. Solution: {correct_sol}"
    return Task(0, question, is_correct, WORLD_RULES["quadratic_ineq"],
                "quadratic_ineq", "grade10", 4, answer)


def _g10_factoring(rng: random.Random, is_correct: bool) -> Task:
    """Factor x^2 + bx + c = (x + p)(x + q)."""
    p = rng.randint(-8, 8)
    q = rng.randint(-8, 8)
    b_val = p + q
    c_val = p * q

    if is_correct:
        p_shown, q_shown = p, q
    else:
        if rng.random() > 0.5:
            p_shown = p + rng.choice([-1, 1])
            q_shown = q
        else:
            p_shown = p
            q_shown = q + rng.choice([-1, 1])

    b_str = f"+ {b_val}" if b_val >= 0 else f"- {abs(b_val)}"
    c_str = f"+ {c_val}" if c_val >= 0 else f"- {abs(c_val)}"
    p_str = f"+ {p_shown}" if p_shown >= 0 else f"- {abs(p_shown)}"
    q_str = f"+ {q_shown}" if q_shown >= 0 else f"- {abs(q_shown)}"

    question = f"Is x^2 {b_str}x {c_str} = (x {p_str})(x {q_str}) correct?"
    answer = f"(x {'+' if p >= 0 else '-'} {abs(p)})(x {'+' if q >= 0 else '-'} {abs(q)})"
    return Task(0, question, is_correct, WORLD_RULES["factoring"],
                "factoring", "grade10", 4, answer)


def _g10_probability(rng: random.Random, is_correct: bool) -> Task:
    """Basic probability with dice/coins/cards."""
    prob_type = rng.choice(["coins", "dice", "draw"])

    if prob_type == "coins":
        n = rng.randint(2, 4)
        k = rng.randint(0, n)
        # P(k heads in n flips) = C(n,k) / 2^n
        numerator = math.comb(n, k)
        denominator = 2 ** n
        frac = Fraction(numerator, denominator)
        correct_str = f"{frac.numerator}/{frac.denominator}" if frac.denominator != 1 else str(frac.numerator)

        if is_correct:
            shown_str = correct_str
        else:
            wrong_num = frac.numerator + rng.choice([-1, 1])
            if wrong_num <= 0:
                wrong_num = frac.numerator + 1
            shown_str = f"{wrong_num}/{frac.denominator}"

        question = (f"When flipping {n} fair coins, is the probability of getting "
                    f"exactly {k} heads = {shown_str} correct?")
        answer = f"P = C({n},{k})/2^{n} = {frac}"

    elif prob_type == "dice":
        n_dice = rng.choice([1, 2])
        if n_dice == 1:
            target = rng.randint(1, 6)
            frac = Fraction(1, 6)
            if is_correct:
                shown_str = "1/6"
            else:
                shown_str = rng.choice(["1/3", "1/5", "2/6"])
            question = f"When rolling one fair die, is P(getting {target}) = {shown_str} correct?"
            answer = f"P = 1/6"
        else:
            target_sum = rng.randint(2, 12)
            # Count ways to get target_sum with 2 dice
            ways = sum(1 for a in range(1, 7) for b in range(1, 7) if a + b == target_sum)
            frac = Fraction(ways, 36)
            correct_str = f"{frac.numerator}/{frac.denominator}" if frac.denominator != 1 else str(frac.numerator)
            if is_correct:
                shown_str = correct_str
            else:
                wrong_ways = ways + rng.choice([-1, 1])
                if wrong_ways <= 0:
                    wrong_ways = ways + 1
                wrong_frac = Fraction(wrong_ways, 36)
                shown_str = f"{wrong_frac.numerator}/{wrong_frac.denominator}"
            question = (f"When rolling two fair dice, is P(sum = {target_sum}) = {shown_str} correct?")
            answer = f"P = {ways}/36 = {frac}"

    else:  # draw
        total = rng.randint(5, 12)
        red = rng.randint(1, total - 1)
        draw = rng.randint(1, min(3, red))
        # P(draw all red) = C(red, draw) / C(total, draw)
        numerator = math.comb(red, draw)
        denominator = math.comb(total, draw)
        frac = Fraction(numerator, denominator)
        correct_str = f"{frac.numerator}/{frac.denominator}" if frac.denominator != 1 else str(frac.numerator)
        if is_correct:
            shown_str = correct_str
        else:
            wrong_num = frac.numerator + rng.choice([-1, 1])
            if wrong_num <= 0:
                wrong_num = frac.numerator + 1
            shown_str = f"{wrong_num}/{frac.denominator}"
        question = (f"A bag has {red} red and {total - red} blue balls. Drawing {draw} ball(s), "
                    f"is P(all red) = {shown_str} correct?")
        answer = f"P = C({red},{draw})/C({total},{draw}) = {frac}"

    return Task(0, question, is_correct, WORLD_RULES["probability"],
                "probability", "grade10", 4, answer)


def _g10_logic(rng: random.Random, is_correct: bool) -> Task:
    """Logic about quadratic function properties."""
    a = rng.choice([-2, -1, 1, 2])
    h = rng.randint(-3, 3)
    k = rng.randint(-5, 5)

    if is_correct:
        if a > 0:
            question = (
                f"A quadratic function y = {a}(x - {h})^2 + {k} opens upward. "
                f"Its minimum value is {k}. "
                f"Its axis of symmetry is x = {h}. "
                f"Are all these statements correct?"
            )
            answer = "All consistent: upward parabola, min = k, axis = h"
        else:
            question = (
                f"A quadratic function y = {a}(x - {h})^2 + {k} opens downward. "
                f"Its maximum value is {k}. "
                f"Its axis of symmetry is x = {h}. "
                f"Are all these statements correct?"
            )
            answer = "All consistent: downward parabola, max = k, axis = h"
    else:
        # Contradiction: wrong direction or wrong extremum type
        if a > 0:
            question = (
                f"A quadratic function y = {a}(x - {h})^2 + {k} opens upward. "
                f"Its maximum value is {k}. "
                f"Are all these statements correct?"
            )
            answer = f"Contradiction: opens upward (a={a}>0) means minimum, not maximum"
        else:
            question = (
                f"A quadratic function y = {a}(x - {h})^2 + {k} opens downward. "
                f"Its minimum value is {k}. "
                f"Are all these statements correct?"
            )
            answer = f"Contradiction: opens downward (a={a}<0) means maximum, not minimum"

    return Task(0, question, is_correct, WORLD_RULES["logic_quad"],
                "logic_quad", "grade10", 4, answer)


def generate_grade10(rng: random.Random) -> List[Task]:
    generators = [
        _g10_quadratic_minmax, _g10_quadratic_ineq, _g10_factoring,
        _g10_probability, _g10_logic,
    ]
    tasks = []
    for gen_idx, gen in enumerate(generators):
        for i in range(5):
            is_correct = (i % 2 == 0) if gen_idx % 2 == 0 else (i % 2 == 1)
            tasks.append(gen(rng, is_correct))
    return tasks


# ═════════════════════════════════════════════════════════════════════════════
# Grade 11 (高2) — 25 problems
# ═════════════════════════════════════════════════════════════════════════════

def _g11_trig_value(rng: random.Random, is_correct: bool) -> Task:
    """Known trig values: sin/cos/tan of standard angles."""
    # Use exact known values
    known = {
        (0, "sin"): "0", (0, "cos"): "1", (0, "tan"): "0",
        (30, "sin"): "1/2", (30, "cos"): "sqrt(3)/2", (30, "tan"): "1/sqrt(3)",
        (45, "sin"): "sqrt(2)/2", (45, "cos"): "sqrt(2)/2", (45, "tan"): "1",
        (60, "sin"): "sqrt(3)/2", (60, "cos"): "1/2", (60, "tan"): "sqrt(3)",
        (90, "sin"): "1", (90, "cos"): "0",
    }
    # Filter out tan(90) which is undefined
    choices = list(known.keys())
    angle, func = rng.choice(choices)
    correct_val = known[(angle, func)]

    # Wrong answers pool
    all_vals = ["0", "1/2", "sqrt(2)/2", "sqrt(3)/2", "1", "1/sqrt(3)", "sqrt(3)", "2"]
    wrong_choices = [v for v in all_vals if v != correct_val]

    if is_correct:
        shown = correct_val
    else:
        shown = rng.choice(wrong_choices)

    question = f"Is {func}({angle} degrees) = {shown} correct?"
    answer = f"{func}({angle}) = {correct_val}"
    return Task(0, question, is_correct, WORLD_RULES["trig_value"],
                "trig_value", "grade11", 5, answer)


def _g11_trig_identity(rng: random.Random, is_correct: bool) -> Task:
    """sin^2 + cos^2 = 1, given one value find the other."""
    # Pick a clean cos value, compute sin
    angle_deg = rng.choice([30, 45, 60])
    angle_rad = math.radians(angle_deg)
    cos_val = math.cos(angle_rad)
    sin_val = math.sin(angle_rad)

    # Use fractions for display
    cos_display = {30: "sqrt(3)/2", 45: "sqrt(2)/2", 60: "1/2"}
    sin_display = {30: "1/2", 45: "sqrt(2)/2", 60: "sqrt(3)/2"}

    query_type = rng.choice(["find_sin", "find_cos"])
    if query_type == "find_sin":
        given = cos_display[angle_deg]
        correct = sin_display[angle_deg]
        wrong_choices = [v for v in ["1/2", "sqrt(2)/2", "sqrt(3)/2", "1/4", "3/4"] if v != correct]
        shown = correct if is_correct else rng.choice(wrong_choices)
        question = f"If cos(theta) = {given} (first quadrant), is sin(theta) = {shown} correct?"
        answer = f"sin(theta) = {correct}"
    else:
        given = sin_display[angle_deg]
        correct = cos_display[angle_deg]
        wrong_choices = [v for v in ["1/2", "sqrt(2)/2", "sqrt(3)/2", "1/4", "3/4"] if v != correct]
        shown = correct if is_correct else rng.choice(wrong_choices)
        question = f"If sin(theta) = {given} (first quadrant), is cos(theta) = {shown} correct?"
        answer = f"cos(theta) = {correct}"

    return Task(0, question, is_correct, WORLD_RULES["trig_identity"],
                "trig_identity", "grade11", 5, answer)


def _g11_logarithm(rng: random.Random, is_correct: bool) -> Task:
    """log_b(x) = y, verify."""
    base = rng.choice([2, 3, 5, 10])
    exp = rng.randint(1, 5)
    x = base ** exp
    correct_val = exp

    if is_correct:
        shown = correct_val
    else:
        shown = correct_val + rng.choice([-1, 1])

    if base == 10:
        question = f"Is log({x}) = {shown} correct?"
    else:
        question = f"Is log_{base}({x}) = {shown} correct?"
    answer = f"log_{base}({x}) = {correct_val}"
    return Task(0, question, is_correct, WORLD_RULES["logarithm"],
                "logarithm", "grade11", 5, answer)


def _g11_exponent(rng: random.Random, is_correct: bool) -> Task:
    """Exponent rules: a^m * a^n = a^(m+n), (a^m)^n = a^(mn), etc."""
    rule_type = rng.choice(["product", "power", "quotient"])
    base = rng.randint(2, 5)
    m = rng.randint(1, 6)
    n = rng.randint(1, 6)

    if rule_type == "product":
        correct_exp = m + n
        expr = f"{base}^{m} * {base}^{n}"
        if is_correct:
            shown_exp = correct_exp
        else:
            shown_exp = m * n  # common mistake
        question = f"Is {expr} = {base}^{shown_exp} correct?"
        answer = f"{expr} = {base}^{correct_exp}"

    elif rule_type == "power":
        correct_exp = m * n
        expr = f"({base}^{m})^{n}"
        if is_correct:
            shown_exp = correct_exp
        else:
            shown_exp = m + n  # common mistake
        question = f"Is {expr} = {base}^{shown_exp} correct?"
        answer = f"{expr} = {base}^{correct_exp}"

    else:  # quotient
        # Ensure m > n for clean result
        if m <= n:
            m, n = n + 1, m
        correct_exp = m - n
        expr = f"{base}^{m} / {base}^{n}"
        if is_correct:
            shown_exp = correct_exp
        else:
            shown_exp = rng.choice([m * n, m + n, correct_exp + rng.choice([-1, 1])])
        question = f"Is {expr} = {base}^{shown_exp} correct?"
        answer = f"{expr} = {base}^{correct_exp}"

    return Task(0, question, is_correct, WORLD_RULES["exponent"],
                "exponent", "grade11", 5, answer)


def _g11_recurrence(rng: random.Random, is_correct: bool) -> Task:
    """Recurrence relation: a_n = r * a_{n-1}, find a_k."""
    a1 = rng.randint(1, 5)
    r = rng.randint(2, 4)
    k = rng.randint(3, 6)
    # a_k = a1 * r^(k-1)
    correct_val = a1 * (r ** (k - 1))

    if is_correct:
        shown = correct_val
    else:
        # Common mistake: a1 * r^k or off by one
        wrong = rng.choice([a1 * (r ** k), a1 * (r ** (k - 2)),
                            correct_val + rng.choice([-r, r])])
        shown = wrong

    question = (f"Given a_n = {r} * a_{{n-1}} with a_1 = {a1}, "
                f"is a_{k} = {shown} correct?")
    answer = f"a_{k} = {a1} * {r}^{k-1} = {correct_val}"
    return Task(0, question, is_correct, WORLD_RULES["recurrence"],
                "recurrence", "grade11", 5, answer)


def generate_grade11(rng: random.Random) -> List[Task]:
    generators = [
        _g11_trig_value, _g11_trig_identity, _g11_logarithm,
        _g11_exponent, _g11_recurrence,
    ]
    tasks = []
    for gen_idx, gen in enumerate(generators):
        for i in range(5):
            is_correct = (i % 2 == 0) if gen_idx % 2 == 0 else (i % 2 == 1)
            tasks.append(gen(rng, is_correct))
    return tasks


# ═════════════════════════════════════════════════════════════════════════════
# Grade 12 (高3) — 25 problems
# ═════════════════════════════════════════════════════════════════════════════

def _g12_derivative(rng: random.Random, is_correct: bool) -> Task:
    """f(x) = ax^n, f'(x) = n*a*x^(n-1)."""
    a = rng.choice([-3, -2, -1, 1, 2, 3, 4, 5])
    n = rng.randint(2, 5)
    correct_coeff = n * a
    correct_exp = n - 1

    if is_correct:
        shown_coeff = correct_coeff
        shown_exp = correct_exp
    else:
        if rng.random() > 0.5:
            shown_coeff = a  # forgot to multiply by n
            shown_exp = correct_exp
        else:
            shown_coeff = correct_coeff
            shown_exp = n  # forgot to subtract 1

    if a == 1:
        f_str = f"x^{n}"
    elif a == -1:
        f_str = f"-x^{n}"
    else:
        f_str = f"{a}x^{n}"

    if shown_exp == 0:
        deriv_str = f"{shown_coeff}"
    elif shown_exp == 1:
        deriv_str = f"{shown_coeff}x"
    else:
        deriv_str = f"{shown_coeff}x^{shown_exp}"

    question = f"If f(x) = {f_str}, is f'(x) = {deriv_str} correct?"
    if correct_exp == 0:
        answer = f"f'(x) = {correct_coeff}"
    elif correct_exp == 1:
        answer = f"f'(x) = {correct_coeff}x"
    else:
        answer = f"f'(x) = {correct_coeff}x^{correct_exp}"
    return Task(0, question, is_correct, WORLD_RULES["derivative"],
                "derivative", "grade12", 6, answer)


def _g12_extremum(rng: random.Random, is_correct: bool) -> Task:
    """f(x) = x^3 + bx^2 + cx + d, find local extremum."""
    # f(x) = x^3 - 3px, f'(x) = 3x^2 - 3p = 3(x^2 - p)
    # Critical points at x = +/- sqrt(p) if p > 0
    p = rng.choice([1, 3, 4])
    # f(x) = x^3 - 3p*x
    # f'(x) = 3x^2 - 3p
    # Local max at x = -sqrt(p), local min at x = sqrt(p)
    sqrt_p = int(math.isqrt(p))
    if sqrt_p * sqrt_p != p:
        p = sqrt_p * sqrt_p  # ensure perfect square
        if p == 0:
            p = 1
        sqrt_p = int(math.isqrt(p))

    # f(sqrt_p) = sqrt_p^3 - 3p * sqrt_p (local min)
    min_val = sqrt_p ** 3 - 3 * p * sqrt_p
    # f(-sqrt_p) = -sqrt_p^3 + 3p * sqrt_p (local max)
    max_val = -(sqrt_p ** 3) + 3 * p * sqrt_p

    extremum = rng.choice(["min", "max"])
    if extremum == "min":
        correct_val = min_val
        x_at = sqrt_p
        label = "local minimum"
    else:
        correct_val = max_val
        x_at = -sqrt_p
        label = "local maximum"

    if is_correct:
        shown = correct_val
    else:
        shown = correct_val + rng.choice([-2, -1, 1, 2])

    question = (f"For f(x) = x^3 - {3*p}x, is the {label} value = {shown} correct?")
    answer = f"{label} at x = {x_at}: f({x_at}) = {correct_val}"
    return Task(0, question, is_correct, WORLD_RULES["extremum"],
                "extremum", "grade12", 6, answer)


def _g12_integral(rng: random.Random, is_correct: bool) -> Task:
    """Indefinite integral: integral of ax^n dx = a/(n+1) * x^(n+1) + C."""
    a = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4, 6])
    n = rng.randint(1, 4)
    correct_denom = n + 1
    frac = Fraction(a, correct_denom)

    if is_correct:
        shown_num = frac.numerator
        shown_den = frac.denominator
    else:
        # Common error: wrong denominator
        wrong_denom = rng.choice([n, n + 2])
        wrong_frac = Fraction(a, wrong_denom)
        shown_num = wrong_frac.numerator
        shown_den = wrong_frac.denominator

    if a == 1:
        integrand = f"x^{n}"
    elif a == -1:
        integrand = f"-x^{n}"
    else:
        integrand = f"{a}x^{n}"

    if shown_den == 1:
        result_str = f"{shown_num}x^{n+1}"
    else:
        result_str = f"({shown_num}/{shown_den})x^{n+1}"

    question = f"Is the integral of {integrand} dx = {result_str} + C correct?"

    if frac.denominator == 1:
        answer = f"integral = {frac.numerator}x^{n+1} + C"
    else:
        answer = f"integral = ({frac.numerator}/{frac.denominator})x^{n+1} + C"
    return Task(0, question, is_correct, WORLD_RULES["integral"],
                "integral", "grade12", 6, answer)


def _g12_area(rng: random.Random, is_correct: bool) -> Task:
    """Area between y = x^2 and y = kx (k > 0)."""
    # Intersection: x^2 = kx => x(x - k) = 0 => x = 0, k
    # Area = integral from 0 to k of (kx - x^2) dx = k^3/2 - k^3/3 = k^3/6
    k = rng.randint(1, 5)
    correct_frac = Fraction(k ** 3, 6)

    if is_correct:
        shown_num = correct_frac.numerator
        shown_den = correct_frac.denominator
    else:
        wrong_denom = rng.choice([3, 4, 8])
        wrong_frac = Fraction(k ** 3, wrong_denom)
        shown_num = wrong_frac.numerator
        shown_den = wrong_frac.denominator

    if shown_den == 1:
        shown_str = str(shown_num)
    else:
        shown_str = f"{shown_num}/{shown_den}"

    if correct_frac.denominator == 1:
        correct_str = str(correct_frac.numerator)
    else:
        correct_str = f"{correct_frac.numerator}/{correct_frac.denominator}"

    question = (f"The area enclosed by y = x^2 and y = {k}x "
                f"is {shown_str}. Is this correct?")
    answer = f"Area = {k}^3 / 6 = {correct_str}"
    return Task(0, question, is_correct, WORLD_RULES["area"],
                "area", "grade12", 6, answer)


def _g12_arith_seq(rng: random.Random, is_correct: bool) -> Task:
    """Sum of arithmetic sequence: S_n = n(a1 + an)/2."""
    a1 = rng.randint(-5, 10)
    d = rng.randint(1, 5)
    n = rng.randint(5, 15)
    an = a1 + (n - 1) * d
    s_n = n * (a1 + an) // 2

    # Ensure integer sum
    if (n * (a1 + an)) % 2 != 0:
        n += 1
        an = a1 + (n - 1) * d
        s_n = n * (a1 + an) // 2

    query_type = rng.choice(["sum", "nth_term"])
    if query_type == "sum":
        if is_correct:
            shown = s_n
        else:
            shown = s_n + rng.choice([-5, -3, 3, 5])
        question = (f"Arithmetic sequence: a_1 = {a1}, common difference = {d}. "
                    f"Is S_{n} (sum of first {n} terms) = {shown} correct?")
        answer = f"a_{n} = {an}, S_{n} = {n}*({a1}+{an})/2 = {s_n}"
    else:
        if is_correct:
            shown = an
        else:
            shown = an + rng.choice([-d, d])
        question = (f"Arithmetic sequence: a_1 = {a1}, common difference = {d}. "
                    f"Is a_{n} = {shown} correct?")
        answer = f"a_{n} = {a1} + ({n}-1)*{d} = {an}"

    return Task(0, question, is_correct, WORLD_RULES["arithmetic_seq"],
                "arithmetic_seq", "grade12", 6, answer)


def generate_grade12(rng: random.Random) -> List[Task]:
    generators = [
        _g12_derivative, _g12_extremum, _g12_integral,
        _g12_area, _g12_arith_seq,
    ]
    tasks = []
    for gen_idx, gen in enumerate(generators):
        for i in range(5):
            is_correct = (i % 2 == 0) if gen_idx % 2 == 0 else (i % 2 == 1)
            tasks.append(gen(rng, is_correct))
    return tasks


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════

def generate_high_school_tasks(seed: int = 42) -> List[Task]:
    """Generate 75 high school math tasks (25 per grade level)."""
    rng = random.Random(seed)

    tasks = []
    tasks.extend(generate_grade10(rng))
    tasks.extend(generate_grade11(rng))
    tasks.extend(generate_grade12(rng))

    # Shuffle within each grade level
    grade10 = [t for t in tasks if t.level == "grade10"]
    grade11 = [t for t in tasks if t.level == "grade11"]
    grade12 = [t for t in tasks if t.level == "grade12"]
    rng.shuffle(grade10)
    rng.shuffle(grade11)
    rng.shuffle(grade12)

    tasks = grade10 + grade11 + grade12
    for i, t in enumerate(tasks):
        t.task_id = i

    return tasks


if __name__ == "__main__":
    tasks = generate_high_school_tasks()
    correct = sum(1 for t in tasks if t.label)
    incorrect = sum(1 for t in tasks if not t.label)
    print(f"Generated {len(tasks)} tasks: {correct} CORRECT, {incorrect} INCORRECT")

    for level in ["grade10", "grade11", "grade12"]:
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
            print(f"  [{t.level}/{t.task_type}] {t.question[:90]}")
            print(f"    Label: {label_str} | Answer: {t.answer}")
            shown.add(key)
