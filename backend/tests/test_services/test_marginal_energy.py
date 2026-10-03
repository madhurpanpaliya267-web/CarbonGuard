import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.research import (
    Experiment,
    ExperimentRun,
    EnergyMeasurement,
    SecurityEffectiveness,
    EnergyAttribution,
)
from app.services.research_service import ResearchExperimentService
from app.services.marginal_energy_service import (
    MarginalEnergyService,
    MarginalEnergyError,
    FORMULA_VERSION,
    JOULES_PER_KWH,
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
def marginal_svc(db_session):
    return MarginalEnergyService(db_session)


def _run_experiment(svc, attack_type, intensity, controls, duration=30, trials=1):
    exp = svc.create_experiment({
        "name": f"{attack_type}_{intensity}_{'_'.join(controls) or 'baseline'}",
        "experiment_type": "MARGINAL_ENERGY",
        "attack_type": attack_type,
        "attack_intensity": intensity,
        "security_controls": controls,
        "duration_seconds": duration,
        "number_of_trials": trials,
    })
    svc.execute_experiment(exp.experiment_uuid)
    runs = svc.get_experiment_runs(exp.experiment_uuid)
    return exp, runs


class TestBasicCalculation:
    def test_delta_energy(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )

        expected_delta = (
            attribution.security_energy_joules - attribution.baseline_energy_joules
        )
        assert abs(attribution.marginal_energy_joules - expected_delta) < 1e-9

    def test_delta_power(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )

        expected_delta = (
            attribution.security_power_watts - attribution.baseline_power_watts
        )
        assert abs(attribution.marginal_power_watts - expected_delta) < 1e-9

    def test_carbon_calculation(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )

        intensity = attribution.carbon_intensity
        expected_baseline = calculate_carbon(
            attribution.baseline_energy_kwh, intensity, 0
        )
        assert abs(attribution.baseline_carbon_kg - expected_baseline["gross_co2_kg"]) < 1e-6

    def test_formula_version(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )
        assert attribution.formula_version == FORMULA_VERSION

    def test_measurement_mode_preserved(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )
        assert attribution.measurement_mode == "ESTIMATED"


class TestValidation:
    def test_attack_type_mismatch(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "brute_force", "low", ["firewall"], trials=1)

        with pytest.raises(MarginalEnergyError, match="Attack type mismatch"):
            marginal_svc.compute_pair(
                experiment_id=exp_b.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=runs_b[0].id,
            )

    def test_intensity_mismatch(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "high", ["firewall"], trials=1)

        with pytest.raises(MarginalEnergyError, match="intensity mismatch"):
            marginal_svc.compute_pair(
                experiment_id=exp_b.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=runs_b[0].id,
            )

    def test_workload_unit_mismatch(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "port_scan", "low", ["firewall"], trials=1)

        with pytest.raises(MarginalEnergyError, match="not comparable"):
            marginal_svc.compute_pair(
                experiment_id=exp_b.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=runs_b[0].id,
            )

    def test_measurement_mode_mismatch(self, marginal_svc, research_svc, db_session):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        runs_b[0].measurement_mode = "MEASURED"
        db_session.commit()

        with pytest.raises(MarginalEnergyError, match="Measurement mode mismatch"):
            marginal_svc.compute_pair(
                experiment_id=exp_b.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=runs_b[0].id,
            )

    def test_duration_mismatch(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], duration=30, trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], duration=60, trials=1)

        with pytest.raises(MarginalEnergyError, match="Duration mismatch"):
            marginal_svc.compute_pair(
                experiment_id=exp_b.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=runs_b[0].id,
            )

    def test_workload_value_mismatch(self, marginal_svc, research_svc, db_session):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        runs_b[0].workload_value = runs_a[0].workload_value + 100
        db_session.commit()

        with pytest.raises(MarginalEnergyError, match="Workload value mismatch"):
            marginal_svc.compute_pair(
                experiment_id=exp_b.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=runs_b[0].id,
            )

    def test_missing_baseline_run(self, marginal_svc):
        with pytest.raises(MarginalEnergyError, match="Baseline run not found"):
            marginal_svc.compute_pair(
                experiment_id=1,
                baseline_run_id=99999,
                security_run_id=99999,
            )

    def test_missing_security_run(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        with pytest.raises(MarginalEnergyError, match="Security run not found"):
            marginal_svc.compute_pair(
                experiment_id=exp_a.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=99999,
            )


class TestMultipleTrials:
    def test_paired_statistics(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=3)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=3)

        stats = marginal_svc.compute_paired_statistics(
            baseline_run_ids=[r.id for r in runs_a],
            security_run_ids=[r.id for r in runs_b],
        )

        assert stats["marginal_energy"]["count"] == 3
        assert "mean" in stats["marginal_energy"]
        assert "median" in stats["marginal_energy"]
        assert "std_dev" in stats["marginal_energy"]
        assert "min" in stats["marginal_energy"]
        assert "max" in stats["marginal_energy"]
        assert stats["formula_version"] == FORMULA_VERSION

    def test_paired_statistics_count_mismatch(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=2)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=3)

        with pytest.raises(MarginalEnergyError, match="counts must match"):
            marginal_svc.compute_paired_statistics(
                baseline_run_ids=[r.id for r in runs_a],
                security_run_ids=[r.id for r in runs_b],
            )

    def test_paired_statistics_empty(self, marginal_svc):
        with pytest.raises(MarginalEnergyError, match="No runs"):
            marginal_svc.compute_paired_statistics([], [])

    def test_paired_statistics_workload_metadata(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "brute_force", "medium", [], trials=2)
        exp_b, runs_b = _run_experiment(research_svc, "brute_force", "medium", ["authentication"], trials=2)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )
        assert attribution.workload_unit == "login_attempts"
        assert attribution.workload_value is not None


class TestDeterminism:
    def test_same_runs_same_result(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        attr1 = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )
        attr2 = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )

        assert attr1.marginal_energy_joules == attr2.marginal_energy_joules
        assert attr1.marginal_power_watts == attr2.marginal_power_watts
        assert attr1.marginal_carbon_kg == attr2.marginal_carbon_kg


class TestComputeForExperiment:
    def test_compute_for_experiment(self, marginal_svc, research_svc):
        exp = research_svc.create_experiment({
            "name": "Multi-run",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "security_controls": ["firewall"],
            "duration_seconds": 30,
        })

        exp_baseline = research_svc.create_experiment({
            "name": "Baseline",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "security_controls": [],
            "duration_seconds": 30,
        })

        research_svc.execute_experiment(exp.experiment_uuid)
        research_svc.execute_experiment(exp_baseline.experiment_uuid)

        with pytest.raises(MarginalEnergyError, match="at least 2 runs"):
            marginal_svc.compute_for_experiment(exp.experiment_uuid)

    def test_nonexistent_experiment(self, marginal_svc):
        with pytest.raises(MarginalEnergyError, match="not found"):
            marginal_svc.compute_for_experiment("nonexistent")


class TestRetrieval:
    def test_get_attribution(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )

        retrieved = marginal_svc.get_attribution(attribution.id)
        assert retrieved is not None
        assert retrieved.id == attribution.id

    def test_list_attributions(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, "ddos", "low", ["firewall"], trials=1)

        marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )

        attributions = marginal_svc.list_attributions(attack_type="ddos")
        assert len(attributions) >= 1

    def test_get_security_effectiveness(self, marginal_svc, research_svc):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        effectiveness = marginal_svc.get_security_effectiveness(runs_a[0].id)
        assert effectiveness is not None
        assert effectiveness.threat_severity is not None


class TestAllAttackTypes:
    @pytest.mark.parametrize("attack_type,intensity,controls", [
        ("ddos", "low", ["firewall"]),
        ("brute_force", "medium", ["authentication"]),
        ("port_scan", "low", ["firewall"]),
        ("sql_injection", "low", ["waf"]),
        ("suspicious_login", "low", ["authentication"]),
        ("malware", "low", ["endpoint_security"]),
        ("phishing", "low", ["waf"]),
    ])
    def test_attack_type_attribution(self, marginal_svc, research_svc, attack_type, intensity, controls):
        exp_a, runs_a = _run_experiment(research_svc, attack_type, intensity, [], trials=1)
        exp_b, runs_b = _run_experiment(research_svc, attack_type, intensity, controls, trials=1)

        attribution = marginal_svc.compute_pair(
            experiment_id=exp_b.id,
            baseline_run_id=runs_a[0].id,
            security_run_id=runs_b[0].id,
        )

        assert attribution.attack_type == attack_type
        assert attribution.attack_intensity == intensity
        assert attribution.baseline_energy_joules > 0
        assert attribution.security_energy_joules > 0


class TestMissingMeasurement:
    def test_missing_security_measurement_rejected(
        self, marginal_svc, research_svc, db_session
    ):
        exp_a, runs_a = _run_experiment(research_svc, "ddos", "low", [], trials=1)
        exp_b, runs_b = _run_experiment(
            research_svc, "ddos", "low", ["firewall"], trials=1
        )
        db_session.query(EnergyMeasurement).filter(
            EnergyMeasurement.run_id == runs_b[0].id
        ).delete()
        db_session.commit()

        with pytest.raises(
            MarginalEnergyError, match="No energy measurement found for run"
        ):
            marginal_svc.compute_pair(
                experiment_id=exp_b.id,
                baseline_run_id=runs_a[0].id,
                security_run_id=runs_b[0].id,
            )
