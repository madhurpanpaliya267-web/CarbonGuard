"""Deterministic statistical primitives for research analytics (Phase 8).

Pure-Python implementation: no numpy/scipy dependency, no randomness, no
nondeterministic ordering. Every function is a deterministic function of its
inputs, so identical inputs always produce identical outputs.

Standard-deviation conventions (explicitly recorded, never mixed silently):

- ``POPULATION_STD_CONVENTION``: variance = sum((x - mean)^2) / n.
  Used for descriptive statistics. This matches the existing convention in
  ``interaction_effect_service.descriptive_statistics`` and the marginal
  energy statistics, so Phase 5-7 descriptive output is reproduced exactly.
- ``SAMPLE_STD_CONVENTION``: variance = sum((x - mean)^2) / (n - 1).
  Used only inside the Student-t confidence interval, the paired t-test and
  Cohen's dz, because those methods are defined with n-1 degrees of freedom.

Hypothesis tests here report statistical results only. They never state that
a security configuration is better, optimal, or more efficient.
"""

import math
from typing import List, Optional

POPULATION_STD_CONVENTION = "population_standard_deviation_n"
SAMPLE_STD_CONVENTION = "sample_standard_deviation_n_minus_1"

_TWO_SIDED = "two-sided"
_GREATER = "greater"
_LESS = "less"
_ALTERNATIVES = (_TWO_SIDED, _GREATER, _LESS)

_BETA_MAX_ITERATIONS = 300
_BETA_EPS = 3.0e-16
_BETA_FPMIN = 1.0e-300
_QUANTILE_MAX_ITERATIONS = 300

# Exact Wilcoxon sign enumeration is used up to this sample size; above it a
# normal approximation (with continuity correction) is used and documented.
WILCOXON_EXACT_MAX_N = 100


def _validate_values(values: List[float], min_n: int = 1) -> int:
    if len(values) < min_n:
        raise ValueError(f"Requires at least {min_n} observation(s), got {len(values)}")
    for index, value in enumerate(values):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"Observation {index} is not numeric: {value!r}")
        if not math.isfinite(value):
            raise ValueError(f"Observation {index} is not finite: {value!r}")
    return len(values)


def descriptive_statistics(values: List[float]) -> dict:
    """Count, mean, median, population standard deviation, min, max.

    Uses the repository's existing population standard-deviation convention
    (divide by n), matching Phase 5-7 descriptive statistics exactly.
    """
    n = _validate_values(values, min_n=1)
    mean_v = sum(values) / n
    sorted_v = sorted(values)
    median_v = (
        sorted_v[n // 2] if n % 2 == 1
        else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2
    )
    variance = sum((v - mean_v) ** 2 for v in values) / n if n > 1 else 0.0
    return {
        "mean": mean_v,
        "median": median_v,
        "std_dev": variance ** 0.5,
        "min": min(values),
        "max": max(values),
        "count": n,
        "std_dev_convention": POPULATION_STD_CONVENTION,
    }


def _sample_std(values: List[float]) -> Optional[float]:
    """Sample standard deviation (n-1). None when it is undefined (n < 2)."""
    n = len(values)
    if n < 2:
        return None
    mean_v = sum(values) / n
    variance = sum((v - mean_v) ** 2 for v in values) / (n - 1)
    return variance ** 0.5


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Continued-fraction expansion for the incomplete beta function (Lentz)."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _BETA_FPMIN:
        d = _BETA_FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, _BETA_MAX_ITERATIONS + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _BETA_FPMIN:
            d = _BETA_FPMIN
        c = 1.0 + aa / c
        if abs(c) < _BETA_FPMIN:
            c = _BETA_FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _BETA_FPMIN:
            d = _BETA_FPMIN
        c = 1.0 + aa / c
        if abs(c) < _BETA_FPMIN:
            c = _BETA_FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _BETA_EPS:
            break
    return h


def regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b). Deterministic."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    ln_factor = ln_beta + a * math.log(x) + b * math.log1p(-x)
    factor = math.exp(ln_factor)
    if x < (a + 1.0) / (a + b + 2.0):
        result = factor * _beta_continued_fraction(a, b, x) / a
    else:
        result = 1.0 - factor * _beta_continued_fraction(b, a, 1.0 - x) / b
    return min(1.0, max(0.0, result))


def _clamp_probability(value: float) -> float:
    return min(1.0, max(0.0, value))


def t_two_sided_p_value(statistic: float, degrees_of_freedom: int) -> float:
    """Two-sided p-value of Student's t: P(|T| >= |t|)."""
    df = float(degrees_of_freedom)
    x = df / (df + statistic * statistic)
    return _clamp_probability(regularized_incomplete_beta(df / 2.0, 0.5, x))


def t_cdf(statistic: float, degrees_of_freedom: int) -> float:
    """CDF of Student's t at ``statistic``."""
    if statistic == 0.0:
        return 0.5
    tail = t_two_sided_p_value(statistic, degrees_of_freedom)
    if statistic > 0:
        return 1.0 - 0.5 * tail
    return 0.5 * tail


def t_quantile(probability: float, degrees_of_freedom: int) -> float:
    """Inverse CDF of Student's t via deterministic bisection."""
    if not 0.0 < probability < 1.0:
        raise ValueError(f"probability must be in (0, 1), got {probability}")
    if degrees_of_freedom < 1:
        raise ValueError(f"degrees_of_freedom must be >= 1, got {degrees_of_freedom}")
    if probability == 0.5:
        # Student's t is symmetric around 0; return its median directly.
        return 0.0
    lower = -1.0
    upper = 1.0
    for _ in range(_QUANTILE_MAX_ITERATIONS):
        if t_cdf(lower, degrees_of_freedom) <= probability:
            break
        lower *= 2.0
    else:
        raise ValueError("Failed to bracket lower t quantile")
    for _ in range(_QUANTILE_MAX_ITERATIONS):
        if t_cdf(upper, degrees_of_freedom) >= probability:
            break
        upper *= 2.0
    else:
        raise ValueError("Failed to bracket upper t quantile")
    for _ in range(_QUANTILE_MAX_ITERATIONS):
        midpoint = (lower + upper) / 2.0
        if t_cdf(midpoint, degrees_of_freedom) < probability:
            lower = midpoint
        else:
            upper = midpoint
        if abs(upper - lower) < 1.0e-12:
            break
    return (lower + upper) / 2.0


def confidence_interval_t(values: List[float], level: float) -> dict:
    """Two-sided Student-t confidence interval for the mean.

    Uses the sample standard deviation (n-1). Requires n >= 2; for n = 1 the
    interval is not computed (a t-interval with zero degrees of freedom is not
    a meaningful inferential result).
    """
    n = _validate_values(values, min_n=1)
    if not 0.0 < level < 1.0:
        raise ValueError(f"confidence level must be in (0, 1), got {level}")
    if n < 2:
        return {
            "status": "omitted",
            "reason": "Confidence intervals require at least 2 observations (n=1 has no degrees of freedom)",
            "level": level,
            "n": n,
        }
    sample_std = _sample_std(values)
    mean_v = sum(values) / n
    standard_error = sample_std / math.sqrt(n)
    degrees_of_freedom = n - 1
    if standard_error == 0.0:
        lower = upper = mean_v
    else:
        critical = t_quantile(1.0 - (1.0 - level) / 2.0, degrees_of_freedom)
        margin = critical * standard_error
        lower = mean_v - margin
        upper = mean_v + margin
    return {
        "status": "ok",
        "reason": None,
        "level": level,
        "n": n,
        "mean": mean_v,
        "lower": lower,
        "upper": upper,
        "standard_error": standard_error,
        "degrees_of_freedom": degrees_of_freedom,
        "critical_value": (
            0.0 if standard_error == 0.0
            else t_quantile(1.0 - (1.0 - level) / 2.0, degrees_of_freedom)
        ),
        "method": "student_t_interval",
        "std_dev_convention": SAMPLE_STD_CONVENTION,
    }


def paired_t_test(
    values: List[float],
    alternative: str = _TWO_SIDED,
    significance_level: float = 0.05,
) -> dict:
    """One-sample t-test on paired differences (equivalent to a paired t-test).

    H0: mean paired difference = 0 (for ``values`` interpreted as paired
    differences). The statistic uses the sample standard deviation (n-1) with
    n-1 degrees of freedom, per the definition of Student's t.
    """
    n = _validate_values(values, min_n=2)
    if alternative not in _ALTERNATIVES:
        raise ValueError(f"alternative must be one of {_ALTERNATIVES}, got {alternative!r}")
    if not 0.0 < significance_level < 1.0:
        raise ValueError(f"significance_level must be in (0, 1), got {significance_level}")
    mean_v = sum(values) / n
    sample_std = _sample_std(values)
    degrees_of_freedom = n - 1
    if sample_std == 0.0:
        return {
            "status": "undefined",
            "reason": "t-statistic undefined: all paired differences are identical (zero variance)",
            "statistic": None,
            "p_value": None,
            "sample_count": n,
            "degrees_of_freedom": degrees_of_freedom,
            "alternative": alternative,
            "significance_level": significance_level,
        }
    standard_error = sample_std / math.sqrt(n)
    statistic = mean_v / standard_error
    if alternative == _TWO_SIDED:
        p_value = t_two_sided_p_value(statistic, degrees_of_freedom)
    elif alternative == _GREATER:
        p_value = 1.0 - t_cdf(statistic, degrees_of_freedom)
    else:
        p_value = t_cdf(statistic, degrees_of_freedom)
    return {
        "status": "ok",
        "reason": None,
        "statistic": statistic,
        "p_value": _clamp_probability(p_value),
        "sample_count": n,
        "degrees_of_freedom": degrees_of_freedom,
        "alternative": alternative,
        "significance_level": significance_level,
        "mean_difference": mean_v,
        "standard_error": standard_error,
        "std_dev_convention": SAMPLE_STD_CONVENTION,
    }


def _average_ranks(absolute_values: List[float]) -> List[float]:
    """Average ranks (1-based) with ties receiving the mean of their ranks."""
    order = sorted(range(len(absolute_values)), key=lambda i: (absolute_values[i], i))
    ranks = [0.0] * len(absolute_values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and absolute_values[order[end + 1]] == absolute_values[order[position]]:
            end += 1
        if end == position:
            ranks[order[position]] = float(position + 1)
        else:
            average = (position + 1 + end + 1) / 2.0
            for k in range(position, end + 1):
                ranks[order[k]] = average
        position = end + 1
    return ranks


def wilcoxon_signed_rank(
    values: List[float],
    alternative: str = _TWO_SIDED,
    significance_level: float = 0.05,
) -> dict:
    """Wilcoxon signed-rank test on paired differences.

    Zero differences are excluded from ranks, following the standard Wilcoxon
    convention; the excluded count is reported (never silently discarded).

    - n <= WILCOXON_EXACT_MAX_N: exact sign-enumeration p-value (deterministic
      dynamic program over doubled ranks, so tie-averaged ranks stay exact).
    - n > WILCOXON_EXACT_MAX_N: normal approximation with continuity
      correction; the approximation is reported in ``method``.
    """
    n_total = _validate_values(values, min_n=1)
    if alternative not in _ALTERNATIVES:
        raise ValueError(f"alternative must be one of {_ALTERNATIVES}, got {alternative!r}")
    if not 0.0 < significance_level < 1.0:
        raise ValueError(f"significance_level must be in (0, 1), got {significance_level}")
    nonzero = [v for v in values if v != 0]
    zeros_excluded = n_total - len(nonzero)
    n = len(nonzero)
    if n == 0:
        return {
            "status": "undefined",
            "reason": "Wilcoxon signed-rank undefined: all paired differences are zero",
            "statistic": None,
            "p_value": None,
            "sample_count": 0,
            "excluded_zero_differences": zeros_excluded,
            "alternative": alternative,
            "significance_level": significance_level,
        }
    if n < 2:
        return {
            "status": "undefined",
            "reason": "Wilcoxon signed-rank requires at least 2 non-zero paired differences",
            "statistic": None,
            "p_value": None,
            "sample_count": n,
            "excluded_zero_differences": zeros_excluded,
            "alternative": alternative,
            "significance_level": significance_level,
        }
    ranks = _average_ranks([abs(v) for v in nonzero])
    w_plus = sum(rank for value, rank in zip(nonzero, ranks) if value > 0)
    w_minus = sum(rank for value, rank in zip(nonzero, ranks) if value < 0)
    total_rank_sum = w_plus + w_minus

    if n <= WILCOXON_EXACT_MAX_N:
        doubled_ranks = [int(round(rank * 2)) for rank in ranks]
        max_doubled = sum(doubled_ranks)
        counts = [0] * (max_doubled + 1)
        counts[0] = 1
        for doubled in doubled_ranks:
            for s in range(max_doubled, doubled - 1, -1):
                if counts[s - doubled]:
                    counts[s] += counts[s - doubled]
        observed = int(round(w_plus * 2))
        total_assignments = 2 ** n
        less_or_equal = sum(counts[: observed + 1]) / total_assignments
        greater_or_equal = sum(counts[observed:]) / total_assignments
        method = "exact_sign_enumeration"
    else:
        mean_w = sum(ranks) / 2.0
        variance_w = sum(rank * rank for rank in ranks) / 4.0
        standard_deviation = math.sqrt(variance_w)
        if standard_deviation == 0.0:
            return {
                "status": "undefined",
                "reason": "Wilcoxon signed-rank undefined: zero variance of rank sum",
                "statistic": None,
                "p_value": None,
                "sample_count": n,
                "excluded_zero_differences": zeros_excluded,
                "alternative": alternative,
                "significance_level": significance_level,
            }
        z_greater = (w_plus - 0.5 - mean_w) / standard_deviation
        z_less = (mean_w - w_plus - 0.5) / standard_deviation
        greater_or_equal = _clamp_probability(0.5 * math.erfc(z_greater / math.sqrt(2.0)))
        less_or_equal = _clamp_probability(0.5 * math.erfc(z_less / math.sqrt(2.0)))
        method = "normal_approximation_continuity_correction"

    if alternative == _TWO_SIDED:
        p_value = _clamp_probability(2.0 * min(less_or_equal, greater_or_equal))
    elif alternative == _GREATER:
        p_value = _clamp_probability(greater_or_equal)
    else:
        p_value = _clamp_probability(less_or_equal)
    return {
        "status": "ok",
        "reason": None,
        "statistic": w_plus,
        "p_value": p_value,
        "sample_count": n,
        "excluded_zero_differences": zeros_excluded,
        "alternative": alternative,
        "significance_level": significance_level,
        "w_plus": w_plus,
        "w_minus": w_minus,
        "total_rank_sum": total_rank_sum,
        "method": method,
    }


def cohens_dz(values: List[float]) -> dict:
    """Cohen's dz for paired differences: mean(d) / sample_std(d).

    Uses the sample standard deviation (n-1), consistent with the paired
    t-statistic (dz = t / sqrt(n)). Descriptive only: a non-zero effect size
    does not imply statistical significance.
    """
    n = _validate_values(values, min_n=2)
    mean_v = sum(values) / n
    sample_std = _sample_std(values)
    if sample_std == 0.0:
        return {
            "status": "undefined",
            "reason": "Cohen's dz undefined: zero variance in paired differences",
            "value": None,
            "sample_count": n,
        }
    return {
        "status": "ok",
        "reason": None,
        "value": mean_v / sample_std,
        "sample_count": n,
        "std_dev_convention": SAMPLE_STD_CONVENTION,
    }


def rank_biserial(values: List[float]) -> dict:
    """Matched-pairs rank-biserial correlation for the Wilcoxon signed-rank test.

    r = (W+ - W-) / (W+ + W-), in [-1, 1]. Descriptive only: a non-zero
    effect size does not imply statistical significance.
    """
    _validate_values(values, min_n=1)
    nonzero = [v for v in values if v != 0]
    if len(nonzero) < 2:
        return {
            "status": "undefined",
            "reason": "Rank-biserial correlation requires at least 2 non-zero paired differences",
            "value": None,
            "sample_count": len(nonzero),
        }
    ranks = _average_ranks([abs(v) for v in nonzero])
    w_plus = sum(rank for value, rank in zip(nonzero, ranks) if value > 0)
    w_minus = sum(rank for value, rank in zip(nonzero, ranks) if value < 0)
    denominator = w_plus + w_minus
    if denominator == 0:
        return {
            "status": "undefined",
            "reason": "Rank-biserial correlation undefined: zero total rank sum",
            "value": None,
            "sample_count": len(nonzero),
        }
    return {
        "status": "ok",
        "reason": None,
        "value": (w_plus - w_minus) / denominator,
        "sample_count": len(nonzero),
    }
