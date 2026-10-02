import json
import pytest
from app.main import app
from fastapi.testclient import TestClient
from app.database import init_db


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def _create_and_execute(client, attack_type, intensity, controls):
    create = client.post("/api/v1/research/experiments", json={
        "name": f"{attack_type}_{intensity}_{controls or 'base'}",
        "experiment_type": "MARGINAL_ENERGY",
        "attack_type": attack_type,
        "attack_intensity": intensity,
        "security_controls": controls,
        "duration_seconds": 30,
        "number_of_trials": 1,
    })
    uuid = create.json()["experiment_uuid"]
    client.post(f"/api/v1/research/experiments/{uuid}/execute")
    runs = client.get(f"/api/v1/research/experiments/{uuid}/runs")
    return create.json(), runs.json()["items"]


class TestMarginalEnergyAPI:
    def test_compute_marginal_energy(self, client):
        _, base_runs = _create_and_execute(client, "ddos", "low", [])
        _, sec_runs = _create_and_execute(client, "ddos", "low", ["firewall"])

        response = client.post("/api/v1/research/marginal-energy", json={
            "baseline_run_id": base_runs[0]["id"],
            "security_run_id": sec_runs[0]["id"],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["attack_type"] == "ddos"
        assert data["attack_intensity"] == "low"
        assert data["formula_version"] == "marginal_energy_v1"
        assert data["measurement_mode"] == "ESTIMATED"

    def test_compute_marginal_energy_with_carbon(self, client):
        _, base_runs = _create_and_execute(client, "ddos", "low", [])
        _, sec_runs = _create_and_execute(client, "ddos", "low", ["ids"])

        response = client.post("/api/v1/research/marginal-energy", json={
            "baseline_run_id": base_runs[0]["id"],
            "security_run_id": sec_runs[0]["id"],
            "carbon_intensity": 400.0,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["carbon_intensity"] == 400.0
        assert data["carbon_basis"] == "calculated_from_estimated_energy"
        cpw = data["marginal_carbon_per_workload"]
        assert cpw["status"] == "available"
        assert cpw["unit"] == f"kg/{data['workload_unit']}"
        assert cpw["value_kg"] == pytest.approx(
            data["marginal_carbon_kg"] / data["workload_value"]
        )

    def test_compute_without_carbon_reports_basis_not_measured(self, client):
        _, base_runs = _create_and_execute(client, "ddos", "low", [])
        _, sec_runs = _create_and_execute(client, "ddos", "low", ["firewall"])
        data = client.post("/api/v1/research/marginal-energy", json={
            "baseline_run_id": base_runs[0]["id"],
            "security_run_id": sec_runs[0]["id"],
        }).json()
        assert data["carbon_basis"] == "calculated_from_estimated_energy"

    def test_compute_mismatched_attack(self, client):
        _, base_runs = _create_and_execute(client, "ddos", "low", [])
        _, sec_runs = _create_and_execute(client, "brute_force", "low", ["firewall"])

        response = client.post("/api/v1/research/marginal-energy", json={
            "baseline_run_id": base_runs[0]["id"],
            "security_run_id": sec_runs[0]["id"],
        })
        assert response.status_code == 400

    def test_compute_mismatched_intensity(self, client):
        _, base_runs = _create_and_execute(client, "ddos", "low", [])
        _, sec_runs = _create_and_execute(client, "ddos", "high", ["firewall"])

        response = client.post("/api/v1/research/marginal-energy", json={
            "baseline_run_id": base_runs[0]["id"],
            "security_run_id": sec_runs[0]["id"],
        })
        assert response.status_code == 400

    def test_list_marginal_energy(self, client):
        _, base_runs = _create_and_execute(client, "port_scan", "low", [])
        _, sec_runs = _create_and_execute(client, "port_scan", "low", ["firewall"])

        client.post("/api/v1/research/marginal-energy", json={
            "baseline_run_id": base_runs[0]["id"],
            "security_run_id": sec_runs[0]["id"],
        })

        response = client.get("/api/v1/research/marginal-energy")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    def test_get_marginal_energy_by_id(self, client):
        _, base_runs = _create_and_execute(client, "sql_injection", "low", [])
        _, sec_runs = _create_and_execute(client, "sql_injection", "low", ["waf"])

        create = client.post("/api/v1/research/marginal-energy", json={
            "baseline_run_id": base_runs[0]["id"],
            "security_run_id": sec_runs[0]["id"],
        })
        attr_id = create.json()["id"]

        response = client.get(f"/api/v1/research/marginal-energy/{attr_id}")
        assert response.status_code == 200
        assert response.json()["id"] == attr_id

    def test_get_marginal_energy_not_found(self, client):
        response = client.get("/api/v1/research/marginal-energy/999999")
        assert response.status_code == 404

    def test_paired_statistics(self, client):
        _, base_runs = _create_and_execute(client, "ddos", "low", [])
        _, sec_runs = _create_and_execute(client, "ddos", "low", ["firewall"])

        response = client.post("/api/v1/research/marginal-energy/statistics", json={
            "baseline_run_ids": [base_runs[0]["id"]],
            "security_run_ids": [sec_runs[0]["id"]],
        })
        assert response.status_code == 200
        data = response.json()
        assert "marginal_energy" in data
        assert "marginal_power" in data
        assert "marginal_carbon" in data
        assert data["marginal_energy"]["count"] == 1

    def test_paired_statistics_mismatch(self, client):
        _, base_runs = _create_and_execute(client, "ddos", "low", [])
        _, sec_runs = _create_and_execute(client, "brute_force", "low", ["firewall"])

        response = client.post("/api/v1/research/marginal-energy/statistics", json={
            "baseline_run_ids": [base_runs[0]["id"]],
            "security_run_ids": [sec_runs[0]["id"]],
        })
        assert response.status_code == 400

    def test_experiment_marginal_energy_endpoint(self, client):
        exp_base = client.post("/api/v1/research/experiments", json={
            "name": "API Exp Base",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "security_controls": [],
            "duration_seconds": 30,
            "number_of_trials": 2,
        }).json()
        client.post(f"/api/v1/research/experiments/{exp_base['experiment_uuid']}/execute")

        exp_sec = client.post("/api/v1/research/experiments", json={
            "name": "API Exp Sec",
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": "ddos",
            "attack_intensity": "low",
            "security_controls": ["firewall"],
            "duration_seconds": 30,
            "number_of_trials": 2,
        }).json()
        client.post(f"/api/v1/research/experiments/{exp_sec['experiment_uuid']}/execute")

        base_runs = client.get(f"/api/v1/research/experiments/{exp_base['experiment_uuid']}/runs").json()["items"]
        sec_runs = client.get(f"/api/v1/research/experiments/{exp_sec['experiment_uuid']}/runs").json()["items"]

        response = client.post("/api/v1/research/marginal-energy/statistics", json={
            "baseline_run_ids": [r["id"] for r in base_runs],
            "security_run_ids": [r["id"] for r in sec_runs],
        })
        assert response.status_code == 200
        assert response.json()["marginal_energy"]["count"] == 2
