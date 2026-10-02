import pytest


def _create_and_execute(client, name, controls, attack_type="ddos", intensity="low"):
    create = client.post(
        "/api/v1/research/experiments",
        json={
            "name": name,
            "experiment_type": "MARGINAL_ENERGY",
            "attack_type": attack_type,
            "attack_intensity": intensity,
            "security_controls": controls,
            "duration_seconds": 30,
            "number_of_trials": 1,
        },
    )
    assert create.status_code == 201
    experiment = create.json()
    execute = client.post(
        f"/api/v1/research/experiments/{experiment['experiment_uuid']}/execute"
    )
    assert execute.status_code == 200
    runs = client.get(
        f"/api/v1/research/experiments/{experiment['experiment_uuid']}/runs"
    ).json()["items"]
    return experiment, runs


def _compute_marginal(client, baseline_runs, security_runs, **extra):
    body = {
        "baseline_run_id": baseline_runs[0]["id"],
        "security_run_id": security_runs[0]["id"],
    }
    body.update(extra)
    response = client.post("/api/v1/research/marginal-energy", json=body)
    assert response.status_code == 201
    return response.json()


class TestResearchSummary:
    def test_empty_research_store_reports_zero_and_no_observations(self, client):
        response = client.get("/api/v1/research/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_experiments"] == 0
        assert data["total_trials"] == 0
        assert data["attack_types"] == []
        assert data["security_controls"] == []
        assert data["measurement_modes"] == []
        assert data["estimated_trials"] == 0
        assert data["measured_trials"] == 0
        assert data["marginal_energy_observations"] == 0
        assert data["interaction_observations"] == 0
        assert data["amplification_observations"] == 0
        assert data["carbon_observations"] == 0

    def test_summary_counts_recorded_experiments(self, client):
        _create_and_execute(client, "Summary one", ["firewall", "ids"])
        _create_and_execute(client, "Summary two", ["waf"])

        response = client.get("/api/v1/research/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_experiments"] == 2
        assert data["total_trials"] == 2
        assert "ddos" in data["attack_types"]
        for control in ("firewall", "ids", "waf"):
            assert control in data["security_controls"]
        assert data["measurement_modes"] == ["ESTIMATED"]
        assert data["estimated_trials"] == 2
        assert data["measured_trials"] == 0
        assert data["marginal_energy_observations"] == 0
        assert data["interaction_observations"] == 0
        assert data["amplification_observations"] == 0

    def test_summary_counts_persisted_observations(self, client):
        _, baseline = _create_and_execute(client, "Baseline", [])
        _, security = _create_and_execute(client, "Secured", ["firewall"])
        _compute_marginal(
            client, baseline, security, carbon_intensity=420.0
        )

        data = client.get("/api/v1/research/summary").json()
        assert data["marginal_energy_observations"] == 1
        assert data["carbon_observations"] == 1
        assert data["interaction_observations"] == 0
        assert data["amplification_observations"] == 0

    def test_summary_never_reports_measured_trials_for_estimated_data(self, client):
        _create_and_execute(client, "Estimated only", [])
        data = client.get("/api/v1/research/summary").json()
        assert data["measured_trials"] == 0
        assert data["estimated_trials"] >= 1


class TestResearchMetrics:
    def test_metrics_are_unavailable_without_observations(self, client):
        response = client.get("/api/v1/research/metrics")
        assert response.status_code == 200
        data = response.json()
        blocks = (
            "marginal_energy",
            "marginal_power",
            "marginal_carbon",
            "interaction_effect",
            "amplification_energy",
            "amplification_ratio",
        )
        for key in blocks:
            block = data[key]
            assert block["status"] == "unavailable"
            assert block["statistics"] is None
            assert block["observation_count"] == 0
            assert block["reason"]
        assert data["std_dev_convention"] == "population_standard_deviation_n"

    def test_metrics_describe_only_persisted_observations(self, client):
        _, baseline = _create_and_execute(client, "Metric baseline", [])
        _, security = _create_and_execute(client, "Metric secured", ["ids"])
        attribution = _compute_marginal(client, baseline, security)

        data = client.get("/api/v1/research/metrics").json()

        marginal = data["marginal_energy"]
        assert marginal["status"] == "available"
        assert marginal["unit"] == "joules"
        assert marginal["observation_count"] == 1
        assert marginal["statistics"]["count"] == 1
        assert marginal["statistics"]["mean"] == pytest.approx(
            attribution["marginal_energy_joules"]
        )
        assert marginal["statistics"]["min"] == pytest.approx(
            attribution["marginal_energy_joules"]
        )
        assert marginal["statistics"]["max"] == pytest.approx(
            attribution["marginal_energy_joules"]
        )

        carbon = data["marginal_carbon"]
        assert carbon["status"] == "available"
        assert carbon["unit"] == "kg_co2"
        assert carbon["statistics"]["mean"] == pytest.approx(
            attribution["marginal_carbon_kg"]
        )

        interaction = data["interaction_effect"]
        assert interaction["status"] == "unavailable"
        assert interaction["statistics"] is None
        assert interaction["observation_count"] == 0

        amplification = data["amplification_energy"]
        assert amplification["status"] == "unavailable"
        assert amplification["statistics"] is None
