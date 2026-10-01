import pytest
from app.services.interaction_effect_service import FORMULA_VERSION


def _create_runs(client, attack, intensity, controls, duration=30, trials=1):
    create = client.post(
        "/api/v1/research/experiments",
        json={
            "name": f"{attack}_{intensity}_{'_'.join(controls) or 'baseline'}",
            "experiment_type": "INTERACTION",
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


def _quartet_ids(client, attack="ddos", intensity="low", duration=30):
    controls = ["firewall", "ids"]
    baseline = _create_runs(client, attack, intensity, [], duration)
    control_a = _create_runs(client, attack, intensity, [controls[0]], duration)
    control_b = _create_runs(client, attack, intensity, [controls[1]], duration)
    combined = _create_runs(client, attack, intensity, controls, duration)
    return {
        "control_a": controls[0],
        "control_b": controls[1],
        "baseline_run_ids": [r["id"] for r in baseline],
        "control_a_run_ids": [r["id"] for r in control_a],
        "control_b_run_ids": [r["id"] for r in control_b],
        "combined_run_ids": [r["id"] for r in combined],
    }


def _compute_body(quartet, **extra):
    body = {
        "control_a": quartet["control_a"],
        "control_b": quartet["control_b"],
        "baseline_run_ids": quartet["baseline_run_ids"],
        "control_a_run_ids": quartet["control_a_run_ids"],
        "control_b_run_ids": quartet["control_b_run_ids"],
        "combined_run_ids": quartet["combined_run_ids"],
    }
    body.update(extra)
    return body


class TestComputeEndpoint:
    def test_compute_interaction_effects(self, client):
        quartet = _quartet_ids(client)
        response = client.post(
            "/api/v1/research/interaction-effects",
            json=_compute_body(quartet),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 1
        row = data["results"][0]
        assert row["formula_version"] == FORMULA_VERSION
        assert row["control_a"] == "firewall"
        assert row["control_b"] == "ids"
        assert row["measurement_mode"] == "ESTIMATED"
        assert row["energy_provider"] == "estimated"
        assert row["interaction_effect"] == 0
        assert row["interpretation"] == "approximately additive"
        assert row["interaction_index"] == 0.0
        assert data["statistics"]["interaction_energy"]["count"] == 1
        assert data["statistics"]["formula_version"] == FORMULA_VERSION

    def test_compute_with_carbon_intensity(self, client):
        quartet = _quartet_ids(client)
        response = client.post(
            "/api/v1/research/interaction-effects",
            json=_compute_body(quartet, carbon_intensity=300),
        )
        assert response.status_code == 201
        row = response.json()["results"][0]
        assert row["carbon_intensity"] == 300

    def test_compute_exposes_security_effectiveness(self, client):
        quartet = _quartet_ids(client)
        response = client.post(
            "/api/v1/research/interaction-effects",
            json=_compute_body(quartet),
        )
        assert response.status_code == 201
        effectiveness = response.json()["results"][0]["security_effectiveness"]
        assert effectiveness["baseline"] is not None
        assert effectiveness["control_a"] is not None
        assert effectiveness["control_b"] is not None
        assert effectiveness["combined"] is not None

    def test_attack_mismatch_rejected(self, client):
        baseline = _quartet_ids(client, attack="ddos")
        other = _quartet_ids(client, attack="port_scan")
        body = _compute_body(baseline)
        body["control_a_run_ids"] = other["control_a_run_ids"]
        body["control_b_run_ids"] = other["control_b_run_ids"]
        body["combined_run_ids"] = other["combined_run_ids"]
        response = client.post("/api/v1/research/interaction-effects", json=body)
        assert response.status_code == 400
        assert "Attack type mismatch" in response.json()["detail"]

    def test_intensity_mismatch_rejected(self, client):
        baseline = _quartet_ids(client, intensity="low")
        other = _quartet_ids(client, intensity="high")
        body = _compute_body(baseline)
        body["control_a_run_ids"] = other["control_a_run_ids"]
        body["control_b_run_ids"] = other["control_b_run_ids"]
        body["combined_run_ids"] = other["combined_run_ids"]
        response = client.post("/api/v1/research/interaction-effects", json=body)
        assert response.status_code == 400
        assert "Attack intensity mismatch" in response.json()["detail"]

    def test_unknown_control_rejected(self, client):
        quartet = _quartet_ids(client)
        body = _compute_body(quartet)
        body["control_a"] = "quantum_shield"
        response = client.post("/api/v1/research/interaction-effects", json=body)
        assert response.status_code == 400
        assert "Unknown security control" in response.json()["detail"]

    def test_run_not_found_rejected(self, client):
        quartet = _quartet_ids(client)
        body = _compute_body(quartet)
        body["baseline_run_ids"] = [999999]
        response = client.post("/api/v1/research/interaction-effects", json=body)
        assert response.status_code == 400
        assert "baseline run not found: 999999" in response.json()["detail"]

    def test_experiment_not_found_rejected(self, client):
        quartet = _quartet_ids(client)
        body = _compute_body(quartet, experiment_id=999999)
        response = client.post("/api/v1/research/interaction-effects", json=body)
        assert response.status_code == 400
        assert "Experiment not found" in response.json()["detail"]

    def test_missing_run_ids_rejected_by_schema(self, client):
        response = client.post(
            "/api/v1/research/interaction-effects",
            json={
                "control_a": "firewall",
                "control_b": "ids",
                "baseline_run_ids": [],
                "control_a_run_ids": [1],
                "control_b_run_ids": [1],
                "combined_run_ids": [1],
            },
        )
        assert response.status_code == 422


class TestGetEndpoints:
    def test_list_interaction_effects(self, client):
        quartet = _quartet_ids(client)
        client.post("/api/v1/research/interaction-effects", json=_compute_body(quartet))

        response = client.get("/api/v1/research/interaction-effects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["items"][0]["formula_version"] == FORMULA_VERSION

    def test_list_with_filters(self, client):
        quartet = _quartet_ids(client)
        client.post("/api/v1/research/interaction-effects", json=_compute_body(quartet))

        response = client.get(
            "/api/v1/research/interaction-effects",
            params={
                "attack_type": "ddos",
                "control_a": "firewall",
                "control_b": "ids",
                "measurement_mode": "ESTIMATED",
            },
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1

        empty = client.get(
            "/api/v1/research/interaction-effects",
            params={"attack_type": "malware"},
        )
        assert empty.status_code == 200
        assert empty.json()["total"] == 0

    def test_get_by_id(self, client):
        quartet = _quartet_ids(client)
        created = client.post(
            "/api/v1/research/interaction-effects", json=_compute_body(quartet)
        ).json()
        interaction_id = created["results"][0]["id"]

        response = client.get(
            f"/api/v1/research/interaction-effects/{interaction_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == interaction_id
        assert data["energy_baseline"] > 0
        assert data["security_effectiveness"]["combined"] is not None
        assert data["duration_seconds"] == 30.0

    def test_get_not_found(self, client):
        response = client.get("/api/v1/research/interaction-effects/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_persisted_result_retrievable_after_create(self, client):
        quartet = _quartet_ids(client)
        created = client.post(
            "/api/v1/research/interaction-effects", json=_compute_body(quartet)
        ).json()
        created_row = created["results"][0]

        fetched = client.get(
            f"/api/v1/research/interaction-effects/{created_row['id']}"
        ).json()
        assert fetched["interaction_effect"] == created_row["interaction_effect"]
        assert fetched["interaction_index"] == created_row["interaction_index"]
        assert fetched["formula_version"] == "interaction_effect_v1"
        assert fetched["baseline_run_id"] == quartet["baseline_run_ids"][0]
