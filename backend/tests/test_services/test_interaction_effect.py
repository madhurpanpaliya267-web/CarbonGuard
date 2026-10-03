import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.research import InteractionResult
from app.services.research_service import ResearchExperimentService
from app.services.interaction_effect_service import (
    InteractionEffectService,
    InteractionEffectError,
    calculate_interaction_values,
    descriptive_statistics,
    FORMULA_VERSION,
    JOULES_PER_KWH,
)
from app.repositories.research_repo import (
    ExperimentRepository,
    ExperimentRunRepository,
    EnergyMeasurementRepository,
)
from app.engines.carbon.carbon_calculator import calculate_carbon
from app.config import settings


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def research_svc(db_session):
    return ResearchExperimentService(db_session)


@pytest.fixture
def interaction_svc(db_session):
    return InteractionEffectService(db_session)


def _run_experiment(
    svc,
    attack_type,
    intensity,
    controls,
    duration=30,
    trials=1,
):
    config = {
        "name": f"{attack_type}_{intensity}_{'_'.join(controls) or 'baseline'}",
        "experiment_type": "INTERACTION",
        "attack_type": attack_type,
        "attack_intensity": intensity,
        "security_controls": controls,
        "duration_seconds": duration,
        "number_of_trials": trials,
    }
    exp = svc.create_experiment(config)
    svc.execute_experiment(exp.experiment_uuid)
    runs = svc.get_experiment_runs(exp.experiment_uuid)
    return exp, runs


def _quartet(
    research_svc,
    attack="ddos",
    intensity="low",
    duration=30,
    trials=1,
    controls=("firewall", "ids"),
):
    exp_b, runs_b = _run_experiment(
        research_svc, attack, intensity, [], duration, trials
    )
    exp_a, runs_a = _run_experiment(
        research_svc, attack, intensity, [controls[0]], duration, trials
    )
    exp_c, runs_c = _run_experiment(
        research_svc, attack, intensity, [controls[1]], duration, trials
    )
    exp_ab, runs_ab = _run_experiment(
        research_svc, attack, intensity, list(controls), duration, trials
    )
    return {
        "experiments": (exp_b, exp_a, exp_c, exp_ab),
        "runs": (runs_b, runs_a, runs_c, runs_ab),
        "baseline_run_ids": [r.id for r in runs_b],
        "control_a_run_ids": [r.id for r in runs_a],
        "control_b_run_ids": [r.id for r in runs_c],
        "combined_run_ids": [r.id for r in runs_ab],
        "control_a": controls[0],
        "control_b": controls[1],
    }


def _set_energies(db, run_ids, energies):
    repo = EnergyMeasurementRepository(db)
    for run_id, energy in zip(run_ids, energies):
        measurement = repo.get_latest_by_run(run_id)
        measurement.energy_joules = energy
    db.commit()


def _compute(interaction_svc, quartet, **kwargs):
    params = {
        "baseline_run_ids": quartet["baseline_run_ids"],
        "control_a_run_ids": quartet["control_a_run_ids"],
        "control_b_run_ids": quartet["control_b_run_ids"],
        "combined_run_ids": quartet["combined_run_ids"],
        "control_a": quartet["control_a"],
        "control_b": quartet["control_b"],
    }
    params.update(kwargs)
    return interaction_svc.compute_interaction_effects(**params)


class TestFormula:
    def test_super_additive_spec_example(self):
        result = calculate_interaction_values(100, 120, 130, 270, 60)
        assert result["interaction_effect"] == 120
        assert result["interaction_index"] == 1.2
        assert result["interpretation"] == "super-additive"

    def test_approximately_additive_spec_example(self):
        result = calculate_interaction_values(100, 120, 130, 150, 60)
        assert result["interaction_effect"] == 0
        assert result["interaction_index"] == 0.0
        assert result["interpretation"] == "approximately additive"

    def test_negative_interaction(self):
        result = calculate_interaction_values(100, 120, 130, 110, 60)
        assert result["interaction_effect"] == -40
        assert result["interaction_index"] == -0.4
        assert result["interpretation"] == "sub-additive"

    def test_zero_baseline_index_is_none(self):
        result = calculate_interaction_values(0, 10, 10, 25, 60)
        assert result["interaction_effect"] == 5
        assert result["interaction_index"] is None

    def test_negative_interaction_index(self):
        result = calculate_interaction_values(100, 120, 130, 105, 60)
        assert result["interaction_effect"] == -45
        assert result["interaction_index"] == -0.45
        assert result["interpretation"] == "sub-additive"

    def test_power_values(self):
        result = calculate_interaction_values(100, 120, 130, 270, 10)
        assert result["power_baseline"] == 10.0
        assert result["power_a"] == 12.0
        assert result["power_b"] == 13.0
        assert result["power_ab"] == 27.0
        assert result["interaction_power"] == 12.0
        assert result["interaction_power"] == result["interaction_effect"] / 10

    def test_carbon_values_use_existing_methodology(self):
        intensity = 475
        result = calculate_interaction_values(100, 120, 130, 270, 60, intensity)
        expected_c0 = calculate_carbon(100 / JOULES_PER_KWH, intensity, 0)
        expected_cab = calculate_carbon(270 / JOULES_PER_KWH, intensity, 0)
        assert result["carbon_baseline_kg"] == expected_c0["gross_co2_kg"]
        assert result["carbon_ab_kg"] == expected_cab["gross_co2_kg"]
        expected_interaction = (
            result["carbon_ab_kg"]
            - result["carbon_a_kg"]
            - result["carbon_b_kg"]
            + result["carbon_baseline_kg"]
        )
        assert abs(result["interaction_carbon_kg"] - expected_interaction) < 1e-12

    def test_default_carbon_intensity(self):
        result = calculate_interaction_values(100, 120, 130, 270, 60)
        assert result["carbon_intensity"] == settings.DEFAULT_CARBON_INTENSITY

    def test_formula_version(self):
        assert FORMULA_VERSION == "interaction_effect_v1"

    def test_zero_duration_power_is_zero(self):
        result = calculate_interaction_values(100, 120, 130, 270, 0)
        assert result["interaction_power"] == 0.0
        assert result["power_baseline"] == 0.0

    def test_descriptive_statistics(self):
        stats = descriptive_statistics([50, 100, 150])
        assert stats["mean"] == 100
        assert stats["median"] == 100
        assert stats["min"] == 50
        assert stats["max"] == 150
        assert stats["count"] == 3
        assert abs(stats["std_dev"] - math.sqrt(5000 / 3)) < 1e-9

    def test_descriptive_statistics_single_value(self):
        stats = descriptive_statistics([42.0])
        assert stats["mean"] == 42.0
        assert stats["median"] == 42.0
        assert stats["std_dev"] == 0.0
        assert stats["count"] == 1


class TestCompute:
    def test_single_trial_persisted(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        response = _compute(interaction_svc, quartet)

        assert response.total == 1
        row = response.results[0]
        assert row.id is not None
        assert row.formula_version == "interaction_effect_v1"
        assert row.trial_number == 1
        assert row.baseline_run_id == quartet["baseline_run_ids"][0]
        assert row.control_a_run_id == quartet["control_a_run_ids"][0]
        assert row.control_b_run_id == quartet["control_b_run_ids"][0]
        assert row.combined_run_id == quartet["combined_run_ids"][0]
        assert row.control_a == "firewall"
        assert row.control_b == "ids"

        persisted = interaction_svc.get_interaction_effect(row.id)
        assert persisted is not None
        assert persisted.interaction_effect == row.interaction_effect

    def test_energy_values_match_measurements(
        self, interaction_svc, research_svc, db_session
    ):
        quartet = _quartet(research_svc)
        response = _compute(interaction_svc, quartet)
        row = response.results[0]

        measurement_repo = EnergyMeasurementRepository(db_session)
        e0 = measurement_repo.get_latest_by_run(
            quartet["baseline_run_ids"][0]
        ).energy_joules
        ea = measurement_repo.get_latest_by_run(
            quartet["control_a_run_ids"][0]
        ).energy_joules
        eb = measurement_repo.get_latest_by_run(
            quartet["control_b_run_ids"][0]
        ).energy_joules
        eab = measurement_repo.get_latest_by_run(
            quartet["combined_run_ids"][0]
        ).energy_joules

        assert row.energy_baseline == e0
        assert row.energy_a == ea
        assert row.energy_b == eb
        assert row.energy_ab == eab

    def test_interaction_formula_holds(
        self, interaction_svc, research_svc
    ):
        quartet = _quartet(research_svc)
        row = _compute(interaction_svc, quartet).results[0]
        expected = row.energy_ab - row.energy_a - row.energy_b + row.energy_baseline
        assert abs(row.interaction_effect - expected) < 1e-9

    def test_interaction_index_holds(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        row = _compute(interaction_svc, quartet).results[0]
        if row.energy_baseline > 0:
            expected = row.interaction_effect / row.energy_baseline
            assert abs(row.interaction_index - expected) < 1e-12

    def test_estimated_provider_is_additive(
        self, interaction_svc, research_svc
    ):
        quartet = _quartet(research_svc)
        row = _compute(interaction_svc, quartet).results[0]
        assert row.interaction_effect == 0
        assert row.interpretation == "approximately additive"

    def test_measurement_mode_preserved(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        row = _compute(interaction_svc, quartet).results[0]
        assert row.measurement_mode == "ESTIMATED"

    def test_energy_provider_recorded(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        row = _compute(interaction_svc, quartet).results[0]
        assert row.energy_provider == "estimated"

    def test_context_preserved(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc, attack="brute_force", intensity="medium")
        row = _compute(interaction_svc, quartet).results[0]
        assert row.attack_type == "brute_force"
        assert row.attack_intensity == "medium"
        assert row.workload_value is not None
        assert row.workload_unit is not None
        assert row.duration_seconds == 30.0

    def test_carbon_values_persisted(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        row = _compute(interaction_svc, quartet).results[0]

        assert row.carbon_baseline_kg == calculate_carbon(
            row.energy_baseline / JOULES_PER_KWH, row.carbon_intensity, 0
        )["gross_co2_kg"]
        assert row.carbon_a_kg is not None
        assert row.carbon_b_kg is not None
        assert row.carbon_ab_kg is not None
        expected = (
            row.carbon_ab_kg - row.carbon_a_kg - row.carbon_b_kg + row.carbon_baseline_kg
        )
        assert abs(row.interaction_carbon_kg - expected) < 1e-12

    def test_security_effectiveness_exposed(
        self, interaction_svc, research_svc
    ):
        quartet = _quartet(research_svc)
        response = _compute(interaction_svc, quartet)
        effectiveness = response.results[0].security_effectiveness

        assert effectiveness is not None
        assert effectiveness.baseline is not None
        assert effectiveness.control_a is not None
        assert effectiveness.control_b is not None
        assert effectiveness.combined is not None
        assert effectiveness.baseline.detection_rate is not None
        assert effectiveness.control_a.controls_active == '["firewall"]'
        assert effectiveness.combined.controls_active == '["firewall", "ids"]'

    def test_statistics_in_response(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        response = _compute(interaction_svc, quartet)
        stats = response.statistics
        assert stats.formula_version == "interaction_effect_v1"
        assert stats.interaction_energy.count == 1
        assert stats.interaction_energy.mean == response.results[0].interaction_effect
        assert stats.interaction_power.count == 1
        assert stats.interaction_carbon.count == 1

    def test_arbitrary_control_pair(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc, controls=("waf", "siem"))
        response = _compute(interaction_svc, quartet)
        assert response.results[0].control_a == "waf"
        assert response.results[0].control_b == "siem"
        assert response.total == 1

    def test_third_control_pair(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc, controls=("encryption", "logging"))
        response = _compute(interaction_svc, quartet)
        assert response.results[0].control_a == "encryption"
        assert response.results[0].control_b == "logging"

    def test_control_ids_normalized(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc, controls=("firewall", "ids"))
        response = _compute(
            interaction_svc, quartet, control_a="Firewall", control_b="IDS"
        )
        assert response.results[0].control_a == "firewall"
        assert response.results[0].control_b == "ids"

    def test_experiment_id_from_baseline(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        response = _compute(interaction_svc, quartet)
        baseline_exp = quartet["experiments"][0]
        assert response.results[0].experiment_id == baseline_exp.id

    def test_experiment_id_override(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        target_exp = quartet["experiments"][3]
        response = _compute(interaction_svc, quartet, experiment_id=target_exp.id)
        assert response.results[0].experiment_id == target_exp.id

    def test_context_conditioning_supported(self, interaction_svc, research_svc):
        for intensity in ("low", "medium", "high"):
            quartet = _quartet(research_svc, intensity=intensity)
            row = _compute(interaction_svc, quartet).results[0]
            assert row.attack_intensity == intensity
            assert row.interaction_effect == 0


class TestSyntheticEnergies:
    def test_super_additive_end_to_end(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        _set_energies(
            db_session,
            quartet["baseline_run_ids"], [100.0],
        )
        _set_energies(db_session, quartet["control_a_run_ids"], [120.0])
        _set_energies(db_session, quartet["control_b_run_ids"], [130.0])
        _set_energies(db_session, quartet["combined_run_ids"], [270.0])

        row = _compute(interaction_svc, quartet).results[0]
        assert row.interaction_effect == 120
        assert row.interaction_index == 1.2
        assert row.interpretation == "super-additive"
        assert row.power_baseline == 100.0 / 30
        assert abs(row.interaction_power - 120.0 / 30) < 1e-9

    def test_sub_additive_end_to_end(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        _set_energies(db_session, quartet["baseline_run_ids"], [100.0])
        _set_energies(db_session, quartet["control_a_run_ids"], [120.0])
        _set_energies(db_session, quartet["control_b_run_ids"], [130.0])
        _set_energies(db_session, quartet["combined_run_ids"], [110.0])

        row = _compute(interaction_svc, quartet).results[0]
        assert row.interaction_effect == -40
        assert row.interaction_index == -0.4
        assert row.interpretation == "sub-additive"


class TestMultipleTrials:
    def test_three_paired_trials_statistics(
        self, interaction_svc, research_svc, db_session
    ):
        quartet = _quartet(research_svc, trials=3)
        _set_energies(db_session, quartet["baseline_run_ids"], [100.0, 100.0, 100.0])
        _set_energies(db_session, quartet["control_a_run_ids"], [120.0, 120.0, 120.0])
        _set_energies(db_session, quartet["control_b_run_ids"], [130.0, 130.0, 130.0])
        _set_energies(db_session, quartet["combined_run_ids"], [200.0, 250.0, 300.0])

        response = _compute(interaction_svc, quartet)

        assert response.total == 3
        interactions = [r.interaction_effect for r in response.results]
        assert interactions == [50.0, 100.0, 150.0]
        assert [r.trial_number for r in response.results] == [1, 2, 3]

        stats = response.statistics.interaction_energy
        assert stats.count == 3
        assert stats.mean == 100.0
        assert stats.median == 100.0
        assert stats.min == 50.0
        assert stats.max == 150.0
        assert abs(stats.std_dev - math.sqrt(5000 / 3)) < 1e-9

    def test_power_statistics_scale_with_energy(
        self, interaction_svc, research_svc, db_session
    ):
        quartet = _quartet(research_svc, trials=3, duration=30)
        _set_energies(db_session, quartet["baseline_run_ids"], [100.0, 100.0, 100.0])
        _set_energies(db_session, quartet["control_a_run_ids"], [120.0, 120.0, 120.0])
        _set_energies(db_session, quartet["control_b_run_ids"], [130.0, 130.0, 130.0])
        _set_energies(db_session, quartet["combined_run_ids"], [200.0, 250.0, 300.0])

        response = _compute(interaction_svc, quartet)
        energy_stats = response.statistics.interaction_energy
        power_stats = response.statistics.interaction_power
        assert abs(power_stats.mean - energy_stats.mean / 30) < 1e-9
        assert power_stats.count == 3

    def test_carbon_statistics_count(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc, trials=3)
        response = _compute(interaction_svc, quartet)
        carbon_stats = response.statistics.interaction_carbon
        assert carbon_stats.count == 3
        expected_mean = sum(
            r.interaction_carbon_kg for r in response.results
        ) / 3
        assert abs(carbon_stats.mean - expected_mean) < 1e-12

    def test_unpaired_lists_rejected(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc, trials=2)
        with pytest.raises(InteractionEffectError, match="Run count mismatch"):
            _compute(
                interaction_svc,
                quartet,
                combined_run_ids=quartet["combined_run_ids"][:1],
            )

    def test_misaligned_trial_numbers_rejected(
        self, interaction_svc, research_svc
    ):
        quartet = _quartet(research_svc, trials=2)
        reversed_a = list(reversed(quartet["control_a_run_ids"]))
        with pytest.raises(InteractionEffectError, match="Trial mismatch"):
            _compute(interaction_svc, quartet, control_a_run_ids=reversed_a)


class TestDeterminism:
    def test_repeated_computation_identical(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        first = _compute(interaction_svc, quartet).results[0]
        second = _compute(interaction_svc, quartet).results[0]

        assert first.interaction_effect == second.interaction_effect
        assert first.interaction_index == second.interaction_index
        assert first.interaction_power == second.interaction_power
        assert first.interaction_carbon_kg == second.interaction_carbon_kg
        assert first.energy_baseline == second.energy_baseline
        assert first.energy_ab == second.energy_ab

    def test_repeated_statistics_identical(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc, trials=2)
        first = _compute(interaction_svc, quartet).statistics
        second = _compute(interaction_svc, quartet).statistics
        assert first.interaction_energy.mean == second.interaction_energy.mean
        assert first.interaction_energy.std_dev == second.interaction_energy.std_dev
        assert first.interaction_carbon.max == second.interaction_carbon.max


class TestValidation:
    def test_attack_type_mismatch(self, interaction_svc, research_svc):
        baseline = _quartet(research_svc, attack="ddos")
        other = _quartet(research_svc, attack="port_scan")
        with pytest.raises(InteractionEffectError, match="Attack type mismatch"):
            _compute(
                interaction_svc,
                baseline,
                control_a_run_ids=other["control_a_run_ids"],
                control_b_run_ids=other["control_b_run_ids"],
                combined_run_ids=other["combined_run_ids"],
            )

    def test_attack_intensity_mismatch(self, interaction_svc, research_svc):
        baseline = _quartet(research_svc, intensity="low")
        other = _quartet(research_svc, intensity="high")
        with pytest.raises(InteractionEffectError, match="Attack intensity mismatch"):
            _compute(
                interaction_svc,
                baseline,
                control_a_run_ids=other["control_a_run_ids"],
                control_b_run_ids=other["control_b_run_ids"],
                combined_run_ids=other["combined_run_ids"],
            )

    def test_workload_value_mismatch(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        run = run_repo.get_by_id(quartet["control_a_run_ids"][0])
        run_repo.update(run, {"workload_value": run.workload_value + 100})
        with pytest.raises(InteractionEffectError, match="Workload value mismatch"):
            _compute(interaction_svc, quartet)

    def test_workload_unit_mismatch(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        run = run_repo.get_by_id(quartet["control_a_run_ids"][0])
        run_repo.update(run, {"workload_unit": "requests_per_second"})
        with pytest.raises(InteractionEffectError, match="Workload unit mismatch"):
            _compute(interaction_svc, quartet)

    def test_duration_mismatch(self, interaction_svc, research_svc):
        baseline = _quartet(research_svc, duration=30)
        other = _quartet(research_svc, duration=60)
        with pytest.raises(InteractionEffectError, match="Duration mismatch"):
            _compute(
                interaction_svc,
                baseline,
                control_b_run_ids=other["control_b_run_ids"],
            )

    def test_provider_mismatch(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        measurement_repo = EnergyMeasurementRepository(db_session)
        measurement = measurement_repo.get_latest_by_run(
            quartet["control_a_run_ids"][0]
        )
        measurement_repo.update(measurement, {"source": "rapl"})
        with pytest.raises(InteractionEffectError, match="Energy provider mismatch"):
            _compute(interaction_svc, quartet)

    def test_measurement_mode_mismatch(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        run = run_repo.get_by_id(quartet["control_b_run_ids"][0])
        run_repo.update(run, {"measurement_mode": "SIMULATED"})
        with pytest.raises(InteractionEffectError, match="Measurement mode mismatch"):
            _compute(interaction_svc, quartet)

    def test_environment_mismatch(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        exp_repo = ExperimentRepository(db_session)
        exp_repo.update(quartet["experiments"][1], {"software_version": "0.0.0-test"})
        with pytest.raises(InteractionEffectError, match="Environment mismatch"):
            _compute(interaction_svc, quartet)

    def test_missing_baseline_ids(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(InteractionEffectError, match="Missing baseline run ids"):
            _compute(interaction_svc, quartet, baseline_run_ids=[])

    def test_missing_control_a_ids(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(InteractionEffectError, match="Missing control A run ids"):
            _compute(interaction_svc, quartet, control_a_run_ids=[])

    def test_missing_control_b_ids(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(InteractionEffectError, match="Missing control B run ids"):
            _compute(interaction_svc, quartet, control_b_run_ids=[])

    def test_missing_combined_ids(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(InteractionEffectError, match="Missing combined run ids"):
            _compute(interaction_svc, quartet, combined_run_ids=[])

    def test_baseline_run_not_found(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(
            InteractionEffectError, match="baseline run not found: 999999"
        ):
            _compute(interaction_svc, quartet, baseline_run_ids=[999999])

    def test_control_a_run_not_found(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(
            InteractionEffectError, match="control_a run not found: 999999"
        ):
            _compute(interaction_svc, quartet, control_a_run_ids=[999999])

    def test_control_b_run_not_found(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(
            InteractionEffectError, match="control_b run not found: 999999"
        ):
            _compute(interaction_svc, quartet, control_b_run_ids=[999999])

    def test_combined_run_not_found(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(
            InteractionEffectError, match="combined run not found: 999999"
        ):
            _compute(interaction_svc, quartet, combined_run_ids=[999999])

    def test_missing_energy_measurement(self, interaction_svc, research_svc, db_session):
        quartet = _quartet(research_svc)
        measurement_repo = EnergyMeasurementRepository(db_session)
        measurement = measurement_repo.get_latest_by_run(
            quartet["control_b_run_ids"][0]
        )
        measurement_repo.delete(measurement)
        with pytest.raises(
            InteractionEffectError,
            match="No energy measurement found for control_b run",
        ):
            _compute(interaction_svc, quartet)

    def test_unknown_control_rejected(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(InteractionEffectError, match="Unknown security control"):
            _compute(interaction_svc, quartet, control_a="quantum_shield")

    def test_same_control_rejected(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc, controls=("firewall", "ids"))
        with pytest.raises(
            InteractionEffectError, match="must be two different controls"
        ):
            _compute(interaction_svc, quartet, control_b="firewall")

    def test_experiment_not_found(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        with pytest.raises(InteractionEffectError, match="Experiment not found"):
            _compute(interaction_svc, quartet, experiment_id=999999)

    def test_nothing_persisted_on_validation_failure(
        self, interaction_svc, research_svc, db_session
    ):
        baseline = _quartet(research_svc)
        other = _quartet(research_svc, attack="brute_force")
        before = interaction_svc.interaction_repo.count()

        with pytest.raises(InteractionEffectError):
            _compute(
                interaction_svc,
                baseline,
                control_a_run_ids=other["control_a_run_ids"],
                control_b_run_ids=other["control_b_run_ids"],
                combined_run_ids=other["combined_run_ids"],
            )

        assert interaction_svc.interaction_repo.count() == before


class TestListing:
    def test_list_and_filter(self, interaction_svc, research_svc):
        quartet = _quartet(research_svc)
        _compute(interaction_svc, quartet)

        all_items = interaction_svc.list_interaction_effects()
        assert all_items.total >= 1

        filtered = interaction_svc.list_interaction_effects(
            attack_type="ddos", control_a="firewall", control_b="ids"
        )
        assert filtered.total >= 1
        assert all(item.control_a == "firewall" for item in filtered.items)

        empty = interaction_svc.list_interaction_effects(
            attack_type="malware", control_a="waf"
        )
        assert empty.total == 0

    def test_get_missing_returns_none(self, interaction_svc):
        assert interaction_svc.get_interaction_effect(999999) is None


class TestEnvironmentAndEffectiveness:
    def test_environment_key_without_experiment(self):
        assert InteractionEffectService._environment_key(None) == "unknown"

    def test_effectiveness_for_missing_runs(self, interaction_svc):
        row = InteractionResult(
            baseline_run_id=None,
            control_a_run_id=999999,
            control_b_run_id=None,
            combined_run_id=None,
        )
        response = interaction_svc._effectiveness_for(row)
        assert response.baseline is None
        assert response.control_a is None
        assert response.control_b is None
        assert response.combined is None
