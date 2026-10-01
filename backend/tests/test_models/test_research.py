import pytest
from datetime import datetime, timezone
from app.models.research import (
    Experiment,
    ExperimentRun,
    EnergyMeasurement,
    SecurityEffectiveness,
    ResearchMetric,
    InteractionResult,
    DefenseAmplificationResult,
)
from app.repositories.research_repo import (
    ExperimentRepository,
    ExperimentRunRepository,
    EnergyMeasurementRepository,
    SecurityEffectivenessRepository,
    ResearchMetricRepository,
    InteractionResultRepository,
    DefenseAmplificationResultRepository,
)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Model creation tests
# ---------------------------------------------------------------------------

class TestExperimentModel:
    def test_create_experiment(self, db):
        exp = Experiment(
            name="DDoS MEDIUM Test",
            experiment_type="marginal_energy",
            attack_type="ddos",
            attack_intensity="MEDIUM",
            measurement_mode="ESTIMATED",
            duration_seconds=60.0,
            num_trials=3,
            status="created",
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        assert exp.id is not None
        assert exp.experiment_uuid is not None
        assert exp.name == "DDoS MEDIUM Test"
        assert exp.experiment_type == "marginal_energy"
        assert exp.attack_type == "ddos"
        assert exp.attack_intensity == "MEDIUM"
        assert exp.measurement_mode == "ESTIMATED"
        assert exp.duration_seconds == 60.0
        assert exp.num_trials == 3
        assert exp.status == "created"
        assert exp.created_at is not None

    def test_experiment_defaults(self, db):
        exp = Experiment(
            name="Minimal",
            experiment_type="marginal_energy",
            attack_type="port_scan",
            attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        assert exp.measurement_mode == "ESTIMATED"
        assert exp.duration_seconds == 60.0
        assert exp.num_trials == 1
        assert exp.status == "created"
        assert exp.experiment_uuid is not None

    def test_experiment_optional_fields(self, db):
        exp = Experiment(
            name="With Optional",
            experiment_type="interaction",
            attack_type="brute_force",
            attack_intensity="HIGH",
            workload_profile="web_server",
            security_controls='["firewall", "ids"]',
            carbon_intensity=475.0,
            renewable_pct=25.0,
            environment_info='{"os": "linux"}',
            software_version="1.0.0",
            configuration_version="v1",
            random_seed=42,
            notes="Test experiment",
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        assert exp.workload_profile == "web_server"
        assert exp.security_controls == '["firewall", "ids"]'
        assert exp.carbon_intensity == 475.0
        assert exp.random_seed == 42
        assert exp.notes == "Test experiment"


class TestExperimentRunModel:
    def test_create_run(self, db):
        exp = Experiment(
            name="Test",
            experiment_type="marginal_energy",
            attack_type="ddos",
            attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id,
            trial_number=1,
            attack_type="ddos",
            attack_intensity="LOW",
            measurement_mode="ESTIMATED",
            status="running",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        assert run.id is not None
        assert run.run_uuid is not None
        assert run.experiment_id == exp.id
        assert run.trial_number == 1
        assert run.status == "running"
        assert run.start_time is not None

    def test_run_defaults(self, db):
        exp = Experiment(
            name="Test",
            experiment_type="marginal_energy",
            attack_type="ddos",
            attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id,
            trial_number=1,
            attack_type="ddos",
            attack_intensity="LOW",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        assert run.measurement_mode == "ESTIMATED"
        assert run.status == "running"
        assert run.control_count == 0


class TestEnergyMeasurementModel:
    def test_create_measurement(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        meas = EnergyMeasurement(
            run_id=run.id,
            energy_joules=150.5,
            power_watts=2.5,
            duration_seconds=60.0,
            cpu_usage_pct=45.0,
            memory_usage_pct=30.0,
            network_usage_mbps=10.0,
            source="estimated",
            measurement_mode="ESTIMATED",
        )
        db.add(meas)
        db.commit()
        db.refresh(meas)

        assert meas.id is not None
        assert meas.run_id == run.id
        assert meas.energy_joules == 150.5
        assert meas.power_watts == 2.5
        assert meas.source == "estimated"
        assert meas.measurement_mode == "ESTIMATED"

    def test_measurement_defaults(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        meas = EnergyMeasurement(
            run_id=run.id,
            energy_joules=100.0,
            duration_seconds=30.0,
        )
        db.add(meas)
        db.commit()
        db.refresh(meas)

        assert meas.source == "estimated"
        assert meas.measurement_mode == "ESTIMATED"


class TestSecurityEffectivenessModel:
    def test_create_effectiveness(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        eff = SecurityEffectiveness(
            run_id=run.id,
            detection_rate=0.95,
            detection_latency_ms=120.5,
            false_positive_rate=0.02,
            mitigation_time_ms=500.0,
            threat_severity="HIGH",
            security_response="blocked",
            security_score=85.0,
            controls_active='["firewall", "ids"]',
        )
        db.add(eff)
        db.commit()
        db.refresh(eff)

        assert eff.id is not None
        assert eff.run_id == run.id
        assert eff.detection_rate == 0.95
        assert eff.detection_latency_ms == 120.5
        assert eff.security_score == 85.0


class TestResearchMetricModel:
    def test_create_metric(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        metric = ResearchMetric(
            run_id=run.id,
            metric_name="marginal_energy_joules",
            metric_value=30.5,
            unit="joules",
            formula_version="1.0",
            measurement_mode="ESTIMATED",
            confidence_interval_lower=25.0,
            confidence_interval_upper=36.0,
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)

        assert metric.id is not None
        assert metric.metric_name == "marginal_energy_joules"
        assert metric.metric_value == 30.5
        assert metric.unit == "joules"
        assert metric.confidence_interval_lower == 25.0
        assert metric.confidence_interval_upper == 36.0


class TestInteractionResultModel:
    def test_create_interaction(self, db):
        exp = Experiment(
            name="T", experiment_type="interaction",
            attack_type="ddos", attack_intensity="MEDIUM",
        )
        db.add(exp)
        db.commit()

        ir = InteractionResult(
            experiment_id=exp.id,
            control_a="firewall",
            control_b="ids",
            energy_baseline=100.0,
            energy_a=120.0,
            energy_b=130.0,
            energy_ab=170.0,
            interaction_effect=20.0,
            interaction_index=0.2,
            interpretation="super_additive",
            attack_type="ddos",
            attack_intensity="MEDIUM",
            measurement_mode="ESTIMATED",
        )
        db.add(ir)
        db.commit()
        db.refresh(ir)

        assert ir.id is not None
        assert ir.experiment_id == exp.id
        assert ir.control_a == "firewall"
        assert ir.control_b == "ids"
        assert ir.energy_baseline == 100.0
        assert ir.interaction_effect == 20.0
        assert ir.interpretation == "super_additive"


class TestDefenseAmplificationResultModel:
    def test_create_amplification(self, db):
        exp = Experiment(
            name="T", experiment_type="amplification",
            attack_type="ddos", attack_intensity="HIGH",
        )
        db.add(exp)
        db.commit()

        da = DefenseAmplificationResult(
            experiment_id=exp.id,
            control_name="ids",
            attack_type="ddos",
            attack_intensity="HIGH",
            attack_workload=5000.0,
            workload_unit="requests_per_second",
            energy_attack_only=200.0,
            energy_attack_defense=320.0,
            additional_defense_energy=120.0,
            defense_energy_amplification=0.024,
            measurement_mode="ESTIMATED",
        )
        db.add(da)
        db.commit()
        db.refresh(da)

        assert da.id is not None
        assert da.experiment_id == exp.id
        assert da.control_name == "ids"
        assert da.additional_defense_energy == 120.0
        assert da.defense_energy_amplification == 0.024


# ---------------------------------------------------------------------------
# Relationship tests
# ---------------------------------------------------------------------------

class TestRelationships:
    def test_experiment_has_runs(self, db):
        exp = Experiment(
            name="Multi-run", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        for trial in range(1, 4):
            run = ExperimentRun(
                experiment_id=exp.id,
                trial_number=trial,
                attack_type="ddos",
                attack_intensity="LOW",
            )
            db.add(run)
        db.commit()

        db.refresh(exp)
        assert len(exp.runs) == 3
        assert exp.runs[0].trial_number == 1
        assert exp.runs[2].trial_number == 3

    def test_run_has_measurements(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        for i in range(5):
            meas = EnergyMeasurement(
                run_id=run.id,
                energy_joules=100.0 + i,
                duration_seconds=10.0,
            )
            db.add(meas)
        db.commit()

        db.refresh(run)
        assert len(run.measurements) == 5

    def test_run_has_security_effectiveness(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        eff = SecurityEffectiveness(run_id=run.id, detection_rate=0.9)
        db.add(eff)
        db.commit()

        db.refresh(run)
        assert len(run.security_effects) == 1
        assert run.security_effects[0].detection_rate == 0.9

    def test_run_has_research_metrics(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        for name, value, unit in [
            ("marginal_energy_joules", 30.0, "joules"),
            ("marginal_power_watts", 0.5, "watts"),
            ("marginal_carbon_kg", 0.001, "kg"),
        ]:
            m = ResearchMetric(run_id=run.id, metric_name=name, metric_value=value, unit=unit)
            db.add(m)
        db.commit()

        db.refresh(run)
        assert len(run.research_metrics) == 3

    def test_experiment_has_interactions(self, db):
        exp = Experiment(
            name="T", experiment_type="interaction",
            attack_type="ddos", attack_intensity="MEDIUM",
        )
        db.add(exp)
        db.commit()

        for a, b in [("firewall", "ids"), ("firewall", "waf"), ("ids", "siem")]:
            ir = InteractionResult(
                experiment_id=exp.id,
                control_a=a, control_b=b,
                energy_baseline=100, energy_a=120, energy_b=130, energy_ab=170,
                interaction_effect=20, interpretation="super_additive",
            )
            db.add(ir)
        db.commit()

        db.refresh(exp)
        assert len(exp.interactions) == 3

    def test_experiment_has_amplification_results(self, db):
        exp = Experiment(
            name="T", experiment_type="amplification",
            attack_type="ddos", attack_intensity="HIGH",
        )
        db.add(exp)
        db.commit()

        for ctrl in ["firewall", "ids", "waf"]:
            da = DefenseAmplificationResult(
                experiment_id=exp.id,
                control_name=ctrl, attack_type="ddos", attack_intensity="HIGH",
                attack_workload=1000, workload_unit="requests_per_second",
                energy_attack_only=100, energy_attack_defense=150,
                additional_defense_energy=50, defense_energy_amplification=0.05,
            )
            db.add(da)
        db.commit()

        db.refresh(exp)
        assert len(exp.amplification_results) == 3

    def test_cascade_delete_experiment_to_runs(self, db):
        exp = Experiment(
            name="Delete me", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        exp_id = exp.id
        db.delete(exp)
        db.commit()

        from sqlalchemy import select
        remaining = db.execute(select(ExperimentRun).where(ExperimentRun.experiment_id == exp_id)).scalars().all()
        assert len(remaining) == 0

    def test_cascade_delete_run_to_measurements(self, db):
        exp = Experiment(
            name="T", experiment_type="marginal_energy",
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(exp)
        db.commit()

        run = ExperimentRun(
            experiment_id=exp.id, trial_number=1,
            attack_type="ddos", attack_intensity="LOW",
        )
        db.add(run)
        db.commit()

        meas = EnergyMeasurement(run_id=run.id, energy_joules=100, duration_seconds=10)
        db.add(meas)
        db.commit()

        run_id = run.id
        db.delete(run)
        db.commit()

        from sqlalchemy import select
        remaining = db.execute(select(EnergyMeasurement).where(EnergyMeasurement.run_id == run_id)).scalars().all()
        assert len(remaining) == 0


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------

class TestExperimentRepository:
    def test_create_and_get(self, db):
        repo = ExperimentRepository(db)
        exp = repo.create({
            "name": "Repo Test",
            "experiment_type": "marginal_energy",
            "attack_type": "ddos",
            "attack_intensity": "LOW",
        })
        assert exp.id is not None

        found = repo.get_by_uuid(exp.experiment_uuid)
        assert found is not None
        assert found.name == "Repo Test"

    def test_filter_by_type(self, db):
        repo = ExperimentRepository(db)
        repo.create({"name": "ME1", "experiment_type": "marginal_energy", "attack_type": "ddos", "attack_intensity": "LOW"})
        repo.create({"name": "INT1", "experiment_type": "interaction", "attack_type": "ddos", "attack_intensity": "LOW"})

        results = repo.get_by_type("marginal_energy")
        assert len(results) == 1
        assert results[0].name == "ME1"

    def test_filter_experiments(self, db):
        repo = ExperimentRepository(db)
        repo.create({"name": "A", "experiment_type": "marginal_energy", "attack_type": "ddos", "attack_intensity": "LOW", "measurement_mode": "ESTIMATED"})
        repo.create({"name": "B", "experiment_type": "marginal_energy", "attack_type": "brute_force", "attack_intensity": "HIGH", "measurement_mode": "SIMULATED"})

        results = repo.filter_experiments(attack_type="ddos")
        assert len(results) == 1

        results = repo.filter_experiments(measurement_mode="SIMULATED")
        assert len(results) == 1

        results = repo.filter_experiments(experiment_type="marginal_energy")
        assert len(results) == 2


class TestExperimentRunRepository:
    def test_get_by_experiment(self, db):
        exp_repo = ExperimentRepository(db)
        exp = exp_repo.create({"name": "T", "experiment_type": "marginal_energy", "attack_type": "ddos", "attack_intensity": "LOW"})

        run_repo = ExperimentRunRepository(db)
        for t in range(1, 4):
            run_repo.create({
                "experiment_id": exp.id,
                "trial_number": t,
                "attack_type": "ddos",
                "attack_intensity": "LOW",
            })

        runs = run_repo.get_by_experiment(exp.id)
        assert len(runs) == 3
        assert runs[0].trial_number == 1

    def test_get_completed_runs(self, db):
        exp_repo = ExperimentRepository(db)
        exp = exp_repo.create({"name": "T", "experiment_type": "marginal_energy", "attack_type": "ddos", "attack_intensity": "LOW"})

        run_repo = ExperimentRunRepository(db)
        run_repo.create({"experiment_id": exp.id, "trial_number": 1, "attack_type": "ddos", "attack_intensity": "LOW", "status": "completed"})
        run_repo.create({"experiment_id": exp.id, "trial_number": 2, "attack_type": "ddos", "attack_intensity": "LOW", "status": "running"})

        completed = run_repo.get_completed_runs(exp.id)
        assert len(completed) == 1


class TestEnergyMeasurementRepository:
    def test_get_by_run(self, db):
        exp_repo = ExperimentRepository(db)
        exp = exp_repo.create({"name": "T", "experiment_type": "marginal_energy", "attack_type": "ddos", "attack_intensity": "LOW"})

        run_repo = ExperimentRunRepository(db)
        run = run_repo.create({"experiment_id": exp.id, "trial_number": 1, "attack_type": "ddos", "attack_intensity": "LOW"})

        meas_repo = EnergyMeasurementRepository(db)
        for i in range(3):
            meas_repo.create({"run_id": run.id, "energy_joules": 100.0 + i, "duration_seconds": 10.0})

        measurements = meas_repo.get_by_run(run.id)
        assert len(measurements) == 3


class TestInteractionResultRepository:
    def test_get_by_controls(self, db):
        exp_repo = ExperimentRepository(db)
        exp = exp_repo.create({"name": "T", "experiment_type": "interaction", "attack_type": "ddos", "attack_intensity": "MEDIUM"})

        ir_repo = InteractionResultRepository(db)
        ir_repo.create({
            "experiment_id": exp.id,
            "control_a": "firewall", "control_b": "ids",
            "energy_baseline": 100, "energy_a": 120, "energy_b": 130, "energy_ab": 170,
            "interaction_effect": 20, "attack_type": "ddos",
        })
        ir_repo.create({
            "experiment_id": exp.id,
            "control_a": "firewall", "control_b": "waf",
            "energy_baseline": 100, "energy_a": 120, "energy_b": 125, "energy_ab": 155,
            "interaction_effect": 10, "attack_type": "ddos",
        })

        results = ir_repo.get_by_controls("firewall", "ids")
        assert len(results) == 1

        results = ir_repo.get_by_controls("firewall", "ids", attack_type="ddos")
        assert len(results) == 1


class TestDefenseAmplificationResultRepository:
    def test_get_by_attack_type(self, db):
        exp_repo = ExperimentRepository(db)
        exp = exp_repo.create({"name": "T", "experiment_type": "amplification", "attack_type": "ddos", "attack_intensity": "HIGH"})

        da_repo = DefenseAmplificationResultRepository(db)
        da_repo.create({
            "experiment_id": exp.id, "control_name": "ids",
            "attack_type": "ddos", "attack_intensity": "HIGH",
            "attack_workload": 1000, "workload_unit": "requests_per_second",
            "energy_attack_only": 100, "energy_attack_defense": 150,
            "additional_defense_energy": 50, "defense_energy_amplification": 0.05,
        })

        results = da_repo.get_by_attack_type("ddos")
        assert len(results) == 1
