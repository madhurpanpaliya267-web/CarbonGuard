import pytest
from app.services.research_analytics_service import ANALYSIS_VERSION
from app.repositories.research_repo import EnergyMeasurementRepository


def _create_runs(client, attack, intensity, controls, duration=30, trials=1,
                 experiment_type="DEFENSE_AMPLIFICATION"):
    create = client.post(
        "/api/v1/research/experiments",
        json={
            "name": f"{attack}_{intensity}_{'_'.join(controls) or 'baseline'}",
            "experiment_type": experiment_type,
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


def _set_energies(db, run_ids, energies):
    repo = EnergyMeasurementRepository(db)
    for run_id, energy in zip(run_ids, energies):
        repo.get_latest_by_run(run_id).energy_joules = energy
    db.commit()


def _seed_amplification(client, db, trials=3, attack="ddos", control="firewall"):
    baseline = _create_runs(client, attack, "low", [], 30, trials)
    defense = _create_runs(client, attack, "low", [control], 30, trials)
    _set_energies(db, [r["id"] for r in baseline], [100.0] * trials)
    _set_energies(db, [r["id"] for r in defense], [160.0, 200.0, 240.0][:trials])
    response = client.post(
        "/api/v1/research/defense-energy-amplification",
        json={
            "control_name": control,
            "baseline_run_ids": [r["id"] for r in baseline],
            "defense_run_ids": [r["id"] for r in defense],
        },
    )
    assert response.status_code == 201
    return response.json()


def _body(**overrides):
    body = {
        "source": "amplification",
        "metric": "additional_defense_energy",
    }
    body.update(overrides)
    return body


class TestComputeEndpoint:
    def test_successful_analytics_request(self, client, db):
        _seed_amplification(client, db, trials=3)
        response = client.post("/api/v1/research/analytics", json=_body())
        assert response.status_code == 201
        data = response.json()
        assert data["source"] == "amplification"
        assert data["metric"] == "additional_defense_energy"
        assert data["metric_category"] == "difference"
        assert data["analysis_version"] == ANALYSIS_VERSION
        assert data["analysis_id"].startswith("anl_")
        assert data["n"] == 3
        assert data["statistics"]["count"] == 3
        assert data["statistics"]["mean"] == 100.0
        assert data["std_dev_convention"] == "population_standard_deviation_n"
        assert data["paired_differences"] == [60.0, 100.0, 140.0]
        assert data["measurement_mode"] == "ESTIMATED"
        assert data["energy_provider"] == "estimated"
        assert any("ESTIMATED" in item for item in data["limitations"])

    def test_filtering(self, client, db):
        _seed_amplification(client, db, trials=2, attack="ddos")
        _seed_amplification(client, db, trials=3, attack="port_scan")
        response = client.post(
            "/api/v1/research/analytics",
            json=_body(filters={"attack_type": "port_scan"}),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["n"] == 3
        assert data["filters"] == {"attack_type": "port_scan"}

        empty = client.post(
            "/api/v1/research/analytics",
            json=_body(filters={"attack_type": "malware"}),
        )
        assert empty.status_code == 400
        assert "Insufficient observations" in empty.json()["detail"]

    def test_grouping(self, client, db):
        _seed_amplification(client, db, trials=2, attack="ddos")
        _seed_amplification(client, db, trials=3, attack="port_scan")
        response = client.post(
            "/api/v1/research/analytics",
            json=_body(group_by=["attack_type"], include_confidence_interval=False),
        )
        assert response.status_code == 201
        groups = response.json()["groups"]
        assert len(groups) == 2
        assert [g["group"]["attack_type"] for g in groups] == ["ddos", "port_scan"]
        assert groups[0]["n"] == 2
        assert groups[1]["n"] == 3
        assert groups[0]["statistics"]["mean"] == 80.0

    def test_descriptive_statistics_endpoint(self, client, db):
        _seed_amplification(client, db, trials=3)
        stats = client.post(
            "/api/v1/research/analytics", json=_body()
        ).json()["statistics"]
        assert stats == {
            "mean": 100.0,
            "median": 100.0,
            "std_dev": stats["std_dev"],
            "min": 60.0,
            "max": 140.0,
            "count": 3,
        }
        assert abs(stats["std_dev"] - (3200 / 3) ** 0.5) < 1e-9

    def test_paired_analysis_with_statistical_result(self, client, db):
        _seed_amplification(client, db, trials=3)
        response = client.post(
            "/api/v1/research/analytics",
            json=_body(hypothesis_test="paired_t"),
        )
        assert response.status_code == 201
        test = response.json()["hypothesis_test"]
        assert test["test_id"] == "paired_t"
        assert test["test_name"].startswith("Paired t-test")
        assert test["null_hypothesis"] == "Mean paired difference = 0"
        assert test["alternative_hypothesis"] == "Mean paired difference != 0"
        assert test["status"] == "ok"
        assert test["statistic"] is not None
        assert 0.0 <= test["p_value"] <= 1.0
        assert test["sample_count"] == 3
        assert test["significance_level"] == 0.05
        assert test["interpretation"] in ("reject_null", "fail_to_reject_null")
        assert test["effect_size"]["name"] == "cohens_dz"
        assert test["effect_size"]["value"] is not None
        assert "does not imply a configuration is better" in test["method_notes"]

    def test_wilcoxon_hypothesis_test(self, client, db):
        _seed_amplification(client, db, trials=3)
        response = client.post(
            "/api/v1/research/analytics",
            json=_body(hypothesis_test="wilcoxon_signed_rank"),
        )
        test = response.json()["hypothesis_test"]
        assert test["test_id"] == "wilcoxon_signed_rank"
        assert test["p_value"] == 0.25
        assert test["effect_size"]["name"] == "rank_biserial_correlation"

    def test_confidence_interval_included(self, client, db):
        _seed_amplification(client, db, trials=3)
        data = client.post("/api/v1/research/analytics", json=_body()).json()
        ci = data["confidence_interval"]
        assert ci["status"] == "ok"
        assert ci["level"] == 0.95
        assert ci["method"] == "student_t_interval"
        assert ci["lower"] < 100.0 < ci["upper"]

    def test_validation_error_invalid_metric(self, client, db):
        _seed_amplification(client, db, trials=1)
        response = client.post(
            "/api/v1/research/analytics", json=_body(metric="nonsense")
        )
        assert response.status_code == 400
        assert "Invalid metric" in response.json()["detail"]

    def test_validation_error_level_metric_with_test(self, client, db):
        _seed_amplification(client, db, trials=3)
        response = client.post(
            "/api/v1/research/analytics",
            json=_body(metric="energy_attack_only", hypothesis_test="paired_t"),
        )
        assert response.status_code == 400
        assert "level metric" in response.json()["detail"]

    def test_validation_error_invalid_source(self, client, db):
        response = client.post(
            "/api/v1/research/analytics",
            json={"source": "quantum", "metric": "additional_defense_energy"},
        )
        assert response.status_code == 400
        assert "Invalid source" in response.json()["detail"]

    def test_validation_error_unsupported_group(self, client, db):
        response = client.post(
            "/api/v1/research/analytics",
            json=_body(group_by=["control_a"]),
        )
        assert response.status_code == 400
        assert "Group dimension" in response.json()["detail"]

    def test_insufficient_data_empty_selection(self, client, db):
        response = client.post(
            "/api/v1/research/analytics",
            json=_body(filters={"experiment_id": 999999}),
        )
        assert response.status_code == 400
        assert "Insufficient observations" in response.json()["detail"]

    def test_small_sample_returns_structured_warnings(self, client, db):
        _seed_amplification(client, db, trials=1)
        response = client.post(
            "/api/v1/research/analytics", json=_body(hypothesis_test="paired_t")
        )
        assert response.status_code == 201
        data = response.json()
        assert data["n"] == 1
        assert data["hypothesis_test"] is None
        assert data["confidence_interval"]["status"] == "omitted"
        assert any("at least 2" in w for w in data["warnings"])

    def test_schema_requires_source_and_metric(self, client, db):
        response = client.post("/api/v1/research/analytics", json={})
        assert response.status_code == 422
        response = client.post("/api/v1/research/analytics", json={"source": "marginal"})
        assert response.status_code == 422

    def test_deterministic_repeat(self, client, db):
        _seed_amplification(client, db, trials=3)
        body = _body(hypothesis_test="paired_t", group_by=["control_name"])
        first = client.post("/api/v1/research/analytics", json=body).json()
        second = client.post("/api/v1/research/analytics", json=body).json()
        assert first["analysis_id"] == second["analysis_id"]
        assert first["statistics"] == second["statistics"]
        assert first["hypothesis_test"]["p_value"] == second["hypothesis_test"]["p_value"]
        assert first["confidence_interval"]["lower"] == second["confidence_interval"]["lower"]


class TestGetEndpoints:
    def test_list_analytics(self, client, db):
        _seed_amplification(client, db, trials=2)
        client.post("/api/v1/research/analytics", json=_body())
        response = client.get("/api/v1/research/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["items"][0]["metric"] == "additional_defense_energy"

    def test_list_with_filters(self, client, db):
        _seed_amplification(client, db, trials=2)
        client.post("/api/v1/research/analytics", json=_body())
        response = client.get(
            "/api/v1/research/analytics",
            params={"source": "amplification", "metric": "additional_defense_energy"},
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1

        empty = client.get(
            "/api/v1/research/analytics", params={"metric": "no_such_metric"}
        )
        assert empty.status_code == 200
        assert empty.json()["total"] == 0

    def test_get_by_analysis_id(self, client, db):
        _seed_amplification(client, db, trials=3)
        created = client.post("/api/v1/research/analytics", json=_body()).json()
        response = client.get(
            f"/api/v1/research/analytics/{created['analysis_id']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == created["analysis_id"]
        assert data["statistics"] == created["statistics"]

    def test_get_not_found(self, client, db):
        response = client.get("/api/v1/research/analytics/anl_notfound1234")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


