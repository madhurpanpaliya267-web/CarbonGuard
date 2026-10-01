import pytest
from app.services.defense_energy_amplification_service import FORMULA_VERSION


def _create_runs(client, attack, intensity, controls, duration=30, trials=1):
    create = client.post(
        "/api/v1/research/experiments",
        json={
            "name": f"{attack}_{intensity}_{'_'.join(controls) or 'baseline'}",
            "experiment_type": "DEFENSE_AMPLIFICATION",
            "attack_type": attack,
            "attack_intensity": intensity,
            "security_controls": controls,
            "duration_seconds": duration,
            "number_of_trials": trials,
        },
    )
    assert create.status_code == 201
    uuid = create.json()["experiment_uuid"]
    execute = client.post(f"/api/v1/research/experiments/{uuid}/execute")
    assert execute.status_code == 200
    runs = client.get(f"/api/v1/research/experiments/{uuid}/runs").json()["items"]
    return runs


def _pair_ids(
    client, attack="ddos", intensity="low", duration=30, control="firewall"
):
    baseline = _create_runs(client, attack, intensity, [], duration)
    defense = _create_runs(client, attack, intensity, [control], duration)
    return {
        "control_name": control,
        "baseline_run_ids": [r["id"] for r in baseline],
        "defense_run_ids": [r["id"] for r in defense],
    }


def _compute_body(pair, **extra):
    body = {
        "control_name": pair["control_name"],
        "baseline_run_ids": pair["baseline_run_ids"],
        "defense_run_ids": pair["defense_run_ids"],
    }
    body.update(extra)
    return body


class TestComputeEndpoint:
    def test_compute_amplification(self, client):
        pair = _pair_ids(client)
        response = client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 1
        row = data["results"][0]
        assert row["formula_version"] == FORMULA_VERSION
        assert row["control_name"] == "firewall"
        assert row["measurement_mode"] == "ESTIMATED"
        assert row["energy_provider"] == "estimated"
        assert row["additional_defense_energy"] > 0
        assert row["defense_energy_amplification"] > 0
        assert row["baseline_run_id"] == pair["baseline_run_ids"][0]
        assert row["defense_run_id"] == pair["defense_run_ids"][0]
        assert data["statistics"]["amplification_energy"]["count"] == 1
        assert data["statistics"]["formula_version"] == FORMULA_VERSION

    def test_dea_equals_ade_over_workload(self, client):
        pair = _pair_ids(client)
        row = client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        ).json()["results"][0]
        expected = row["additional_defense_energy"] / row["attack_workload"]
        assert abs(row["defense_energy_amplification"] - expected) < 1e-9

    def test_compute_with_carbon_intensity(self, client):
        pair = _pair_ids(client)
        row = client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair, carbon_intensity=300),
        ).json()["results"][0]
        assert row["carbon_intensity"] == 300

    def test_repeat_compute_deterministic(self, client):
        pair = _pair_ids(client)
        first = client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        ).json()["results"][0]
        second = client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        ).json()["results"][0]
        assert (
            first["additional_defense_energy"] == second["additional_defense_energy"]
        )
        assert (
            first["defense_energy_amplification"]
            == second["defense_energy_amplification"]
        )
        assert first["energy_attack_only"] == second["energy_attack_only"]
        assert first["energy_attack_defense"] == second["energy_attack_defense"]

    def test_attack_mismatch_rejected(self, client):
        baseline = _pair_ids(client, attack="ddos")
        other = _pair_ids(client, attack="port_scan")
        body = _compute_body(baseline, defense_run_ids=other["defense_run_ids"])
        response = client.post(
            "/api/v1/research/defense-energy-amplification", json=body
        )
        assert response.status_code == 400
        assert "Attack type mismatch" in response.json()["detail"]

    def test_intensity_mismatch_rejected(self, client):
        baseline = _pair_ids(client, intensity="low")
        other = _pair_ids(client, intensity="high")
        body = _compute_body(baseline, defense_run_ids=other["defense_run_ids"])
        response = client.post(
            "/api/v1/research/defense-energy-amplification", json=body
        )
        assert response.status_code == 400
        assert "Attack intensity mismatch" in response.json()["detail"]

    def test_unknown_control_rejected(self, client):
        pair = _pair_ids(client)
        body = _compute_body(pair, control_name="quantum_shield")
        response = client.post(
            "/api/v1/research/defense-energy-amplification", json=body
        )
        assert response.status_code == 400
        assert "Unknown security control" in response.json()["detail"]

    def test_missing_run_rejected(self, client):
        pair = _pair_ids(client)
        body = _compute_body(pair, baseline_run_ids=[999999])
        response = client.post(
            "/api/v1/research/defense-energy-amplification", json=body
        )
        assert response.status_code == 400
        assert "Baseline run not found: 999999" in response.json()["detail"]

    def test_identical_configurations_rejected(self, client):
        baseline = _create_runs(client, "ddos", "low", [])
        defense = _create_runs(client, "ddos", "low", [])
        response = client.post(
            "/api/v1/research/defense-energy-amplification",
            json={
                "control_name": "firewall",
                "baseline_run_ids": [baseline[0]["id"]],
                "defense_run_ids": [defense[0]["id"]],
            },
        )
        assert response.status_code == 400
        assert "Identical baseline and defense" in response.json()["detail"]

    def test_missing_run_ids_rejected_by_schema(self, client):
        response = client.post(
            "/api/v1/research/defense-energy-amplification",
            json={
                "control_name": "firewall",
                "baseline_run_ids": [],
                "defense_run_ids": [],
            },
        )
        assert response.status_code == 422


class TestGetEndpoints:
    def test_list_amplification(self, client):
        pair = _pair_ids(client)
        client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        )

        response = client.get("/api/v1/research/defense-energy-amplification")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["items"][0]["formula_version"] == FORMULA_VERSION

    def test_list_with_filters(self, client):
        pair = _pair_ids(client)
        client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        )

        response = client.get(
            "/api/v1/research/defense-energy-amplification",
            params={
                "attack_type": "ddos",
                "attack_intensity": "low",
                "measurement_mode": "ESTIMATED",
                "control_name": "firewall",
            },
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1

        empty = client.get(
            "/api/v1/research/defense-energy-amplification",
            params={"attack_type": "malware", "control_name": "siem"},
        )
        assert empty.status_code == 200
        assert empty.json()["total"] == 0

    def test_get_by_id(self, client):
        pair = _pair_ids(client)
        created = client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        ).json()
        amplification_id = created["results"][0]["id"]

        response = client.get(
            f"/api/v1/research/defense-energy-amplification/{amplification_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == amplification_id
        assert data["additional_defense_energy"] == (
            created["results"][0]["additional_defense_energy"]
        )
        assert data["statistics"] is not None
        assert data["duration_seconds"] == 30.0

    def test_get_not_found(self, client):
        response = client.get("/api/v1/research/defense-energy-amplification/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_persisted_result_retrievable_after_create(self, client):
        pair = _pair_ids(client)
        created_row = client.post(
            "/api/v1/research/defense-energy-amplification",
            json=_compute_body(pair),
        ).json()["results"][0]

        fetched = client.get(
            f"/api/v1/research/defense-energy-amplification/{created_row['id']}"
        ).json()
        assert fetched["defense_energy_amplification"] == (
            created_row["defense_energy_amplification"]
        )
        assert fetched["formula_version"] == "defense_energy_amplification_v1"
        assert fetched["baseline_run_id"] == pair["baseline_run_ids"][0]
        assert fetched["defense_run_id"] == pair["defense_run_ids"][0]
