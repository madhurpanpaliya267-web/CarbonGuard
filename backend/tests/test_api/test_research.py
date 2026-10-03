import json
import pytest
from app.main import app
from fastapi.testclient import TestClient
from app.database import get_db, init_db


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


class TestResearchAPI:
    def test_create_experiment(self, client):
        response = client.post("/api/v1/research/experiments", json={
            "name": "API Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["attack_type"] == "ddos"
        assert data["status"] == "created"
        assert data["experiment_uuid"]

    def test_create_experiment_with_controls(self, client):
        response = client.post("/api/v1/research/experiments", json={
            "name": "With Controls",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "brute_force",
            "attack_intensity": "medium",
            "security_controls": ["firewall", "ids"],
        })
        assert response.status_code == 201
        controls = json.loads(response.json()["security_controls"])
        assert "firewall" in controls

    def test_create_experiment_invalid_type(self, client):
        response = client.post("/api/v1/research/experiments", json={
            "name": "Invalid",
            "experiment_type": "INVALID",
            "attack_type": "ddos",
            "attack_intensity": "low",
        })
        assert response.status_code in (400, 422)

    def test_create_experiment_invalid_attack(self, client):
        response = client.post("/api/v1/research/experiments", json={
            "name": "Invalid",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "nonexistent",
            "attack_intensity": "low",
        })
        assert response.status_code == 400

    def test_list_experiments(self, client):
        response = client.get("/api/v1/research/experiments")
        assert response.status_code == 200
        assert "total" in response.json()
        assert "items" in response.json()

    def test_get_experiment(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "Get Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "port_scan",
            "attack_intensity": "low",
        })
        uuid = create.json()["experiment_uuid"]

        response = client.get(f"/api/v1/research/experiments/{uuid}")
        assert response.status_code == 200
        assert response.json()["experiment_uuid"] == uuid

    def test_get_experiment_not_found(self, client):
        response = client.get("/api/v1/research/experiments/nonexistent")
        assert response.status_code == 404

    def test_get_experiment_status(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "Status Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
        })
        uuid = create.json()["experiment_uuid"]

        response = client.get(f"/api/v1/research/experiments/{uuid}/status")
        assert response.status_code == 200
        assert response.json()["status"] == "created"

    def test_execute_experiment(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "Execute Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
            "number_of_trials": 1,
        })
        uuid = create.json()["experiment_uuid"]

        response = client.post(f"/api/v1/research/experiments/{uuid}/execute")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_execute_and_get_runs(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "Runs Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
            "number_of_trials": 2,
        })
        uuid = create.json()["experiment_uuid"]
        client.post(f"/api/v1/research/experiments/{uuid}/execute")

        response = client.get(f"/api/v1/research/experiments/{uuid}/runs")
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_get_summary(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "Summary API Test",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "duration_seconds": 30,
        })
        uuid = create.json()["experiment_uuid"]
        client.post(f"/api/v1/research/experiments/{uuid}/execute")

        response = client.get(f"/api/v1/research/experiments/{uuid}/summary")
        assert response.status_code == 200
        summary = response.json()
        assert len(summary["runs"]) == 1
        assert len(summary["measurements"]) == 1
        assert len(summary["security_effects"]) == 1

    def test_list_attack_types(self, client):
        response = client.get("/api/v1/research/attacks")
        assert response.status_code == 200
        attacks = response.json()["attacks"]
        assert len(attacks) == 7

    def test_list_controls(self, client):
        response = client.get("/api/v1/research/controls")
        assert response.status_code == 200
        controls = response.json()["controls"]
        assert len(controls) == 10

    def test_baseline_experiment_via_api(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "API Baseline",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "sql_injection",
            "attack_intensity": "low",
            "security_controls": [],
            "duration_seconds": 30,
        })
        uuid = create.json()["experiment_uuid"]
        execute = client.post(f"/api/v1/research/experiments/{uuid}/execute")
        assert execute.json()["status"] == "completed"

        runs = client.get(f"/api/v1/research/experiments/{uuid}/runs")
        controls = json.loads(runs.json()["items"][0]["security_controls"])
        assert controls == []

    def test_controlled_experiment_via_api(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "API Controlled",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "security_controls": ["waf"],
            "duration_seconds": 30,
        })
        uuid = create.json()["experiment_uuid"]
        execute = client.post(f"/api/v1/research/experiments/{uuid}/execute")
        assert execute.json()["status"] == "completed"

        runs = client.get(f"/api/v1/research/experiments/{uuid}/runs")
        controls = json.loads(runs.json()["items"][0]["security_controls"])
        assert "waf" in controls

    def test_execute_experiment_not_found(self, client):
        response = client.post("/api/v1/research/experiments/nonexistent/execute")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_experiment_status_not_found(self, client):
        response = client.get("/api/v1/research/experiments/nonexistent/status")
        assert response.status_code == 404

    def test_experiment_runs_not_found(self, client):
        response = client.get("/api/v1/research/experiments/nonexistent/runs")
        assert response.status_code == 404

    def test_experiment_summary_not_found(self, client):
        response = client.get("/api/v1/research/experiments/nonexistent/summary")
        assert response.status_code == 404

    def test_experiment_marginal_energy_via_api(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "API Marginal Energy",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "port_scan",
            "attack_intensity": "low",
            "security_controls": [],
            "duration_seconds": 30,
            "number_of_trials": 2,
        })
        uuid = create.json()["experiment_uuid"]
        execute = client.post(f"/api/v1/research/experiments/{uuid}/execute")
        assert execute.json()["status"] == "completed"

        response = client.post(
            f"/api/v1/research/experiments/{uuid}/marginal-energy"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        item = data["items"][0]
        assert item["marginal_energy_joules"] is not None
        assert item["measurement_mode"] == "ESTIMATED"
        assert item["baseline_run_id"] != item["security_run_id"]

    def test_experiment_marginal_energy_not_found(self, client):
        response = client.post(
            "/api/v1/research/experiments/nonexistent/marginal-energy"
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_experiment_marginal_energy_requires_two_runs(self, client):
        create = client.post("/api/v1/research/experiments", json={
            "name": "API Marginal Single Run",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "brute_force",
            "attack_intensity": "low",
            "security_controls": [],
            "duration_seconds": 30,
            "number_of_trials": 1,
        })
        uuid = create.json()["experiment_uuid"]
        execute = client.post(f"/api/v1/research/experiments/{uuid}/execute")
        assert execute.json()["status"] == "completed"

        response = client.post(
            f"/api/v1/research/experiments/{uuid}/marginal-energy"
        )
        assert response.status_code == 400
        assert "at least 2 runs" in response.json()["detail"]
