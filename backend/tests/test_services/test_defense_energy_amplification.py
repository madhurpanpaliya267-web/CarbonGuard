import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.services.research_service import ResearchExperimentService
from app.services.defense_energy_amplification_service import (
    DefenseEnergyAmplificationService,
    DefenseEnergyAmplificationError,
    calculate_amplification_values,
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
def amplification_svc(db_session):
    return DefenseEnergyAmplificationService(db_session)


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
        "experiment_type": "DEFENSE_AMPLIFICATION",
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


def _pair(
    research_svc,
    attack="ddos",
    intensity="low",
    duration=30,
    trials=1,
    control="firewall",
    defense_controls=None,
):
    exp_b, runs_b = _run_experiment(research_svc, attack, intensity, [], duration, trials)
    exp_d, runs_d = _run_experiment(
        research_svc,
        attack,
        intensity,
        defense_controls if defense_controls is not None else [control],
        duration,
        trials,
    )
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


def _compute(amplification_svc, pair, **kwargs):
    params = {
        "baseline_run_ids": pair["baseline_run_ids"],
        "defense_run_ids": pair["defense_run_ids"],
        "control_name": pair["control_name"],
    }
    params.update(kwargs)
    return amplification_svc.compute_amplification(**params)


class TestFormula:
    def test_ade_calculation(self):
        result = calculate_amplification_values(5000, 5100, 500, 30)
        assert result["additional_defense_energy"] == 100

    def test_dea_calculation(self):
        result = calculate_amplification_values(5000, 5100, 500, 30)
        assert result["defense_energy_amplification"] == 0.2

    def test_zero_ade(self):
        result = calculate_amplification_values(5000, 5000, 500, 30)
        assert result["additional_defense_energy"] == 0
        assert result["defense_energy_amplification"] == 0

    def test_negative_ade_allowed(self):
        result = calculate_amplification_values(5000, 4900, 500, 30)
        assert result["additional_defense_energy"] == -100
        assert result["defense_energy_amplification"] == -0.2

    def test_power_amplification(self):
        result = calculate_amplification_values(5000, 5100, 500, 10)
        assert result["power_baseline"] == 500.0
        assert result["power_defense"] == 510.0
        assert result["power_amplification"] == 10.0
        assert result["power_amplification"] == (
            result["additional_defense_energy"] / 10
        )

    def test_carbon_calculation_uses_existing_methodology(self):
        intensity = 475
        result = calculate_amplification_values(5000, 5100, 500, 30, intensity)
        expected_baseline = calculate_carbon(5000 / JOULES_PER_KWH, intensity, 0)
        expected_defense = calculate_carbon(5100 / JOULES_PER_KWH, intensity, 0)
        assert result["carbon_baseline_kg"] == expected_baseline["gross_co2_kg"]
        assert result["carbon_defense_kg"] == expected_defense["gross_co2_kg"]
        assert (
            abs(
                result["amplification_carbon_kg"]
                - (
                    expected_defense["gross_co2_kg"]
                    - expected_baseline["gross_co2_kg"]
                )
            )
            < 1e-12
        )

    def test_default_carbon_intensity(self):
        result = calculate_amplification_values(5000, 5100, 500, 30)
        assert result["carbon_intensity"] == settings.DEFAULT_CARBON_INTENSITY

    def test_zero_workload_rejected(self):
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Zero workload"
        ):
            calculate_amplification_values(5000, 5100, 0, 30)

    def test_negative_workload_rejected(self):
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Invalid workload value: -5"
        ):
            calculate_amplification_values(5000, 5100, -5, 30)

    def test_none_workload_rejected(self):
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Invalid workload: None"
        ):
            calculate_amplification_values(5000, 5100, None, 30)

    def test_negative_energy_rejected(self):
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Negative baseline energy"
        ):
            calculate_amplification_values(-1, 5100, 500, 30)
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Negative defense energy"
        ):
            calculate_amplification_values(5000, -1, 500, 30)

    def test_invalid_duration_rejected(self):
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Invalid duration"
        ):
            calculate_amplification_values(5000, 5100, 500, 0)

    def test_formula_version(self):
        assert FORMULA_VERSION == "defense_energy_amplification_v1"


class TestCompute:
    def test_single_pair_persisted(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        response = _compute(amplification_svc, pair)

        assert response.total == 1
        row = response.results[0]
        assert row.id is not None
        assert row.formula_version == "defense_energy_amplification_v1"
        assert row.trial_number == 1
        assert row.num_paired_trials == 1
        assert row.baseline_run_id == pair["baseline_run_ids"][0]
        assert row.defense_run_id == pair["defense_run_ids"][0]
        assert row.control_name == "firewall"

    def test_ade_matches_measurements(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]

        measurement_repo = EnergyMeasurementRepository(db_session)
        baseline = measurement_repo.get_latest_by_run(
            pair["baseline_run_ids"][0]
        ).energy_joules
        defense = measurement_repo.get_latest_by_run(
            pair["defense_run_ids"][0]
        ).energy_joules

        assert row.energy_attack_only == baseline
        assert row.energy_attack_defense == defense
        assert row.additional_defense_energy == defense - baseline

    def test_dea_matches_ade_over_workload(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        expected = row.additional_defense_energy / row.attack_workload
        assert abs(row.defense_energy_amplification - expected) < 1e-12

    def test_engine_pair_is_amplified(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        assert row.additional_defense_energy > 0
        assert row.defense_energy_amplification > 0
        assert row.power_amplification > 0

    def test_workload_unit_preserved(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        assert row.workload_unit == "packets_per_second"
        assert row.attack_workload == 500.0

    def test_context_preserved(self, amplification_svc, research_svc):
        pair = _pair(research_svc, attack="brute_force", intensity="medium")
        row = _compute(amplification_svc, pair).results[0]
        assert row.attack_type == "brute_force"
        assert row.attack_intensity == "medium"
        assert row.duration_seconds == 30.0

    def test_measurement_mode_and_provider(
        self, amplification_svc, research_svc
    ):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        assert row.measurement_mode == "ESTIMATED"
        assert row.energy_provider == "estimated"

    def test_environment_recorded(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        baseline_exp = pair["experiments"][0]
        assert row.software_version == baseline_exp.software_version
        assert row.configuration_version == baseline_exp.configuration_version

    def test_carbon_values_persisted(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        assert row.carbon_baseline_kg == calculate_carbon(
            row.energy_attack_only / JOULES_PER_KWH, row.carbon_intensity, 0
        )["gross_co2_kg"]
        assert row.carbon_defense_kg == calculate_carbon(
            row.energy_attack_defense / JOULES_PER_KWH, row.carbon_intensity, 0
        )["gross_co2_kg"]
        expected = row.carbon_defense_kg - row.carbon_baseline_kg
        assert abs(row.amplification_carbon_kg - expected) < 1e-12

    def test_carbon_intensity_parameter(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair, carbon_intensity=300).results[0]
        assert row.carbon_intensity == 300
        assert row.carbon_baseline_kg == calculate_carbon(
            row.energy_attack_only / JOULES_PER_KWH, 300, 0
        )["gross_co2_kg"]

    def test_statistics_present(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        response = _compute(amplification_svc, pair)
        stats = response.statistics
        assert stats.formula_version == "defense_energy_amplification_v1"
        assert stats.amplification_energy.count == 1
        assert stats.amplification_energy.mean == (
            response.results[0].additional_defense_energy
        )
        assert stats.amplification_ratio.count == 1
        assert stats.amplification_ratio.mean == (
            response.results[0].defense_energy_amplification
        )
        assert stats.power_amplification.count == 1
        assert stats.carbon_amplification.count == 1

    def test_statistics_stored_on_row(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        assert row.statistics is not None
        assert row.statistics.amplification_energy.count == 1
        assert row.statistics.formula_version == "defense_energy_amplification_v1"

    def test_negative_ade_persisted(self, amplification_svc, research_svc, db_session):
        pair = _pair(research_svc)
        _set_energies(db_session, pair["baseline_run_ids"], [5000.0])
        _set_energies(db_session, pair["defense_run_ids"], [4900.0])
        row = _compute(amplification_svc, pair).results[0]
        assert row.additional_defense_energy == -100
        assert row.defense_energy_amplification == -0.2
        assert abs(row.power_amplification - (-100.0 / 30)) < 1e-9

    def test_experiment_id_from_baseline(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(amplification_svc, pair).results[0]
        assert row.experiment_id == pair["experiments"][0].id

    def test_experiment_id_override(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        row = _compute(
            amplification_svc, pair, experiment_id=pair["experiments"][1].id
        ).results[0]
        assert row.experiment_id == pair["experiments"][1].id

    def test_other_control_pairs(self, amplification_svc, research_svc):
        for control in ("ids", "waf", "siem", "encryption"):
            pair = _pair(research_svc, control=control)
            row = _compute(amplification_svc, pair).results[0]
            assert row.control_name == control

    def test_control_normalized(self, amplification_svc, research_svc):
        pair = _pair(research_svc, control="firewall")
        row = _compute(amplification_svc, pair, control_name="Firewall").results[0]
        assert row.control_name == "firewall"


class TestMultipleTrials:
    def test_three_paired_trials(self, amplification_svc, research_svc, db_session):
        pair = _pair(research_svc, trials=3)
        _set_energies(db_session, pair["baseline_run_ids"], [100.0, 100.0, 100.0])
        _set_energies(db_session, pair["defense_run_ids"], [160.0, 200.0, 240.0])

        response = _compute(amplification_svc, pair)

        assert response.total == 3
        ades = [r.additional_defense_energy for r in response.results]
        assert ades == [60.0, 100.0, 140.0]
        assert [r.trial_number for r in response.results] == [1, 2, 3]
        assert all(r.num_paired_trials == 3 for r in response.results)

        deas = [r.defense_energy_amplification for r in response.results]
        assert deas == [0.12, 0.2, 0.28]

    def test_ade_statistics(self, amplification_svc, research_svc, db_session):
        pair = _pair(research_svc, trials=3)
        _set_energies(db_session, pair["baseline_run_ids"], [100.0, 100.0, 100.0])
        _set_energies(db_session, pair["defense_run_ids"], [160.0, 200.0, 240.0])

        stats = _compute(amplification_svc, pair).statistics.amplification_energy
        assert stats.count == 3
        assert stats.mean == 100.0
        assert stats.median == 100.0
        assert stats.min == 60.0
        assert stats.max == 140.0
        assert abs(stats.std_dev - math.sqrt(3200 / 3)) < 1e-9

    def test_dea_statistics(self, amplification_svc, research_svc, db_session):
        pair = _pair(research_svc, trials=3)
        _set_energies(db_session, pair["baseline_run_ids"], [100.0, 100.0, 100.0])
        _set_energies(db_session, pair["defense_run_ids"], [160.0, 200.0, 240.0])

        stats = _compute(amplification_svc, pair).statistics.amplification_ratio
        assert stats.count == 3
        assert abs(stats.mean - 0.2) < 1e-12
        assert abs(stats.median - 0.2) < 1e-12
        assert abs(stats.min - 0.12) < 1e-12
        assert abs(stats.max - 0.28) < 1e-12
        assert abs(stats.std_dev - math.sqrt(3200 / 3) / 500) < 1e-12

    def test_power_and_carbon_statistics(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc, trials=3)
        _set_energies(db_session, pair["baseline_run_ids"], [100.0, 100.0, 100.0])
        _set_energies(db_session, pair["defense_run_ids"], [160.0, 200.0, 240.0])

        response = _compute(amplification_svc, pair)
        assert response.statistics.power_amplification.count == 3
        assert response.statistics.carbon_amplification.count == 3
        expected_power_mean = response.statistics.amplification_energy.mean / 30
        assert abs(
            response.statistics.power_amplification.mean - expected_power_mean
        ) < 1e-9

    def test_count_mismatch_rejected(self, amplification_svc, research_svc):
        pair = _pair(research_svc, trials=2)
        with pytest.raises(DefenseEnergyAmplificationError, match="Run count mismatch"):
            _compute(
                amplification_svc,
                pair,
                defense_run_ids=pair["defense_run_ids"][:1],
            )

    def test_trial_misalignment_rejected(self, amplification_svc, research_svc):
        pair = _pair(research_svc, trials=2)
        reversed_defense = list(reversed(pair["defense_run_ids"]))
        with pytest.raises(DefenseEnergyAmplificationError, match="Trial mismatch"):
            _compute(amplification_svc, pair, defense_run_ids=reversed_defense)


class TestDeterminism:
    def test_repeated_computation_identical(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        first = _compute(amplification_svc, pair).results[0]
        second = _compute(amplification_svc, pair).results[0]

        assert first.additional_defense_energy == second.additional_defense_energy
        assert first.defense_energy_amplification == second.defense_energy_amplification
        assert first.power_amplification == second.power_amplification
        assert first.amplification_carbon_kg == second.amplification_carbon_kg
        assert first.energy_attack_only == second.energy_attack_only
        assert first.energy_attack_defense == second.energy_attack_defense

    def test_repeated_statistics_identical(self, amplification_svc, research_svc):
        pair = _pair(research_svc, trials=2)
        first = _compute(amplification_svc, pair).statistics
        second = _compute(amplification_svc, pair).statistics
        assert first.amplification_energy.mean == second.amplification_energy.mean
        assert first.amplification_energy.std_dev == second.amplification_energy.std_dev
        assert first.amplification_ratio.max == second.amplification_ratio.max


class TestValidation:
    def test_attack_mismatch(self, amplification_svc, research_svc):
        baseline_pair = _pair(research_svc, attack="ddos")
        other = _pair(research_svc, attack="port_scan")
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Attack type mismatch"
        ):
            _compute(
                amplification_svc,
                baseline_pair,
                defense_run_ids=other["defense_run_ids"],
            )

    def test_intensity_mismatch(self, amplification_svc, research_svc):
        baseline_pair = _pair(research_svc, intensity="low")
        other = _pair(research_svc, intensity="high")
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Attack intensity mismatch"
        ):
            _compute(
                amplification_svc,
                baseline_pair,
                defense_run_ids=other["defense_run_ids"],
            )

    def test_workload_value_mismatch(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        run = run_repo.get_by_id(pair["defense_run_ids"][0])
        run_repo.update(run, {"workload_value": run.workload_value + 100})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Workload value mismatch"
        ):
            _compute(amplification_svc, pair)

    def test_workload_unit_mismatch(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        run = run_repo.get_by_id(pair["defense_run_ids"][0])
        run_repo.update(run, {"workload_unit": "requests_per_second"})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Workload unit mismatch"
        ):
            _compute(amplification_svc, pair)

    def test_duration_mismatch(self, amplification_svc, research_svc):
        baseline_pair = _pair(research_svc, duration=30)
        other = _pair(research_svc, duration=60)
        with pytest.raises(DefenseEnergyAmplificationError, match="Duration mismatch"):
            _compute(
                amplification_svc,
                baseline_pair,
                defense_run_ids=other["defense_run_ids"],
            )

    def test_environment_mismatch(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        exp_repo = ExperimentRepository(db_session)
        exp_repo.update(pair["experiments"][0], {"environment_info": "lab-rack-1"})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Environment mismatch"
        ):
            _compute(amplification_svc, pair)

    def test_software_config_mismatch(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        exp_repo = ExperimentRepository(db_session)
        exp_repo.update(pair["experiments"][1], {"software_version": "0.0.0-test"})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Software/config version mismatch"
        ):
            _compute(amplification_svc, pair)

    def test_energy_provider_mismatch(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        measurement_repo = EnergyMeasurementRepository(db_session)
        measurement = measurement_repo.get_latest_by_run(pair["defense_run_ids"][0])
        measurement_repo.update(measurement, {"source": "rapl"})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Energy provider mismatch"
        ):
            _compute(amplification_svc, pair)

    def test_measurement_mode_mismatch(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        run = run_repo.get_by_id(pair["defense_run_ids"][0])
        run_repo.update(run, {"measurement_mode": "SIMULATED"})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Measurement mode mismatch"
        ):
            _compute(amplification_svc, pair)

    def test_missing_baseline_run(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Baseline run not found: 999999"
        ):
            _compute(amplification_svc, pair, baseline_run_ids=[999999])

    def test_missing_defense_run(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Defense run not found: 999999"
        ):
            _compute(amplification_svc, pair, defense_run_ids=[999999])

    def test_missing_energy_measurement(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        measurement_repo = EnergyMeasurementRepository(db_session)
        measurement = measurement_repo.get_latest_by_run(pair["defense_run_ids"][0])
        measurement_repo.delete(measurement)
        with pytest.raises(
            DefenseEnergyAmplificationError,
            match="No energy measurement found for defense run",
        ):
            _compute(amplification_svc, pair)

    def test_unknown_control(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Unknown security control"
        ):
            _compute(amplification_svc, pair, control_name="quantum_shield")

    def test_missing_baseline_ids(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Missing baseline run ids"
        ):
            _compute(amplification_svc, pair, baseline_run_ids=[])

    def test_missing_defense_ids(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Missing defense run ids"
        ):
            _compute(amplification_svc, pair, defense_run_ids=[])

    def test_zero_workload_rejected(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        for run_id in pair["baseline_run_ids"] + pair["defense_run_ids"]:
            run_repo.update(run_repo.get_by_id(run_id), {"workload_value": 0})
        with pytest.raises(DefenseEnergyAmplificationError, match="Zero workload"):
            _compute(amplification_svc, pair)

    def test_invalid_workload_rejected(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        for run_id in pair["baseline_run_ids"] + pair["defense_run_ids"]:
            run_repo.update(run_repo.get_by_id(run_id), {"workload_value": None})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Invalid workload value"
        ):
            _compute(amplification_svc, pair)

    def test_negative_energy_rejected(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        measurement_repo = EnergyMeasurementRepository(db_session)
        measurement = measurement_repo.get_latest_by_run(pair["defense_run_ids"][0])
        measurement_repo.update(measurement, {"energy_joules": -10})
        with pytest.raises(
            DefenseEnergyAmplificationError,
            match="Negative energy measurement for defense run",
        ):
            _compute(amplification_svc, pair)

    def test_invalid_duration_rejected(
        self, amplification_svc, research_svc, db_session
    ):
        pair = _pair(research_svc)
        run_repo = ExperimentRunRepository(db_session)
        for run_id in pair["baseline_run_ids"] + pair["defense_run_ids"]:
            run_repo.update(run_repo.get_by_id(run_id), {"duration_seconds": 0})
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Invalid duration for baseline run"
        ):
            _compute(amplification_svc, pair)

    def test_identical_configurations_rejected(self, amplification_svc, research_svc):
        pair = _pair(research_svc, defense_controls=[])
        with pytest.raises(
            DefenseEnergyAmplificationError,
            match="Identical baseline and defense configurations",
        ):
            _compute(amplification_svc, pair)

    def test_same_run_rejected(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        same = pair["baseline_run_ids"][0]
        with pytest.raises(
            DefenseEnergyAmplificationError,
            match="Identical baseline and defense runs",
        ):
            _compute(
                amplification_svc,
                pair,
                baseline_run_ids=[same],
                defense_run_ids=[same],
            )

    def test_experiment_not_found(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        with pytest.raises(
            DefenseEnergyAmplificationError, match="Experiment not found"
        ):
            _compute(amplification_svc, pair, experiment_id=999999)

    def test_nothing_persisted_on_validation_failure(
        self, amplification_svc, research_svc
    ):
        baseline_pair = _pair(research_svc)
        other = _pair(research_svc, attack="brute_force")
        before = amplification_svc.amplification_repo.count()

        with pytest.raises(DefenseEnergyAmplificationError):
            _compute(
                amplification_svc,
                baseline_pair,
                defense_run_ids=other["defense_run_ids"],
            )

        assert amplification_svc.amplification_repo.count() == before


class TestListing:
    def test_list_and_filter(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        _compute(amplification_svc, pair)

        all_items = amplification_svc.list_amplification()
        assert all_items.total >= 1

        filtered = amplification_svc.list_amplification(
            attack_type="ddos", control_name="firewall"
        )
        assert filtered.total >= 1
        assert all(item.control_name == "firewall" for item in filtered.items)

        empty = amplification_svc.list_amplification(
            attack_type="malware", control_name="siem"
        )
        assert empty.total == 0

    def test_get_missing_returns_none(self, amplification_svc):
        assert amplification_svc.get_amplification(999999) is None

    def test_persistence_roundtrip(self, amplification_svc, research_svc):
        pair = _pair(research_svc)
        created = _compute(amplification_svc, pair).results[0]

        fetched = amplification_svc.get_amplification(created.id)
        assert fetched is not None
        assert fetched.additional_defense_energy == created.additional_defense_energy
        assert fetched.defense_energy_amplification == created.defense_energy_amplification
        assert fetched.baseline_run_id == created.baseline_run_id
        assert fetched.statistics == created.statistics
