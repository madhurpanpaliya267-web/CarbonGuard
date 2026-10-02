import csv
import io
import json

import pytest

from app.services.research_export_service import CSV_COLUMNS


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


def _compute_marginal(client, baseline_runs, security_runs):
    response = client.post(
        "/api/v1/research/marginal-energy",
        json={
            "baseline_run_id": baseline_runs[0]["id"],
            "security_run_id": security_runs[0]["id"],
            "carbon_intensity": 350.0,
        },
    )
    assert response.status_code == 201
    return response.json()


def _csv_rows(response):
    return list(csv.reader(io.StringIO(response.text)))


class TestCsvExport:
    def test_csv_defaults_to_marginal_energy_dataset(self, client):
        response = client.get("/api/v1/research/export/csv")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert (
            "carbon_guard_research_marginal_energy.csv"
            in response.headers["content-disposition"]
        )
        rows = _csv_rows(response)
        assert rows[0] == CSV_COLUMNS["marginal_energy"]

    def test_csv_empty_dataset_emits_header_only(self, client):
        for dataset in CSV_COLUMNS:
            response = client.get(
                "/api/v1/research/export/csv", params={"dataset": dataset}
            )
            assert response.status_code == 200
            rows = _csv_rows(response)
            assert len(rows) == 1, f"{dataset} produced fabricated rows"
            assert rows[0] == CSV_COLUMNS[dataset]

    def test_csv_unsupported_dataset_rejected(self, client):
        response = client.get(
            "/api/v1/research/export/csv", params={"dataset": "threats"}
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Unsupported export dataset" in detail
        assert "marginal_energy" in detail

    def test_csv_non_string_dataset_rejected_by_schema(self, client):
        response = client.get(
            "/api/v1/research/export/csv", params={"dataset": 7}
        )
        assert response.status_code in (400, 422)

    def test_csv_experiments_contains_persisted_rows(self, client):
        experiment, _ = _create_and_execute(client, "CSV Experiment", ["waf"])

        response = client.get(
            "/api/v1/research/export/csv", params={"dataset": "experiments"}
        )
        assert response.status_code == 200
        rows = _csv_rows(response)
        assert len(rows) == 2
        record = dict(zip(rows[0], rows[1]))
        assert record["experiment_uuid"] == experiment["experiment_uuid"]
        assert record["attack_type"] == "ddos"
        assert record["measurement_mode"] == "ESTIMATED"
        assert record["status"] == "completed"

    def test_csv_marginal_energy_contains_persisted_rows(self, client):
        _, baseline = _create_and_execute(client, "CSV baseline", [])
        _, security = _create_and_execute(client, "CSV secured", ["firewall"])
        attribution = _compute_marginal(client, baseline, security)

        response = client.get(
            "/api/v1/research/export/csv", params={"dataset": "marginal_energy"}
        )
        rows = _csv_rows(response)
        assert len(rows) == 2
        record = dict(zip(rows[0], rows[1]))
        assert int(record["id"]) == attribution["id"]
        assert float(record["marginal_energy_joules"]) == pytest.approx(
            attribution["marginal_energy_joules"]
        )
        assert record["formula_version"] == "marginal_energy_v1"
        assert record["measurement_mode"] == "ESTIMATED"


class TestJsonExport:
    def test_json_export_shape_on_empty_store(self, client):
        response = client.get("/api/v1/research/export/json")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert (
            "carbon_guard_research.json"
            in response.headers["content-disposition"]
        )
        data = response.json()
        assert set(data) == {
            "exported_at",
            "record_counts",
            "experiments",
            "marginal_energy",
            "interaction_effects",
            "defense_amplification",
        }
        assert data["record_counts"] == {
            "experiments": 0,
            "marginal_energy": 0,
            "interaction_effects": 0,
            "defense_amplification": 0,
        }
        assert data["experiments"] == []
        assert data["marginal_energy"] == []
        assert data["interaction_effects"] == []
        assert data["defense_amplification"] == []

    def test_json_export_serialises_dto_fields_not_orm_state(self, client):
        experiment, baseline = _create_and_execute(client, "JSON baseline", [])
        _, security = _create_and_execute(client, "JSON secured", ["ids"])
        attribution = _compute_marginal(client, baseline, security)

        response = client.get("/api/v1/research/export/json")
        assert response.status_code == 200
        data = response.json()

        assert data["record_counts"]["experiments"] == 2
        assert data["record_counts"]["marginal_energy"] == 1
        assert data["record_counts"]["interaction_effects"] == 0
        assert data["record_counts"]["defense_amplification"] == 0
        assert "_sa_instance_state" not in json.dumps(data)

        exported_uuids = {row["experiment_uuid"] for row in data["experiments"]}
        assert experiment["experiment_uuid"] in exported_uuids

        exported_attribution = data["marginal_energy"][0]
        assert exported_attribution["id"] == attribution["id"]
        assert exported_attribution["formula_version"] == "marginal_energy_v1"
        assert exported_attribution["marginal_carbon_per_workload"]["status"] in (
            "available",
            "unavailable",
        )
