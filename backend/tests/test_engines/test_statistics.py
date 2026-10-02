import itertools
import math

import pytest

from app.engines.analytics.statistics import (
    POPULATION_STD_CONVENTION,
    SAMPLE_STD_CONVENTION,
    WILCOXON_EXACT_MAX_N,
    cohens_dz,
    confidence_interval_t,
    descriptive_statistics,
    paired_t_test,
    rank_biserial,
    regularized_incomplete_beta,
    t_cdf,
    t_quantile,
    t_two_sided_p_value,
    wilcoxon_signed_rank,
)


class TestDescriptiveStatistics:
    def test_known_values(self):
        result = descriptive_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result["count"] == 5
        assert result["mean"] == 3.0
        assert result["median"] == 3.0
        assert result["min"] == 1.0
        assert result["max"] == 5.0
        # population convention: variance = 2.0, std = sqrt(2)
        assert abs(result["std_dev"] - math.sqrt(2)) < 1e-12
        assert result["std_dev_convention"] == POPULATION_STD_CONVENTION

    def test_median_even_count(self):
        result = descriptive_statistics([1.0, 2.0, 3.0, 4.0])
        assert result["median"] == 2.5

    def test_single_value(self):
        result = descriptive_statistics([42.0])
        assert result["count"] == 1
        assert result["mean"] == 42.0
        assert result["std_dev"] == 0.0

    def test_negative_values(self):
        result = descriptive_statistics([-5.0, 5.0])
        assert result["mean"] == 0.0
        assert result["min"] == -5.0
        assert result["max"] == 5.0

    def test_matches_phase6_convention(self):
        from app.services.interaction_effect_service import descriptive_statistics as phase6

        values = [1.5, -2.0, 9.25, 0.0, 4.75]
        mine = descriptive_statistics(values)
        theirs = phase6(values)
        for key in ("mean", "median", "std_dev", "min", "max", "count"):
            assert mine[key] == theirs[key]

    def test_empty_rejected(self):
        with pytest.raises(ValueError):
            descriptive_statistics([])

    def test_non_finite_rejected(self):
        with pytest.raises(ValueError):
            descriptive_statistics([1.0, float("nan")])
        with pytest.raises(ValueError):
            descriptive_statistics([1.0, float("inf")])

    def test_non_numeric_rejected(self):
        with pytest.raises(ValueError):
            descriptive_statistics([1.0, "2.0"])


class TestTDistribution:
    def test_quantile_reference_values(self):
        references = {
            1: 12.706205,
            2: 4.302653,
            4: 2.776445,
            10: 2.228139,
            30: 2.042272,
        }
        for df, expected in references.items():
            assert abs(t_quantile(0.975, df) - expected) < 1e-5

    def test_two_sided_p_reference(self):
        # t = 2.776445 with df=4 is the 97.5% critical value -> two-sided p=0.05
        assert abs(t_two_sided_p_value(2.7764451051977987, 4) - 0.05) < 1e-6

    def test_cdf_symmetry(self):
        assert abs(t_cdf(1.5, 7) + t_cdf(-1.5, 7) - 1.0) < 1e-12
        assert abs(t_cdf(0.0, 7) - 0.5) < 1e-12

    def test_quantile_bounds(self):
        assert t_quantile(0.025, 5) < 0.0 < t_quantile(0.975, 5)
        assert abs(t_quantile(0.5, 9) - 0.0) < 1e-9

    def test_quantile_invalid_inputs(self):
        with pytest.raises(ValueError):
            t_quantile(0.0, 4)
        with pytest.raises(ValueError):
            t_quantile(0.95, 0)

    def test_incomplete_beta_known_values(self):
        assert abs(regularized_incomplete_beta(1.0, 1.0, 0.3) - 0.3) < 1e-12
        assert abs(regularized_incomplete_beta(2.0, 2.0, 0.5) - 0.5) < 1e-12
        assert regularized_incomplete_beta(2.0, 3.0, 0.0) == 0.0
        assert regularized_incomplete_beta(2.0, 3.0, 1.0) == 1.0


class TestConfidenceInterval:
    def test_known_interval(self):
        result = confidence_interval_t([1.0, 2.0, 3.0, 4.0, 5.0], 0.95)
        assert result["status"] == "ok"
        assert result["method"] == "student_t_interval"
        assert result["std_dev_convention"] == SAMPLE_STD_CONVENTION
        assert abs(result["lower"] - 1.0368) < 0.001
        assert abs(result["upper"] - 4.9632) < 0.001
        assert result["lower"] < result["mean"] < result["upper"]

    def test_n1_omitted(self):
        result = confidence_interval_t([7.0], 0.95)
        assert result["status"] == "omitted"
        assert "at least 2" in result["reason"]
        assert result.get("lower") is None

    def test_zero_variance_degenerate_interval(self):
        result = confidence_interval_t([5.0, 5.0, 5.0], 0.95)
        assert result["status"] == "ok"
        assert result["lower"] == result["upper"] == 5.0

    def test_wider_interval_for_higher_confidence(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        ci90 = confidence_interval_t(values, 0.90)
        ci99 = confidence_interval_t(values, 0.99)
        assert (ci99["upper"] - ci99["lower"]) > (ci90["upper"] - ci90["lower"])

    def test_invalid_level(self):
        with pytest.raises(ValueError):
            confidence_interval_t([1.0, 2.0], 1.5)


class TestPairedTTest:
    def test_known_statistic_and_p(self):
        result = paired_t_test([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result["status"] == "ok"
        assert abs(result["statistic"] - 4.2426406871) < 1e-6
        assert abs(result["p_value"] - 0.01323) < 1e-4
        assert result["degrees_of_freedom"] == 4
        assert result["sample_count"] == 5
        assert result["std_dev_convention"] == SAMPLE_STD_CONVENTION

    def test_one_sided_is_half_of_two_sided_for_symmetric_case(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        two_sided = paired_t_test(values, alternative="two-sided")
        greater = paired_t_test(values, alternative="greater")
        less = paired_t_test(values, alternative="less")
        # observed direction is positive, so the greater p is half of two-sided
        assert abs(greater["p_value"] * 2 - two_sided["p_value"]) < 1e-9
        assert abs(greater["p_value"] + less["p_value"] - 1.0) < 1e-9
        assert greater["p_value"] < less["p_value"]

    def test_zero_variance_undefined(self):
        result = paired_t_test([4.0, 4.0, 4.0])
        assert result["status"] == "undefined"
        assert result["statistic"] is None
        assert result["p_value"] is None
        assert "zero variance" in result["reason"]

    def test_insufficient_sample(self):
        with pytest.raises(ValueError):
            paired_t_test([1.0])

    def test_invalid_alternative(self):
        with pytest.raises(ValueError):
            paired_t_test([1.0, 2.0], alternative="sideways")

    def test_deterministic_repeat(self):
        values = [0.5, -1.0, 3.25, 2.0]
        assert paired_t_test(values) == paired_t_test(values)


class TestWilcoxonSignedRank:
    def test_all_positive_n5_exact(self):
        result = wilcoxon_signed_rank([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result["status"] == "ok"
        assert result["statistic"] == 15.0
        assert result["p_value"] == 0.0625
        assert result["method"] == "exact_sign_enumeration"
        assert result["sample_count"] == 5

    def test_exact_matches_brute_force(self):
        vectors = [
            [1.0, -2.0, 3.0, -4.0, 5.0],
            [2.5, 2.5, -1.0, 4.0, -3.5, 0.5],
            [-1.0, -2.0, -3.0],
            [1.0, 1.0, 2.0, -2.0, 5.0],
        ]
        for values in vectors:
            result = wilcoxon_signed_rank(values)
            brute_p = _brute_force_wilcoxon(values, result["alternative"])
            assert abs(result["p_value"] - brute_p) < 1e-12, values
            assert result["statistic"] == _reference_w_plus(
                [v for v in values if v != 0]
            ), values

    def test_brute_force_cross_check_statistic(self):
        values = [1.0, -2.0, 3.0, -4.0, 5.0]
        result = wilcoxon_signed_rank(values)
        nonzero = [v for v in values if v != 0]
        expected_w_plus = _reference_w_plus(nonzero)
        assert result["statistic"] == expected_w_plus

    def test_zero_differences_excluded_and_reported(self):
        result = wilcoxon_signed_rank([0.0, 0.0, 1.0, 2.0])
        assert result["status"] == "ok"
        assert result["sample_count"] == 2
        assert result["excluded_zero_differences"] == 2

    def test_all_zeros_undefined(self):
        result = wilcoxon_signed_rank([0.0, 0.0])
        assert result["status"] == "undefined"
        assert result["p_value"] is None

    def test_one_nonzero_undefined(self):
        result = wilcoxon_signed_rank([0.0, 3.0])
        assert result["status"] == "undefined"
        assert "at least 2 non-zero" in result["reason"]

    def test_normal_approximation_beyond_exact_cap(self):
        values = [float(i) for i in range(1, WILCOXON_EXACT_MAX_N + 2)]
        result = wilcoxon_signed_rank(values)
        assert result["status"] == "ok"
        assert result["method"] == "normal_approximation_continuity_correction"
        assert 0.0 <= result["p_value"] <= 1.0

    def test_deterministic_repeat(self):
        values = [1.0, -2.0, 3.0, 4.0, -5.0, 6.0]
        assert wilcoxon_signed_rank(values) == wilcoxon_signed_rank(values)


class TestEffectSizes:
    def test_cohens_dz_known(self):
        result = cohens_dz([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result["status"] == "ok"
        assert abs(result["value"] - 1.8973665961) < 1e-9
        assert result["std_dev_convention"] == SAMPLE_STD_CONVENTION

    def test_cohens_dz_zero_variance(self):
        result = cohens_dz([4.0, 4.0])
        assert result["status"] == "undefined"
        assert result["value"] is None

    def test_cohens_dz_relationship_to_t(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        dz = cohens_dz(values)["value"]
        t = paired_t_test(values)["statistic"]
        assert abs(dz - t / math.sqrt(5)) < 1e-9

    def test_rank_biserial_all_positive(self):
        result = rank_biserial([1.0, 2.0, 3.0])
        assert result["status"] == "ok"
        assert result["value"] == 1.0

    def test_rank_biserial_all_negative(self):
        result = rank_biserial([-1.0, -2.0, -3.0])
        assert result["value"] == -1.0

    def test_rank_biserial_mixed(self):
        result = rank_biserial([1.0, -1.0, 2.0, -2.0])
        assert result["value"] == 0.0

    def test_rank_biserial_too_few_nonzero(self):
        result = rank_biserial([0.0, 1.0])
        assert result["status"] == "undefined"


def _reference_w_plus(nonzero_values):
    from app.engines.analytics.statistics import _average_ranks

    ranks = _average_ranks([abs(v) for v in nonzero_values])
    return sum(r for v, r in zip(nonzero_values, ranks) if v > 0)


def _brute_force_wilcoxon(values, alternative):
    """Independent reference: enumerate all 2^n sign assignments."""
    nonzero = [v for v in values if v != 0]
    from app.engines.analytics.statistics import _average_ranks

    ranks = _average_ranks([abs(v) for v in nonzero])
    n = len(nonzero)
    observed = sum(r for v, r in zip(nonzero, ranks) if v > 0)
    total = 2 ** n
    count_le = 0
    count_ge = 0
    for signs in itertools.product([0, 1], repeat=n):
        w = sum(r for s, r in zip(signs, ranks) if s == 1)
        if w <= observed + 1e-9:
            count_le += 1
        if w >= observed - 1e-9:
            count_ge += 1
    p_less = count_le / total
    p_greater = count_ge / total
    if alternative == "greater":
        return p_greater
    if alternative == "less":
        return p_less
    return min(1.0, 2.0 * min(p_less, p_greater))
