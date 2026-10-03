"""Phase 13 targeted tests: end-to-end CarbonGuard pipeline orchestration."""
import json

import pytest
from unittest.mock import patch

from app.services.orchestration_service import CarbonGuardOrchestrationService
from app.services.research_service import ResearchExperimentService
from app.models.research import (
    EnergyMeasurement,
    ExperimentRun,
    ResearchMetric,
    SecurityEffectiveness,
)


VALID_EXPERIMENT = {
    "experiment_type": "MARGINAL_ENERGY",
    "attack_type": "ddos",
    "attack_intensity": "medium",
    "security_controls": ["firewall"],
    "measurement_provider": "estimated",
    "number_of_trials": 1,
    "duration_seconds": 60,
}


@pytest.fixture
def service(db):
    return CarbonGuardOrchestrationService(db)


class TestStageConnections:
    def test_attack_feeds_threat(self, service):
        result = service.run("ddos")
        assert result["attack"]["attack_type"] == "ddos"
        assert result["threat"]["threat_type"] == "ddos"
        assert result["threat"]["id"] is not None
        assert result["event"]["id"] is not None
        assert result["threat"]["event_id"] == result["event"]["id"]

    def test_threat_severity_drives_defense_tier(self, service):
        result = service.run("port_scan")
        assert result["defense"]["tier"] == result["threat"]["severity"]
        assert result["defense"]["basis"] == "rule_based"
        assert result["defense"]["activated"] is True
        assert 1 <= len(result["security_controls"]) <= len(result["defense"]["available"])

    def test_defense_controls_feed_energy(self, service):
        result = service.run("ddos")
        assert result["energy"]["status"] == "completed"
        assert (
            result["energy"]["security_controls_active"]
            == len(result["security_controls"])
        )

    def test_energy_feeds_carbon(self, service):
        result = service.run("ddos")
        assert result["carbon"]["status"] == "completed"
        assert result["carbon"]["energy_kwh"] == result["energy"]["energy_kwh"]
        expected_gross = round(
            result["energy"]["energy_kwh"] * result["carbon"]["carbon_intensity"] / 1000,
            6,
        )
        assert result["carbon"]["gross_co2_kg"] == expected_gross

    def test_carbon_preserves_units_and_formula(self, service):
        result = service.run("ddos")
        carbon = result["carbon"]
        assert "kWh" in carbon["calculation_breakdown"]
        assert "gCO2/kWh" in carbon["calculation_breakdown"]
        assert carbon["renewable_pct"] is not None


class TestCompleteResponse:
    REQUIRED_KEYS = {
        "status", "event", "attack", "threat", "risk", "defense",
        "security_controls", "energy", "carbon", "comparison",
        "research", "analytics", "provenance", "stages", "warnings",
    }

    def test_all_sections_present(self, service):
        result = service.run("ddos")
        assert self.REQUIRED_KEYS.issubset(result.keys())
        assert result["status"] in ("completed", "partial")

    def test_stage_order_follows_pipeline(self, service):
        result = service.run("ddos")
        steps = [s["step"] for s in result["stages"]]
        assert steps[0] == "Attack Simulation"
        assert "Threat Detection" in steps
        assert "Risk Score" in steps
        assert "Detection Energy Estimate" in steps
        assert "Detection Carbon Estimate" in steps
        assert steps[-1] == "Analytics"
        assert "Defense Selection" in steps
        assert "Defense Energy Measurement" in steps
        assert "Defense Carbon Calculation" in steps
        assert "Research Observation" in steps
        assert (
            steps.index("Defense Selection")
            < steps.index("Defense Energy Measurement")
            < steps.index("Defense Carbon Calculation")
            < steps.index("Research Observation")
            < steps.index("Analytics")
        )
        assert steps.index("Detection Carbon Estimate") < steps.index(
            "Defense Selection"
        )
        assert len(steps) == len(set(steps)), "stage names must be unique"

    def test_risk_section_matches_engine_output(self, service):
        result = service.run("ddos")
        assert set(result["risk"].keys()) == {"risk_score", "severity", "confidence", "factors"}
        assert 0 <= result["risk"]["risk_score"] <= 100


class TestProvenanceAndLabeling:
    def test_marked_synthetic(self, service):
        result = service.run("ddos")
        assert result["provenance"]["data_classification"] == "SYNTHETIC"
        assert result["provenance"]["simulated_attack"] is True
        assert result["attack"]["synthetic"] is True

    def test_estimated_measurement_labelled(self, service):
        result = service.run("ddos")
        assert result["energy"]["measurement_mode"] == "ESTIMATED"
        assert result["energy"]["estimated"] is True
        assert result["provenance"]["measurement_mode"] == "ESTIMATED"

    def test_carbon_basis_labelled(self, service):
        result = service.run("ddos")
        assert result["carbon"]["carbon_basis"] == "calculated_from_estimated_energy"
        assert result["provenance"]["carbon_basis"] == "calculated_from_estimated_energy"

    def test_control_selection_declared_rule_based(self, service):
        result = service.run("ddos")
        assert result["provenance"]["control_selection"] == "rule_based"


class TestComparison:
    def test_comparison_available_with_both_sides(self, service):
        result = service.run("ddos")
        comparison = result["comparison"]
        assert comparison["status"] == "available"
        assert comparison["baseline_energy_kwh"] is not None
        assert comparison["defense_energy_kwh"] == result["energy"]["energy_kwh"]
        assert comparison["energy_difference_kwh"] is not None
        assert comparison["carbon_difference_kg"] is not None
        assert comparison["direction"] in (
            "additional_energy", "energy_saved", "neutral"
        )

    def test_controls_add_energy_overhead(self, service):
        result = service.run("ddos")
        assert result["comparison"]["energy_difference_kwh"] >= 0
        assert result["comparison"]["direction"] != "energy_saved"

    def test_comparison_not_called_saved_when_unavailable(self, service):
        with patch(
            "app.services.orchestration_service.get_provider",
            side_effect=RuntimeError("provider down"),
        ):
            result = service.run("ddos")
        comparison = result["comparison"]
        assert comparison["status"] == "unavailable"
        assert comparison["direction"] is None
        assert comparison["reason"]


class TestResearchObservation:
    def test_not_requested_by_default(self, service):
        result = service.run("ddos")
        assert result["research"]["status"] == "not_requested"
        assert result["research"]["run_id"] is None

    def test_pipeline_run_recorded_on_experiment(self, db, service):
        experiment = ResearchExperimentService(db).create_experiment(VALID_EXPERIMENT)

        result = service.run(
            "ddos",
            intensity="medium",
            record_research=True,
            experiment_uuid=experiment.experiment_uuid,
        )

        research = result["research"]
        assert research["status"] == "recorded"
        assert research["experiment_uuid"] == experiment.experiment_uuid
        assert research["run_id"] is not None
        assert research["trial_number"] == 1

        run = db.query(ExperimentRun).filter_by(id=research["run_id"]).one()
        assert run.attack_type == "ddos"
        assert json.loads(run.security_controls) == sorted(result["security_controls"])
        assert run.status == "completed"

        measurements = db.query(EnergyMeasurement).filter_by(run_id=run.id).all()
        assert len(measurements) == 1
        assert measurements[0].measurement_mode == "ESTIMATED"
        assert measurements[0].energy_joules == result["energy"]["energy_joules"]

        effect = db.query(SecurityEffectiveness).filter_by(run_id=run.id).one()
        assert effect.threat_severity == result["threat"]["severity"]
        assert effect.security_score == result["risk"]["risk_score"]

        metrics = db.query(ResearchMetric).filter_by(run_id=run.id).all()
        carbon_metrics = [m for m in metrics if m.metric_name == "pipeline_net_carbon_kg"]
        assert len(carbon_metrics) == 1
        assert carbon_metrics[0].metric_value == result["carbon"]["net_co2_kg"]
        assert "calculated_from_estimated_energy" in carbon_metrics[0].notes

    def test_second_run_becomes_next_trial(self, db, service):
        experiment = ResearchExperimentService(db).create_experiment(VALID_EXPERIMENT)
        service.run(
            "ddos", record_research=True, experiment_uuid=experiment.experiment_uuid
        )
        second = service.run(
            "port_scan", record_research=True, experiment_uuid=experiment.experiment_uuid
        )
        assert second["research"]["trial_number"] == 2

    def test_invalid_experiment_id_degrades_gracefully(self, service):
        result = service.run(
            "ddos", record_research=True, experiment_uuid="does-not-exist"
        )
        assert result["research"]["status"] == "failed"
        assert "Experiment not found" in result["research"]["reason"]
        assert result["status"] == "partial"
        assert any(w["stage"] == "Research Observation" for w in result["warnings"])
        assert result["event"]["id"] is not None

    def test_missing_experiment_uuid_degrades_gracefully(self, service):
        result = service.run("ddos", record_research=True)
        assert result["research"]["status"] == "failed"
        assert "experiment_uuid is required" in result["research"]["reason"]
        assert result["status"] == "partial"

    def test_persistence_failure_does_not_crash_run(self, db, service):
        experiment = ResearchExperimentService(db).create_experiment(VALID_EXPERIMENT)
        with patch.object(
            ResearchExperimentService,
            "record_pipeline_observation",
            side_effect=RuntimeError("disk full"),
        ):
            result = service.run(
                "ddos",
                record_research=True,
                experiment_uuid=experiment.experiment_uuid,
            )
        assert result["research"]["status"] == "failed"
        assert "Research persistence failed" in result["research"]["reason"]
        assert result["energy"]["status"] == "completed"
        assert result["stages"][-1]["step"] == "Analytics"


class TestFailureHandling:
    def test_unavailable_energy_degrades_carbon_and_comparison(self, service):
        with patch(
            "app.services.orchestration_service.get_provider",
            side_effect=RuntimeError("no provider"),
        ):
            result = service.run("ddos")

        assert result["status"] == "partial"
        assert result["energy"]["status"] == "unavailable"
        assert result["energy"]["reason"]
        assert result["carbon"]["status"] == "unavailable"
        assert "energy measurement is unavailable" in result["carbon"]["reason"]
        assert result["comparison"]["status"] == "unavailable"
        assert any(w["stage"] == "Energy" for w in result["warnings"])
        assert result["event"]["id"] is not None
        assert result["defense"]["selected"]

    def test_unavailable_carbon_keeps_energy(self, service):
        with patch(
            "app.services.orchestration_service.calculate_carbon",
            side_effect=RuntimeError("intensity feed down"),
        ):
            result = service.run("ddos")

        assert result["status"] == "partial"
        assert result["energy"]["status"] == "completed"
        assert result["carbon"]["status"] == "unavailable"
        assert "Carbon calculation unavailable" in result["carbon"]["reason"]
        assert result["comparison"]["status"] == "unavailable"
        assert any(w["stage"] == "Carbon" for w in result["warnings"])

    def test_persistence_failure_degrades_to_analytics_partial(self):
        service = CarbonGuardOrchestrationService(None)
        result = service.run("ddos")
        assert result["status"] == "partial"
        assert result["analytics"]["status"] == "partial"
        assert any(w["stage"] == "Persistence" for w in result["warnings"])
        assert result["defense"]["selected"]

    def test_invalid_attack_type_raises(self, service):
        from app.engines.security.attack_profiles import AttackProfileError

        with pytest.raises(AttackProfileError):
            service.run("not_a_real_attack")

    def test_invalid_intensity_raises(self, service):
        from app.engines.security.attack_profiles import AttackProfileError

        with pytest.raises(AttackProfileError):
            service.run("ddos", intensity="apocalyptic")

    def test_invalid_provider_raises(self, service):
        with pytest.raises(ValueError):
            service.run("ddos", measurement_provider="quantum")

    def test_stage_statuses_report_failures(self, service):
        with patch(
            "app.services.orchestration_service.get_provider",
            side_effect=RuntimeError("down"),
        ):
            result = service.run("ddos")
        by_step = {s["step"]: s for s in result["stages"]}
        assert by_step["Defense Energy Measurement"]["status"] == "failed"
        assert by_step["Defense Carbon Calculation"]["status"] == "failed"
        assert by_step["Attack Simulation"]["status"] == "completed"
