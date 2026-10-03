import itertools
import math
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.research import DefenseAmplificationResult, InteractionResult
from app.repositories.research_repo import EnergyMeasurementRepository
from app.services.research_service import ResearchExperimentService
from app.services.defense_energy_amplification_service import (
    DefenseEnergyAmplificationService,
)
from app.services.interaction_effect_service import InteractionEffectService
from app.services.marginal_energy_service import MarginalEnergyService
from app.services.research_analytics_service import (
    ANALYSIS_VERSION,
    ResearchAnalyticsService,
    AnalyticsInsufficientDataError,
    AnalyticsValidationError,
    _group_value,
)
from app.schemas.research import ResearchAnalyticsFilters, ResearchAnalyticsRequest
from app.engines.analytics.statistics import (
    POPULATION_STD_CONVENTION,
    SAMPLE_STD_CONVENTION,
    descriptive_statistics,
    paired_t_test,
)


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    session = sessionmaker(bind=db_engine)()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def research_svc(db_session):
    return ResearchExperimentService(db_session)


@pytest.fixture
def analytics_svc(db_session):
    return ResearchAnalyticsService(db_session)


@pytest.fixture
def amp_svc(db_session):
    return DefenseEnergyAmplificationService(db_session)


@pytest.fixture
def int_svc(db_session):
    return InteractionEffectService(db_session)


@pytest.fixture
def marginal_svc(db_session):
    return MarginalEnergyService(db_session)


def _run_experiment(svc, attack, intensity, controls, duration=30, trials=1,
                    experiment_type="DEFENSE_AMPLIFICATION"):
    config = {
        "name": f"{attack}_{intensity}_{'_'.join(controls) or 'baseline'}",
        "experiment_type": experiment_type,
        "attack_type": attack,
        "attack_intensity": intensity,
        "security_controls": controls,
        "duration_seconds": duration,
        "number_of_trials": trials,
    }
    exp = svc.create_experiment(config)
    svc.execute_experiment(exp.experiment_uuid)
    runs = svc.get_experiment_runs(exp.experiment_uuid)
    return exp, runs


def _pair(research_svc, attack="ddos", intensity="low", duration=30, trials=1,
          control="firewall"):
    exp_b, runs_b = _run_experiment(research_svc, attack, intensity, [], duration, trials)
    exp_d, runs_d = _run_experiment(research_svc, attack, intensity, [control], duration, trials)
    return {
        "experiments": (exp_b, exp_d),
        "baseline_run_ids": [r.id for r in runs_b],
        "defense_run_ids": [r.id for r in runs_d],
        "control_name": control,
    }


def _set_energies(db, run_ids, energies):
    repo = EnergyMeasurementRepository(db)
    for run_id, energy in zip(run_ids, energies):
        measurement = repo.get_latest_by_run(run_id)
        measurement.energy_joules = energy
    db.commit()


def _seed_amplification(db, amp_svc, research_svc, trials=3, attack="ddos",
                        intensity="low", control="firewall", defense_energies=None):
    pair = _pair(research_svc, attack=attack, intensity=intensity, trials=trials,
                 control=control)
    _set_energies(db, pair["baseline_run_ids"], [100.0] * trials)
    _set_energies(
        db,
        pair["defense_run_ids"],
        defense_energies if defense_energies is not None
        else [160.0, 200.0, 240.0][:trials],
    )
    response = amp_svc.compute_amplification(
        baseline_run_ids=pair["baseline_run_ids"],
        defense_run_ids=pair["defense_run_ids"],
        control_name=pair["control_name"],
    )
    return response, pair


def _seed_interaction(db, int_svc, research_svc, trials=2, attack="ddos"):
    kwargs = {"experiment_type": "INTERACTION"}
    exp_b, runs_b = _run_experiment(research_svc, attack, "low", [], 30, trials, **kwargs)
    exp_a, runs_a = _run_experiment(research_svc, attack, "low", ["firewall"], 30, trials, **kwargs)
    exp_c, runs_c = _run_experiment(research_svc, attack, "low", ["ids"], 30, trials, **kwargs)
    exp_x, runs_x = _run_experiment(
        research_svc, attack, "low", ["firewall", "ids"], 30, trials, **kwargs
    )
    b_ids = [r.id for r in runs_b]
    a_ids = [r.id for r in runs_a]
    c_ids = [r.id for r in runs_c]
    x_ids = [r.id for r in runs_x]
    _set_energies(db, b_ids, [1000.0] * trials)
    _set_energies(db, a_ids, [1100.0] * trials)
    _set_energies(db, c_ids, [1150.0] * trials)
    _set_energies(db, x_ids, [1300.0, 1400.0][:trials])
    response = int_svc.compute_interaction_effects(
        baseline_run_ids=b_ids,
        control_a_run_ids=a_ids,
        control_b_run_ids=c_ids,
        combined_run_ids=x_ids,
        control_a="firewall",
        control_b="ids",
    )
    return response


def _seed_attribution(db, marginal_svc, research_svc, trials=2, attack="ddos"):
    kwargs = {"experiment_type": "MARGINAL_ENERGY"}
    exp_b, runs_b = _run_experiment(research_svc, attack, "low", [], 30, trials, **kwargs)
    exp_s, runs_s = _run_experiment(research_svc, attack, "low", ["firewall"], 30, trials, **kwargs)
    b_ids = [r.id for r in runs_b]
    s_ids = [r.id for r in runs_s]
    _set_energies(db, b_ids, [100.0] * trials)
    _set_energies(db, s_ids, [160.0, 210.0][:trials])
    for b_id, s_id in zip(b_ids, s_ids):
        marginal_svc.compute_pair(experiment_id=exp_b.id, baseline_run_id=b_id,
                                  security_run_id=s_id)
    return b_ids, s_ids


_seq = itertools.count(1)


def _amp_row(db, **overrides):
    idx = next(_seq)
    defaults = dict(
        experiment_id=idx,
        control_name="firewall",
        attack_type="ddos",
        attack_intensity="low",
        attack_workload=500.0,
        workload_unit="packets_per_second",
        energy_attack_only=5000.0,
        energy_attack_defense=5100.0,
        additional_defense_energy=100.0,
        defense_energy_amplification=0.2,
        measurement_mode="ESTIMATED",
        trial_number=1,
        baseline_run_id=100000 + idx,
        defense_run_id=200000 + idx,
        energy_provider="estimated",
        duration_seconds=30.0,
        formula_version="defense_energy_amplification_v1",
    )
    defaults.update(overrides)
    row = DefenseAmplificationResult(**defaults)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _interaction_row(db, **overrides):
    idx = next(_seq)
    defaults = dict(
        experiment_id=idx,
        control_a="firewall",
        control_b="ids",
        energy_baseline=1000.0,
        energy_a=1100.0,
        energy_b=1150.0,
        energy_ab=1300.0,
        interaction_effect=50.0,
        interaction_power=1.666,
        attack_type="ddos",
        attack_intensity="low",
        measurement_mode="ESTIMATED",
        trial_number=1,
        baseline_run_id=100000 + idx,
        control_a_run_id=110000 + idx,
        control_b_run_id=120000 + idx,
        combined_run_id=130000 + idx,
        workload_unit="packets_per_second",
        energy_provider="estimated",
        formula_version="interaction_effect_v1",
    )
    defaults.update(overrides)
    row = InteractionResult(**defaults)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _req(source, metric, **kwargs):
    return ResearchAnalyticsRequest(source=source, metric=metric, **kwargs)


class TestDescriptiveStatistics:
    def test_count_mean_median_std_min_max(self, analytics_svc, db_session,
                                            research_svc, amp_svc):
        _, _ = _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        stats = response.statistics
        assert stats.count == 3
        assert stats.mean == 100.0
        assert stats.median == 100.0
        assert stats.min == 60.0
        assert stats.max == 140.0
        expected = descriptive_statistics([60.0, 100.0, 140.0])
        assert abs(stats.std_dev - expected["std_dev"]) < 1e-12
        assert response.std_dev_convention == POPULATION_STD_CONVENTION

    def test_convention_matches_phase6_helper(self):
        from app.services.interaction_effect_service import (
            descriptive_statistics as phase6_stats,
        )

        values = [60.0, 100.0, 140.0]
        mine = descriptive_statistics(values)
        theirs = phase6_stats(values)
        assert mine["std_dev"] == theirs["std_dev"]
        assert mine["mean"] == theirs["mean"]

    def test_single_observation(self, analytics_svc, db_session, research_svc,
                                 amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=1)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.n == 1
        assert response.statistics.std_dev == 0.0
        assert response.statistics.mean == 60.0

    def test_metric_category_reported(self, analytics_svc, db_session, research_svc,
                                       amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        diff = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        ratio = analytics_svc.analyze(
            _req("amplification", "defense_energy_amplification")
        )
        level = analytics_svc.analyze(_req("amplification", "energy_attack_only"))
        assert diff.metric_category == "difference"
        assert ratio.metric_category == "ratio"
        assert level.metric_category == "level"
        assert diff.paired_differences == [60.0, 100.0]
        assert level.paired_differences is None


class TestGroupedAnalysis:
    def test_groups_by_attack_type(self, analytics_svc, db_session, research_svc,
                                   amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2, attack="ddos")
        _seed_amplification(db_session, amp_svc, research_svc, trials=3,
                            attack="port_scan")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 group_by=["attack_type"], include_confidence_interval=False)
        )
        assert len(response.groups) == 2
        assert [g.group["attack_type"] for g in response.groups] == [
            "ddos", "port_scan"
        ]
        assert response.groups[0].n == 2
        assert response.groups[1].n == 3
        assert response.groups[0].statistics.mean == 80.0  # (60+100)/2
        assert response.groups[1].statistics.mean == 100.0
        assert response.n == 5

    def test_groups_sorted_deterministically(self, analytics_svc, db_session,
                                              research_svc, amp_svc):
        for attack in ("sql_injection", "malware", "brute_force"):
            _seed_amplification(db_session, amp_svc, research_svc, trials=1,
                                attack=attack)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 group_by=["attack_type"], include_confidence_interval=False)
        )
        keys = [g.group["attack_type"] for g in response.groups]
        assert keys == sorted(keys)

    def test_group_with_single_observation_has_omitted_ci(self, analytics_svc,
                                                           db_session, research_svc,
                                                           amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3, attack="ddos")
        _seed_amplification(db_session, amp_svc, research_svc, trials=1,
                            attack="port_scan")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 group_by=["attack_type"])
        )
        singles = [g for g in response.groups if g.n == 1]
        assert singles
        assert singles[0].confidence_interval.status == "omitted"
        assert any("at least 2" in w for w in singles[0].warnings)

    def test_group_by_control_name(self, analytics_svc, db_session, research_svc,
                                    amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=1, control="ids")
        _seed_amplification(db_session, amp_svc, research_svc, trials=2,
                            control="firewall")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 group_by=["control_name"], include_confidence_interval=False)
        )
        assert [g.group["control_name"] for g in response.groups] == [
            "firewall", "ids"
        ]


class TestPairedAnalysis:
    def test_paired_differences_are_existing_phase7_values(self, analytics_svc,
                                                            db_session, research_svc,
                                                            amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.paired_differences == [60.0, 100.0, 140.0]

    def test_paired_t_test_matches_engine(self, analytics_svc, db_session,
                                           research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="paired_t")
        )
        test = response.hypothesis_test
        expected = paired_t_test([60.0, 100.0, 140.0])
        assert test is not None
        assert test.status == "ok"
        assert test.test_id == "paired_t"
        assert test.statistic == expected["statistic"]
        assert test.p_value == expected["p_value"]
        assert test.sample_count == 3
        assert test.degrees_of_freedom == 2
        assert test.null_hypothesis == "Mean paired difference = 0"
        assert test.alternative_hypothesis == "Mean paired difference != 0"
        assert test.interpretation in ("reject_null", "fail_to_reject_null")
        assert test.reject_null == (test.p_value < test.significance_level)

    def test_directional_alternatives(self, analytics_svc, db_session, research_svc,
                                      amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        greater = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="paired_t", alternative="greater")
        )
        less = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="paired_t", alternative="less")
        )
        assert greater.hypothesis_test.alternative_hypothesis == (
            "Mean paired difference > 0"
        )
        assert less.hypothesis_test.alternative_hypothesis == (
            "Mean paired difference < 0"
        )
        assert greater.hypothesis_test.p_value < less.hypothesis_test.p_value

    def test_wilcoxon_exact(self, analytics_svc, db_session, research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="wilcoxon_signed_rank")
        )
        test = response.hypothesis_test
        assert test.status == "ok"
        assert test.test_id == "wilcoxon_signed_rank"
        assert test.statistic == 6.0
        assert test.p_value == 0.25
        assert test.reject_null is False
        assert test.interpretation == "fail_to_reject_null"
        assert test.method == "exact_sign_enumeration"
        assert test.effect_size.name == "rank_biserial_correlation"
        assert test.effect_size.value == 1.0

    def test_effect_size_cohens_dz(self, analytics_svc, db_session, research_svc,
                                   amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="paired_t")
        )
        effect = response.hypothesis_test.effect_size
        assert effect.name == "cohens_dz"
        assert abs(effect.value - 2.5) < 1e-9  # 100 / 40
        assert effect.convention.startswith("Cohen's dz")
        assert any("does not imply statistical significance" in w
                   for w in response.warnings)

    def test_paired_analysis_on_attribution_source(self, analytics_svc, db_session,
                                                    research_svc, marginal_svc):
        _seed_attribution(db_session, marginal_svc, research_svc, trials=2)
        response = analytics_svc.analyze(
            _req("marginal", "marginal_energy_joules", hypothesis_test="paired_t")
        )
        assert response.n == 2
        assert response.paired_differences == [60.0, 110.0]
        assert response.hypothesis_test.status == "ok"
        assert response.source == "marginal"


class TestConfidenceInterval:
    def test_interval_contains_mean(self, analytics_svc, db_session, research_svc,
                                    amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        ci = response.confidence_interval
        assert ci.status == "ok"
        assert ci.level == 0.95
        assert ci.method == "student_t_interval"
        assert ci.std_dev_convention == SAMPLE_STD_CONVENTION
        assert ci.lower < response.statistics.mean < ci.upper
        assert ci.degrees_of_freedom == 2

    def test_n1_omitted_with_warning(self, analytics_svc, db_session, research_svc,
                                      amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=1)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.confidence_interval.status == "omitted"
        assert response.confidence_interval.lower is None
        assert any("at least 2" in w for w in response.warnings)

    def test_disabled_by_request(self, analytics_svc, db_session, research_svc,
                                 amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 include_confidence_interval=False)
        )
        assert response.confidence_interval is None

    def test_custom_confidence_level(self, analytics_svc, db_session, research_svc,
                                     amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy", confidence_level=0.99)
        )
        assert response.confidence_interval.level == 0.99

    def test_small_sample_handling_n1_with_test(self, analytics_svc, db_session,
                                                 research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=1)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="paired_t")
        )
        assert response.hypothesis_test is None
        assert any("at least 2 paired observations" in w for w in response.warnings)


class TestHypothesisTestValidation:
    def test_level_metric_rejected_for_test(self, analytics_svc, db_session,
                                            research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        with pytest.raises(AnalyticsValidationError, match="level metric"):
            analytics_svc.analyze(
                _req("amplification", "energy_attack_only", hypothesis_test="paired_t")
            )

    def test_unknown_metric_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="Invalid metric"):
            analytics_svc.analyze(_req("amplification", "nonsense_metric"))

    def test_metric_from_wrong_source_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="Invalid metric"):
            analytics_svc.analyze(_req("marginal", "interaction_effect"))

    def test_unknown_source_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="Invalid source"):
            analytics_svc.analyze(_req("quantum", "marginal_energy_joules"))

    def test_unknown_hypothesis_test_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="Invalid hypothesis test"):
            analytics_svc.analyze(
                _req("marginal", "marginal_energy_joules", hypothesis_test="magic")
            )

    def test_invalid_alternative_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="Invalid alternative"):
            analytics_svc.analyze(
                _req("marginal", "marginal_energy_joules", hypothesis_test="paired_t",
                     alternative="sideways")
            )

    def test_unsupported_filter_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="not supported for source"):
            analytics_svc.analyze(
                _req("amplification", "additional_defense_energy",
                     filters={"control_a": "firewall"})
            )

    def test_unsupported_group_dimension_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="Group dimension"):
            analytics_svc.analyze(
                _req("marginal", "marginal_energy_joules", group_by=["control_name"])
            )

    def test_duplicate_group_dimensions_rejected(self, analytics_svc):
        with pytest.raises(AnalyticsValidationError, match="duplicate dimensions"):
            analytics_svc.analyze(
                _req("marginal", "marginal_energy_joules",
                     group_by=["attack_type", "attack_type"])
            )


class TestDataQuality:
    def test_empty_dataset(self, analytics_svc):
        with pytest.raises(AnalyticsInsufficientDataError, match="Insufficient"):
            analytics_svc.analyze(
                _req("amplification", "additional_defense_energy",
                     filters={"experiment_id": 999999})
            )

    def test_missing_metric_value(self, analytics_svc, db_session):
        row = _interaction_row(db_session, interaction_power=None)
        with pytest.raises(AnalyticsValidationError, match="Missing metric value"):
            analytics_svc.analyze(
                _req("interaction", "interaction_power",
                     filters={"experiment_id": row.experiment_id})
            )

    def test_invalid_numeric_value(self, analytics_svc, db_session):
        row = _amp_row(db_session, additional_defense_energy=float("inf"))
        with pytest.raises(AnalyticsValidationError, match="Invalid numeric data"):
            analytics_svc.analyze(
                _req("amplification", "additional_defense_energy",
                     filters={"experiment_id": row.experiment_id})
            )

    def test_mismatched_workload_units(self, analytics_svc, db_session):
        _amp_row(db_session, workload_unit="packets_per_second")
        _amp_row(db_session, workload_unit="requests_per_second")
        with pytest.raises(AnalyticsValidationError, match="Mismatched workload units"):
            analytics_svc.analyze(
                _req("amplification", "defense_energy_amplification")
            )

    def test_mixed_measurement_modes(self, analytics_svc, db_session):
        _amp_row(db_session, measurement_mode="ESTIMATED")
        _amp_row(db_session, measurement_mode="SIMULATED")
        with pytest.raises(AnalyticsValidationError, match="Mixed measurement modes"):
            analytics_svc.analyze(_req("amplification", "additional_defense_energy"))

    def test_mixed_energy_providers(self, analytics_svc, db_session):
        _interaction_row(db_session, energy_provider="estimated")
        _interaction_row(db_session, energy_provider="rapl")
        with pytest.raises(AnalyticsValidationError, match="Mixed energy providers"):
            analytics_svc.analyze(_req("interaction", "interaction_effect"))

    def test_unpaired_observations_rejected(self, analytics_svc, db_session):
        _amp_row(db_session, baseline_run_id=None, defense_run_id=None)
        _amp_row(db_session, baseline_run_id=None, defense_run_id=None)
        with pytest.raises(AnalyticsValidationError, match="Unpaired observations"):
            analytics_svc.analyze(
                _req("amplification", "additional_defense_energy",
                     hypothesis_test="paired_t")
            )

    def test_unpaired_allowed_without_paired_analysis(self, analytics_svc, db_session):
        _amp_row(db_session, baseline_run_id=None, defense_run_id=None)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.n == 1
        assert response.hypothesis_test is None

    def test_duplicate_observations_rejected(self, analytics_svc, db_session):
        _amp_row(db_session, experiment_id=777, trial_number=1, control_name="firewall")
        _amp_row(db_session, experiment_id=777, trial_number=1, control_name="firewall")
        with pytest.raises(AnalyticsValidationError, match="Duplicate observations"):
            analytics_svc.analyze(_req("amplification", "additional_defense_energy"))

    def test_zero_workload_for_ratio_metric(self, analytics_svc, db_session):
        _amp_row(db_session, attack_workload=0.0)
        with pytest.raises(AnalyticsValidationError, match="non-positive workload"):
            analytics_svc.analyze(
                _req("amplification", "defense_energy_amplification")
            )

    def test_mixed_workload_units_warned_for_non_workload_metric(
        self, analytics_svc, db_session
    ):
        _amp_row(db_session, workload_unit="packets_per_second")
        _amp_row(db_session, workload_unit="login_attempts")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.n == 2
        assert any("mismatched workload units" in w for w in response.warnings)


class TestMixedAttackContexts:
    def test_overall_inferential_omitted_with_warning(self, analytics_svc, db_session,
                                                       research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3, attack="ddos")
        _seed_amplification(db_session, amp_svc, research_svc, trials=3,
                            attack="port_scan")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="paired_t")
        )
        assert response.hypothesis_test is None
        assert response.confidence_interval.status == "omitted"
        assert any("mixed attack contexts" in w for w in response.warnings)

    def test_grouping_enables_per_group_tests(self, analytics_svc, db_session,
                                               research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3, attack="ddos")
        _seed_amplification(db_session, amp_svc, research_svc, trials=3,
                            attack="port_scan")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 group_by=["attack_type"], hypothesis_test="paired_t")
        )
        assert len(response.groups) == 2
        for group in response.groups:
            assert group.hypothesis_test is not None
            assert group.hypothesis_test.status == "ok"

    def test_descriptive_only_mixed_context_warns(self, analytics_svc, db_session,
                                                   research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2, attack="ddos")
        _seed_amplification(db_session, amp_svc, research_svc, trials=2,
                            attack="port_scan")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.n == 4
        assert any("mixed attack contexts" in w or "attack" in w
                   for w in response.warnings)


class TestReproducibility:
    def test_deterministic_repeat(self, analytics_svc, db_session, research_svc,
                                  amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        request = _req("amplification", "additional_defense_energy",
                       hypothesis_test="paired_t", group_by=["control_name"])
        first = analytics_svc.analyze(request)
        second = analytics_svc.analyze(request)
        assert first.analysis_id == second.analysis_id
        assert first.statistics == second.statistics
        assert first.hypothesis_test.p_value == second.hypothesis_test.p_value
        assert first.confidence_interval.lower == second.confidence_interval.lower
        assert first.paired_differences == second.paired_differences

    def test_analysis_id_stable_and_formatted(self, analytics_svc, db_session,
                                               research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.analysis_id.startswith("anl_")
        assert len(response.analysis_id) == 20
        assert response.analysis_version == ANALYSIS_VERSION

    def test_different_configuration_different_id(self, analytics_svc, db_session,
                                                   research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        first = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        second = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy", confidence_level=0.99)
        )
        assert first.analysis_id != second.analysis_id

    def test_analysis_id_ignores_row_order(self, analytics_svc, db_session,
                                            research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        request = _req("amplification", "additional_defense_energy")
        response = analytics_svc.analyze(request)
        assert response.analysis_id == analytics_svc.analyze(request).analysis_id


class TestPersistence:
    def test_roundtrip_get_and_list(self, analytics_svc, db_session, research_svc,
                                    amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        created = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        fetched = analytics_svc.get_analysis(created.analysis_id)
        assert fetched is not None
        assert fetched.analysis_id == created.analysis_id
        assert fetched.statistics == created.statistics

        listed = analytics_svc.list_analyses(source="amplification")
        assert listed.total >= 1
        assert any(i.analysis_id == created.analysis_id for i in listed.items)

    def test_get_unknown_returns_none(self, analytics_svc):
        assert analytics_svc.get_analysis("anl_doesnotexist") is None

    def test_list_filter_by_metric(self, analytics_svc, db_session, research_svc,
                                   amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        analytics_svc.analyze(_req("amplification", "additional_defense_energy"))
        listed = analytics_svc.list_analyses(metric="additional_defense_energy")
        assert listed.total >= 1
        assert all(i.metric == "additional_defense_energy" for i in listed.items)

    def test_update_existing_row_on_repeat(self, analytics_svc, db_session,
                                           research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        first = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        count_before = analytics_svc.analytics_repo.count()
        second = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert second.analysis_id == first.analysis_id
        assert analytics_svc.analytics_repo.count() == count_before


class TestResponseMetadata:
    def test_filters_echoed(self, analytics_svc, db_session, research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 filters={"attack_type": "ddos", "attack_intensity": "low"})
        )
        assert response.filters == {"attack_type": "ddos",
                                     "attack_intensity": "low"}

    def test_measurement_mode_and_provider_recorded(self, analytics_svc, db_session,
                                                     research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.measurement_mode == "ESTIMATED"
        assert response.energy_provider == "estimated"

    def test_estimated_limitation_present(self, analytics_svc, db_session,
                                           research_svc, amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=2)
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert any("ESTIMATED" in item for item in response.limitations)
        assert any("does not convert estimated energy" in item
                   for item in response.limitations)

    def test_undefined_test_when_zero_variance(self, analytics_svc, db_session,
                                                research_svc, amp_svc):
        # identical defense energies -> identical paired differences -> zero variance
        _seed_amplification(db_session, amp_svc, research_svc, trials=3,
                            defense_energies=[160.0, 160.0, 160.0])
        result = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="paired_t")
        )
        assert result.hypothesis_test.status == "undefined"
        assert result.hypothesis_test.p_value is None
        assert result.hypothesis_test.interpretation == "undefined"
        assert "zero variance" in result.hypothesis_test.reason


class TestCarbonPerWorkloadMetrics:
    """Phase 10: carbon-per-attack-workload is derived at read time."""

    def test_amplification_metric_derived_from_stored_fields(
        self, analytics_svc, db_session
    ):
        _amp_row(db_session, amplification_carbon_kg=0.5, attack_workload=500.0)
        _amp_row(db_session, amplification_carbon_kg=1.5, attack_workload=500.0)
        response = analytics_svc.analyze(
            _req("amplification", "defense_carbon_per_workload")
        )
        assert response.metric_category == "ratio"
        assert response.statistics.count == 2
        assert response.statistics.mean == pytest.approx((0.5 + 1.5) / 2 / 500.0)

    def test_interaction_metric_derived_from_stored_fields(
        self, analytics_svc, db_session
    ):
        _interaction_row(
            db_session, interaction_carbon_kg=0.25, workload_value=100.0
        )
        _interaction_row(
            db_session, interaction_carbon_kg=0.5, workload_value=100.0
        )
        response = analytics_svc.analyze(
            _req("interaction", "interaction_carbon_per_workload")
        )
        assert response.statistics.mean == pytest.approx(
            (0.25 + 0.5) / 2 / 100.0
        )

    def test_marginal_metric_matches_stored_carbon(
        self, analytics_svc, db_session, research_svc, marginal_svc
    ):
        from app.models.research import EnergyAttribution

        _seed_attribution(db_session, marginal_svc, research_svc, trials=2)
        response = analytics_svc.analyze(
            _req("marginal", "marginal_carbon_per_workload")
        )
        rows = db_session.query(EnergyAttribution).all()
        expected = [r.marginal_carbon_kg / r.workload_value for r in rows]
        assert response.statistics.count == len(expected)
        assert response.statistics.mean == pytest.approx(sum(expected) / len(expected))

    def test_zero_workload_rejected_with_reason(self, analytics_svc, db_session):
        _amp_row(db_session, amplification_carbon_kg=0.5, attack_workload=0.0)
        with pytest.raises(AnalyticsValidationError) as exc:
            analytics_svc.analyze(_req("amplification", "defense_carbon_per_workload"))
        assert "carbon-per-workload" in str(exc.value)
        assert "zero" in str(exc.value)

    def test_missing_carbon_rejected_with_reason(self, analytics_svc, db_session):
        _amp_row(db_session, amplification_carbon_kg=None, attack_workload=500.0)
        with pytest.raises(AnalyticsValidationError) as exc:
            analytics_svc.analyze(_req("amplification", "defense_carbon_per_workload"))
        assert "not available" in str(exc.value)

    def test_mismatched_workload_units_rejected(self, analytics_svc, db_session):
        _amp_row(db_session, amplification_carbon_kg=0.5, attack_workload=500.0)
        _amp_row(
            db_session,
            amplification_carbon_kg=0.5,
            attack_workload=500.0,
            workload_unit="requests_per_second",
        )
        with pytest.raises(AnalyticsValidationError) as exc:
            analytics_svc.analyze(_req("amplification", "defense_carbon_per_workload"))
        assert "workload units" in str(exc.value)

    def test_derived_metric_is_not_persisted_as_column(
        self, analytics_svc, db_session
    ):
        _amp_row(db_session, amplification_carbon_kg=0.5, attack_workload=500.0)
        analytics_svc.analyze(_req("amplification", "defense_carbon_per_workload"))
        row = db_session.query(DefenseAmplificationResult).first()
        assert not hasattr(row, "defense_carbon_per_workload")

    def test_derived_metric_limitation_documented(
        self, analytics_svc, db_session
    ):
        _amp_row(db_session, amplification_carbon_kg=0.5, attack_workload=500.0)
        response = analytics_svc.analyze(
            _req("amplification", "defense_carbon_per_workload")
        )
        assert any(
            "Carbon per workload is a derived ratio" in item
            for item in response.limitations
        )
        assert any("not from grid telemetry" in item for item in response.limitations)


class TestGroupValue:
    def test_none_is_unknown(self):
        row = SimpleNamespace(attack_type=None)
        assert _group_value(row, "attack_type") == "unknown"

    def test_nan_float(self):
        row = SimpleNamespace(attack_workload=float("nan"))
        assert _group_value(row, "attack_workload") == "nan"

    def test_integral_float(self):
        row = SimpleNamespace(attack_workload=3.0)
        assert _group_value(row, "attack_workload") == "3"

    def test_fractional_float(self):
        row = SimpleNamespace(attack_workload=3.5)
        assert _group_value(row, "attack_workload") == "3.5"

    def test_non_float_stringified(self):
        row = SimpleNamespace(attack_type=7)
        assert _group_value(row, "attack_type") == "7"


class TestWilcoxonDirectionalHypotheses:
    def test_directional_alternatives(self, analytics_svc, db_session, research_svc,
                                      amp_svc):
        _seed_amplification(db_session, amp_svc, research_svc, trials=3)
        greater = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="wilcoxon_signed_rank", alternative="greater")
        )
        less = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 hypothesis_test="wilcoxon_signed_rank", alternative="less")
        )
        assert greater.hypothesis_test.alternative_hypothesis == (
            "Median paired difference > 0"
        )
        assert less.hypothesis_test.alternative_hypothesis == (
            "Median paired difference < 0"
        )
        assert greater.hypothesis_test.p_value < less.hypothesis_test.p_value


class TestGroupHypothesisWarnings:
    def test_single_observation_group_omits_test(self, analytics_svc, db_session):
        _amp_row(db_session, attack_type="ddos")
        _amp_row(db_session, attack_type="ddos")
        _amp_row(db_session, attack_type="port_scan")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 group_by=["attack_type"], hypothesis_test="paired_t")
        )
        groups = {g.group["attack_type"]: g for g in response.groups}
        assert groups["ddos"].hypothesis_test is not None
        assert groups["port_scan"].hypothesis_test is None
        assert any(
            "at least 2 paired observations (n=1)" in w
            for w in groups["port_scan"].warnings
        )

    def test_mixed_context_group_omits_test(self, analytics_svc, db_session):
        _amp_row(db_session, control_name="firewall", attack_type="ddos")
        _amp_row(db_session, control_name="firewall", attack_type="port_scan")
        _amp_row(db_session, control_name="ids", attack_type="ddos")
        _amp_row(db_session, control_name="ids", attack_type="ddos")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 group_by=["control_name"], hypothesis_test="paired_t")
        )
        groups = {g.group["control_name"]: g for g in response.groups}
        assert groups["firewall"].hypothesis_test is None
        assert any(
            "mixed attack contexts" in w for w in groups["firewall"].warnings
        )
        assert groups["ids"].hypothesis_test is not None


class TestPostFetchFilters:
    def test_workload_unit_filter_excludes_rows(self, analytics_svc, db_session):
        _amp_row(db_session, workload_unit="packets_per_second")
        _amp_row(db_session, workload_unit="requests_per_second")
        _amp_row(db_session, workload_unit="packets_per_second")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 filters=ResearchAnalyticsFilters(
                     workload_unit="packets_per_second"))
        )
        assert response.n == 2

    def test_energy_provider_filter_excludes_rows(self, analytics_svc, db_session):
        _amp_row(db_session, energy_provider="estimated")
        _amp_row(db_session, energy_provider="custom_model")
        _amp_row(db_session, energy_provider="estimated")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy",
                 filters=ResearchAnalyticsFilters(energy_provider="estimated"))
        )
        assert response.n == 2


class TestProvenanceLimitations:
    def test_simulated_mode_limitation(self, analytics_svc, db_session):
        _amp_row(db_session, measurement_mode="SIMULATED")
        _amp_row(db_session, measurement_mode="SIMULATED")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.limitations[0].startswith("Energy values are SIMULATED")

    def test_measured_mode_limitation(self, analytics_svc, db_session):
        _amp_row(db_session, measurement_mode="MEASURED",
                 energy_provider="hardware_monitor")
        _amp_row(db_session, measurement_mode="MEASURED",
                 energy_provider="hardware_monitor")
        response = analytics_svc.analyze(
            _req("amplification", "additional_defense_energy")
        )
        assert response.limitations[0].startswith("Energy values are MEASURED")
