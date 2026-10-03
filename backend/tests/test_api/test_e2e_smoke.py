"""Phase 17 integration audit: one end-to-end smoke test.

Covers the full synthetic chain without performing any real attack:

    attack -> threat -> risk -> defense -> energy -> carbon
        -> research experiment/run persistence
        -> API responses -> frontend-consumable result shape

Uses only the existing simulated attack system and the estimated energy
provider, so every value stays clearly labeled (SYNTHETIC / ESTIMATED).
"""

FRONTEND_RESULT_KEYS = (
    "status",
    "event",
    "attack",
    "threat",
    "risk",
    "defense",
    "security_controls",
    "energy",
    "carbon",
    "comparison",
    "research",
    "analytics",
    "provenance",
    "stages",
    "warnings",
)


class TestEndToEndSmoke:
    def test_full_chain_attack_to_frontend_result(self, client):
        # 1. Research experiment exists first so the pipeline can record on it.
        created = client.post(
            "/api/v1/research/experiments",
            json={
                "name": "phase17 smoke experiment",
                "experiment_type": "MARGINAL_ENERGY",
                "attack_type": "ddos",
                "attack_intensity": "low",
                "duration_seconds": 30,
                "number_of_trials": 1,
                "measurement_provider": "estimated",
            },
        )
        assert created.status_code == 201, created.text
        experiment_uuid = created.json()["experiment_uuid"]

        # 2. One end-to-end pipeline run with research recording.
        run = client.post(
            "/api/v1/orchestration/run",
            json={
                "attack_type": "ddos",
                "intensity": "low",
                "record_research": True,
                "experiment_uuid": experiment_uuid,
            },
        )
        assert run.status_code == 200, run.text
        result = run.json()

        # Frontend-consumable shape: every OrchestrationResult key present.
        for key in FRONTEND_RESULT_KEYS:
            assert key in result, f"missing {key}"
        assert result["status"] in ("completed", "partial")

        # Attack -> threat -> risk -> defense chain.
        assert result["event"]["id"] is not None
        assert result["threat"]["threat_uuid"]
        assert isinstance(result["risk"]["risk_score"], float)
        assert result["defense"]["basis"] == "rule_based"
        assert isinstance(result["defense"]["selected"], list)
        assert result["security_controls"] == result["defense"]["selected"]

        # Energy -> carbon with explicit provenance.
        energy = result["energy"]
        assert energy["status"] == "completed"
        assert energy["measurement_mode"] == "ESTIMATED"
        assert isinstance(energy["energy_kwh"], float)
        carbon = result["carbon"]
        assert carbon["status"] == "completed"
        assert carbon["carbon_basis"] == "calculated_from_estimated_energy"
        assert isinstance(carbon["net_co2_kg"], float)

        provenance = result["provenance"]
        assert provenance["data_classification"] == "SYNTHETIC"
        assert provenance["simulated_attack"] is True
        assert provenance["measurement_mode"] == "ESTIMATED"
        assert provenance["control_selection"] == "rule_based"

        # Research observation recorded on the experiment.
        research = result["research"]
        assert research["status"] == "recorded", research
        assert research["run_id"] is not None
        assert research["trial_number"] == 1

        # Stages cover the whole lifecycle for display in the frontend.
        steps = [stage["step"] for stage in result["stages"]]
        for expected in (
            "Defense Selection",
            "Defense Energy Measurement",
            "Defense Carbon Calculation",
            "Research Observation",
            "Analytics",
        ):
            assert expected in steps, f"missing stage {expected}"

        # 3. Persistence: the run, measurement and security effect are stored.
        summary = client.get(
            f"/api/v1/research/experiments/{experiment_uuid}/summary"
        )
        assert summary.status_code == 200, summary.text
        payload = summary.json()
        assert len(payload["runs"]) == 1
        assert len(payload["measurements"]) >= 1
        assert payload["measurements"][0]["measurement_mode"] == "ESTIMATED"
        assert len(payload["security_effects"]) >= 1

        # 4. Security feeds consumed by dashboard/analytics pages.
        stats = client.get("/api/v1/security/stats")
        assert stats.status_code == 200
        assert stats.json()["total_events"] >= 1
        threat_stats = client.get("/api/v1/threats/stats")
        assert threat_stats.status_code == 200
        assert threat_stats.json()["total_threats"] >= 1

        # 5. Aggregates consumed by the Research Lab overview/metrics pages.
        research_summary = client.get("/api/v1/research/summary")
        assert research_summary.status_code == 200
        rs = research_summary.json()
        assert rs["total_trials"] >= 1
        assert rs["estimated_trials"] >= 1
        assert "ESTIMATED" in rs["measurement_modes"]

        metrics = client.get("/api/v1/research/metrics")
        assert metrics.status_code == 200
        block = metrics.json()["marginal_energy"]
        assert block["status"] in ("available", "unavailable")
        assert "observation_count" in block
        assert "statistics" in block

        # 6. Export consumed by the Research Dataset page.
        export = client.get(
            "/api/v1/research/export/csv", params={"dataset": "experiments"}
        )
        assert export.status_code == 200
        assert "ddos" in export.text
