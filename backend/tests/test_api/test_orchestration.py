"""Phase 13 API tests: POST /api/v1/orchestration/run."""
import pytest


class TestRunPipeline:
    def test_returns_complete_pipeline_response(self, client):
        response = client.post("/api/v1/orchestration/run", json={"attack_type": "ddos"})
        assert response.status_code == 200
        data = response.json()
        for key in (
            "status", "event", "attack", "threat", "risk", "defense",
            "security_controls", "energy", "carbon", "comparison",
            "research", "analytics", "provenance", "stages", "warnings",
        ):
            assert key in data, f"missing {key}"
        assert data["status"] in ("completed", "partial")

    def test_response_schema_types(self, client):
        data = client.post(
            "/api/v1/orchestration/run", json={"attack_type": "port_scan"}
        ).json()

        assert isinstance(data["event"]["event_uuid"], str)
        assert isinstance(data["event"]["id"], int)
        assert isinstance(data["threat"]["threat_uuid"], str)
        assert isinstance(data["risk"]["risk_score"], float)
        assert isinstance(data["risk"]["factors"], list)
        assert isinstance(data["defense"]["selected"], list)
        assert isinstance(data["security_controls"], list)
        assert isinstance(data["stages"], list)
        assert isinstance(data["warnings"], list)

        energy = data["energy"]
        assert energy["status"] == "completed"
        assert isinstance(energy["energy_kwh"], float)
        assert energy["measurement_mode"] == "ESTIMATED"

        carbon = data["carbon"]
        assert carbon["status"] == "completed"
        assert isinstance(carbon["net_co2_kg"], float)
        assert carbon["carbon_basis"] == "calculated_from_estimated_energy"

        provenance = data["provenance"]
        assert provenance["data_classification"] == "SYNTHETIC"
        assert provenance["control_selection"] == "rule_based"
        assert provenance["carbon_engine"] == "calculate_carbon"

    def test_defense_is_rule_based_not_optimal(self, client):
        data = client.post(
            "/api/v1/orchestration/run", json={"attack_type": "malware"}
        ).json()
        assert data["defense"]["basis"] == "rule_based"
        assert data["defense"]["status"] in ("selected", "none_available")
        assert "not an optimality claim" in data["defense"]["reason"]

    def test_threat_to_defense_to_energy_chain(self, client):
        data = client.post(
            "/api/v1/orchestration/run", json={"attack_type": "ddos"}
        ).json()
        assert data["defense"]["tier"] == data["threat"]["severity"]
        assert data["energy"]["security_controls_active"] == len(
            data["security_controls"]
        )
        assert data["carbon"]["energy_kwh"] == data["energy"]["energy_kwh"]

    def test_invalid_attack_type_returns_400(self, client):
        response = client.post(
            "/api/v1/orchestration/run", json={"attack_type": "teleport_bomb"}
        )
        assert response.status_code == 400
        assert "Unsupported attack type" in response.json()["detail"]

    def test_invalid_intensity_returns_400(self, client):
        response = client.post(
            "/api/v1/orchestration/run",
            json={"attack_type": "ddos", "intensity": "apocalyptic"},
        )
        assert response.status_code == 400
        assert "Unsupported intensity" in response.json()["detail"]

    def test_invalid_provider_returns_400(self, client):
        response = client.post(
            "/api/v1/orchestration/run",
            json={"attack_type": "ddos", "measurement_provider": "quantum"},
        )
        assert response.status_code == 400
        assert "Unknown energy provider" in response.json()["detail"]

    def test_invalid_duration_rejected_by_request_schema(self, client):
        response = client.post(
            "/api/v1/orchestration/run",
            json={"attack_type": "ddos", "duration_seconds": 0},
        )
        assert response.status_code == 422

    def test_unknown_experiment_id_degrades_gracefully(self, client):
        response = client.post(
            "/api/v1/orchestration/run",
            json={
                "attack_type": "ddos",
                "record_research": True,
                "experiment_uuid": "missing-uuid",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["research"]["status"] == "failed"
        assert "Experiment not found" in data["research"]["reason"]
        assert data["status"] == "partial"
        assert data["energy"]["status"] == "completed"

    def test_research_recorded_on_valid_experiment(self, client, db):
        from tests.test_services.test_orchestration_service import (
            VALID_EXPERIMENT,
        )
        from app.services.research_service import ResearchExperimentService

        experiment = ResearchExperimentService(db).create_experiment(VALID_EXPERIMENT)
        response = client.post(
            "/api/v1/orchestration/run",
            json={
                "attack_type": "ddos",
                "intensity": "medium",
                "record_research": True,
                "experiment_uuid": experiment.experiment_uuid,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["research"]["status"] == "recorded"
        assert data["research"]["trial_number"] == 1
        assert data["analytics"]["recorded"] is True
        assert "research_summary" in data["analytics"]["feeds"]

    def test_integrated_run_feeds_security_stats(self, client):
        client.post("/api/v1/orchestration/run", json={"attack_type": "ddos"})
        stats = client.get("/api/v1/security/stats").json()
        assert stats["total_events"] >= 1
        assert stats["by_type"].get("ddos", 0) >= 1
        assert stats["simulated"] is True


class TestRouteRegistration:
    def test_single_orchestration_run_route_registered(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/orchestration/run" in paths
        orchestration_paths = [p for p in paths if p.startswith("/api/v1/orchestration")]
        assert orchestration_paths == ["/api/v1/orchestration/run"]

    def test_existing_simulator_route_untouched(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/simulator/simulate" in paths
