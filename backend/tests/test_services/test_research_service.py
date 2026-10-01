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
)
from app.services.research_service import (
    ResearchExperimentService,
    ExperimentError,
    _normalize_controls,
    CONFIG_VERSION,
)


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
def service(db_session):
    return ResearchExperimentService(db_session)


class TestNormalizeControls:
    def test_empty(self):
        assert _normalize_controls([]) == []

    def test_single(self):
        assert _normalize_controls(["firewall"]) == ["firewall"]

    def test_sorted_and_deduped(self):
        result = _normalize_controls(["ids", "firewall", "ids", "Firewall"])
        assert result == ["firewall", "ids"]

    def test_whitespace(self):
        result = _normalize_controls(["  firewall  ", " ids "])
        assert result == ["firewall", "ids"]


class TestValidateExperimentConfig:
    def test_valid_config(self, service):
        config = {
            "name": "Test Experiment",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "duration_seconds": 60,
            "number_of_trials": 1,
            "measurement_provider": "estimated",
        }
        result = service.validate_experiment_config(config)
        assert result["attack_type"] == "ddos"

    def test_invalid_experiment_type(self, service):
        config = {
            "experiment_type": "INVALID",
            "attack_type": "ddos",
            "attack_intensity": "medium",
        }
        with pytest.raises(ExperimentError, match="Invalid experiment_type"):
            service.validate_experiment_config(config)

    def test_invalid_attack_type(self, service):
        config = {
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "nonexistent",
            "attack_intensity": "medium",
        }
        with pytest.raises(ExperimentError, match="Unsupported attack type"):
            service.validate_experiment_config(config)

    def test_invalid_intensity(self, service):
        config = {
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "extreme",
        }
        with pytest.raises(ExperimentError, match="Unsupported intensity"):
            service.validate_experiment_config(config)

    def test_invalid_control(self, service):
        config = {
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "security_controls": ["nonexistent"],
        }
        with pytest.raises(ExperimentError, match="Unknown security control"):
            service.validate_experiment_config(config)

    def test_invalid_provider(self, service):
        config = {
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "measurement_provider": "quantum",
        }
        with pytest.raises(ExperimentError, match="Invalid measurement_provider"):
            service.validate_experiment_config(config)

    def test_invalid_num_trials(self, service):
        config = {
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "number_of_trials": 50,
        }
        with pytest.raises(ExperimentError, match="number_of_trials"):
            service.validate_experiment_config(config)


class TestCreateExperiment:
    def test_creates_experiment(self, service):
        config = {
            "name": "DDoS Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "duration_seconds": 30,
            "number_of_trials": 1,
        }
        experiment = service.create_experiment(config)
        assert experiment.experiment_uuid
        assert experiment.attack_type == "ddos"
        assert experiment.attack_intensity == "medium"
        assert experiment.status == "created"

    def test_experiment_with_controls(self, service):
        config = {
            "name": "DDoS with Firewall",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "security_controls": ["firewall", "ids"],
            "duration_seconds": 30,
        }
        experiment = service.create_experiment(config)
        controls = json.loads(experiment.security_controls)
        assert "firewall" in controls
        assert "ids" in controls

    def test_experiment_baseline(self, service):
        config = {
            "name": "Baseline",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "brute_force",
            "attack_intensity": "high",
            "security_controls": [],
        }
        experiment = service.create_experiment(config)
        controls = json.loads(experiment.security_controls)
        assert controls == []

    def test_config_version_preserved(self, service):
        config = {
            "name": "Version Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
        }
        experiment = service.create_experiment(config)
        assert experiment.configuration_version == CONFIG_VERSION

    def test_workload_profile_set(self, service):
        config = {
            "name": "Workload Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
        }
        experiment = service.create_experiment(config)
        assert experiment.workload_profile == "ddos_medium"

    def test_measurement_mode_preserved(self, service):
        config = {
            "name": "Mode Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "measurement_provider": "estimated",
        }
        experiment = service.create_experiment(config)
        assert experiment.measurement_mode == "ESTIMATED"


class TestExecuteExperiment:
    def test_execute_single_trial(self, service):
        config = {
            "name": "Execute Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
            "number_of_trials": 1,
        }
        experiment = service.create_experiment(config)
        result = service.execute_experiment(experiment.experiment_uuid)
        assert result.status == "completed"
        assert result.completed_at is not None

    def test_execute_multiple_trials(self, service):
        config = {
            "name": "Multi Trial",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "brute_force",
            "attack_intensity": "low",
            "duration_seconds": 30,
            "number_of_trials": 3,
        }
        experiment = service.create_experiment(config)
        result = service.execute_experiment(experiment.experiment_uuid)
        assert result.status == "completed"

        runs = service.get_experiment_runs(experiment.experiment_uuid)
        assert len(runs) == 3
        for i, run in enumerate(runs, 1):
            assert run.trial_number == i
            assert run.status == "completed"

    def test_run_has_measurements(self, service):
        config = {
            "name": "Measurement Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
            "number_of_trials": 1,
        }
        experiment = service.create_experiment(config)
        service.execute_experiment(experiment.experiment_uuid)

        runs = service.get_experiment_runs(experiment.experiment_uuid)
        measurements = service.get_run_measurements(runs[0].id)
        assert len(measurements) == 1
        assert measurements[0].energy_joules > 0
        assert measurements[0].measurement_mode == "ESTIMATED"

    def test_run_has_security_effectiveness(self, service):
        config = {
            "name": "Security Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
            "number_of_trials": 1,
        }
        experiment = service.create_experiment(config)
        service.execute_experiment(experiment.experiment_uuid)

        runs = service.get_experiment_runs(experiment.experiment_uuid)
        effectiveness = service.get_run_effectiveness(runs[0].id)
        assert effectiveness is not None
        assert effectiveness.detection_rate is not None
        assert effectiveness.threat_severity is not None

    def test_run_has_workload_metadata(self, service):
        config = {
            "name": "Workload Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "duration_seconds": 30,
            "number_of_trials": 1,
        }
        experiment = service.create_experiment(config)
        service.execute_experiment(experiment.experiment_uuid)

        runs = service.get_experiment_runs(experiment.experiment_uuid)
        assert runs[0].workload_value is not None
        assert runs[0].workload_value > 0
        assert runs[0].workload_unit == "packets_per_second"

    def test_execute_nonexistent_experiment(self, service):
        with pytest.raises(ExperimentError, match="not found"):
            service.execute_experiment("nonexistent-uuid")

    def test_experiment_with_controls_runs(self, service):
        config = {
            "name": "Controls Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "port_scan",
            "attack_intensity": "low",
            "security_controls": ["firewall"],
            "duration_seconds": 30,
            "number_of_trials": 1,
        }
        experiment = service.create_experiment(config)
        result = service.execute_experiment(experiment.experiment_uuid)
        assert result.status == "completed"

        runs = service.get_experiment_runs(experiment.experiment_uuid)
        controls = json.loads(runs[0].security_controls)
        assert "firewall" in controls
        assert runs[0].control_count == 1

    def test_baseline_experiment_runs(self, service):
        config = {
            "name": "Baseline Run",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "sql_injection",
            "attack_intensity": "low",
            "security_controls": [],
            "duration_seconds": 30,
        }
        experiment = service.create_experiment(config)
        result = service.execute_experiment(experiment.experiment_uuid)
        assert result.status == "completed"

        runs = service.get_experiment_runs(experiment.experiment_uuid)
        assert runs[0].control_count == 0


class TestExperimentRetrieval:
    def test_get_experiment(self, service):
        config = {
            "name": "Retrieval Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
        }
        experiment = service.create_experiment(config)
        retrieved = service.get_experiment(experiment.experiment_uuid)
        assert retrieved is not None
        assert retrieved.experiment_uuid == experiment.experiment_uuid

    def test_get_nonexistent_experiment(self, service):
        assert service.get_experiment("nonexistent") is None

    def test_list_experiments(self, service):
        config1 = {
            "name": "List Test 1",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
        }
        config2 = {
            "name": "List Test 2",
            "experiment_type": "INTERACTION",
            "attack_type": "brute_force",
            "attack_intensity": "medium",
        }
        service.create_experiment(config1)
        service.create_experiment(config2)

        all_exps = service.list_experiments()
        assert len(all_exps) >= 2

        marginals = service.list_experiments(experiment_type="MARGINAL_ENERGY")
        assert all(e.experiment_type == "MARGINAL_ENERGY" for e in marginals)

    def test_experiment_status(self, service):
        config = {
            "name": "Status Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "number_of_trials": 2,
        }
        experiment = service.create_experiment(config)
        status = service.get_experiment_status(experiment.experiment_uuid)
        assert status["status"] == "created"
        assert status["total_runs"] == 0


class TestExperimentSummary:
    def test_summary_after_execution(self, service):
        config = {
            "name": "Summary Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
            "number_of_trials": 2,
        }
        experiment = service.create_experiment(config)
        service.execute_experiment(experiment.experiment_uuid)

        summary = service.get_experiment_summary(experiment.experiment_uuid)
        assert len(summary["runs"]) == 2
        assert len(summary["measurements"]) == 2
        assert len(summary["security_effects"]) == 2


class TestDeterminism:
    def test_same_config_same_workload(self, service):
        config = {
            "name": "Determinism Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "duration_seconds": 60,
        }
        exp1 = service.create_experiment(config)
        exp2 = service.create_experiment(config)

        service.execute_experiment(exp1.experiment_uuid)
        service.execute_experiment(exp2.experiment_uuid)

        runs1 = service.get_experiment_runs(exp1.experiment_uuid)
        runs2 = service.get_experiment_runs(exp2.experiment_uuid)

        assert runs1[0].workload_value == runs2[0].workload_value
        assert runs1[0].workload_unit == runs2[0].workload_unit


class TestBaselineVsControlled:
    def test_baseline_and_controlled_same_attack(self, service):
        baseline_config = {
            "name": "Baseline",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "security_controls": [],
            "duration_seconds": 30,
        }
        controlled_config = {
            "name": "With Firewall",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "medium",
            "security_controls": ["firewall"],
            "duration_seconds": 30,
        }

        baseline = service.create_experiment(baseline_config)
        controlled = service.create_experiment(controlled_config)

        service.execute_experiment(baseline.experiment_uuid)
        service.execute_experiment(controlled.experiment_uuid)

        b_runs = service.get_experiment_runs(baseline.experiment_uuid)
        c_runs = service.get_experiment_runs(controlled.experiment_uuid)

        assert b_runs[0].attack_type == c_runs[0].attack_type
        assert b_runs[0].attack_intensity == c_runs[0].attack_intensity
        assert b_runs[0].workload_value == c_runs[0].workload_value
        assert b_runs[0].workload_unit == c_runs[0].workload_unit

        b_controls = json.loads(b_runs[0].security_controls)
        c_controls = json.loads(c_runs[0].security_controls)
        assert b_controls == []
        assert "firewall" in c_controls

        b_meas = service.get_run_measurements(b_runs[0].id)
        c_meas = service.get_run_measurements(c_runs[0].id)
        assert len(b_meas) == 1
        assert len(c_meas) == 1
