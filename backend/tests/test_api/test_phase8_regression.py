"""Phase 8 regression guard: Phases 1-7 functionality remains unchanged."""

from app.engines.carbon.carbon_calculator import calculate_carbon


class TestPhase1Smoke:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_carbon_formula_unchanged(self):
        result = calculate_carbon(1.0, 475, 0)
        assert abs(result["gross_co2_kg"] - 0.475) < 1e-12

    def test_carbon_renewable_offset_unchanged(self):
        result = calculate_carbon(1.0, 475, 50)
        assert abs(result["gross_co2_kg"] - 0.475) < 1e-12
        assert abs(result["net_co2_kg"] - 0.2375) < 1e-12

    def test_dashboard_responds(self, client):
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200


class TestPhase3Smoke:
    def test_attack_types_listed(self, client):
        response = client.get("/api/v1/simulator/attack-types")
        assert response.status_code == 200


class TestPhase4Smoke:
    def test_experiment_lifecycle(self, client):
        create = client.post(
            "/api/v1/research/experiments",
            json={
                "name": "regression_lifecycle",
                "experiment_type": "DEFENSE_AMPLIFICATION",
                "attack_type": "ddos",
                "attack_intensity": "low",
                "security_controls": ["firewall"],
                "duration_seconds": 30,
                "number_of_trials": 1,
            },
        )
        assert create.status_code == 201
        uuid = create.json()["experiment_uuid"]
        execute = client.post(f"/api/v1/research/experiments/{uuid}/execute")
        assert execute.status_code == 200
        runs = client.get(f"/api/v1/research/experiments/{uuid}/runs")
        assert runs.status_code == 200
        assert len(runs.json()["items"]) == 1


class TestPhase5Regression:
    def test_marginal_energy_formula_unchanged(self, client):
        baseline = client.post(
            "/api/v1/research/experiments",
            json={
                "name": "regression_p5_base",
                "experiment_type": "MARGINAL_ENERGY",
                "attack_type": "ddos",
                "attack_intensity": "low",
                "security_controls": [],
                "duration_seconds": 30,
                "number_of_trials": 1,
            },
        ).json()
        security = client.post(
            "/api/v1/research/experiments",
            json={
                "name": "regression_p5_fw",
                "experiment_type": "MARGINAL_ENERGY",
                "attack_type": "ddos",
                "attack_intensity": "low",
                "security_controls": ["firewall"],
                "duration_seconds": 30,
                "number_of_trials": 1,
            },
        ).json()
        client.post(f"/api/v1/research/experiments/{baseline['experiment_uuid']}/execute")
        client.post(f"/api/v1/research/experiments/{security['experiment_uuid']}/execute")
        base_runs = client.get(
            f"/api/v1/research/experiments/{baseline['experiment_uuid']}/runs"
        ).json()["items"]
        sec_runs = client.get(
            f"/api/v1/research/experiments/{security['experiment_uuid']}/runs"
        ).json()["items"]

        response = client.post(
            "/api/v1/research/marginal-energy",
            json={
                "baseline_run_id": base_runs[0]["id"],
                "security_run_id": sec_runs[0]["id"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert (
            data["marginal_energy_joules"]
            == data["security_energy_joules"] - data["baseline_energy_joules"]
        )
        assert data["formula_version"] == "marginal_energy_v1"
        assert data["measurement_mode"] == "ESTIMATED"


class TestPhase6Regression:
    def test_interaction_formula_unchanged(self, client):
        def runs(controls):
            created = client.post(
                "/api/v1/research/experiments",
                json={
                    "name": f"regression_p6_{'_'.join(controls) or 'base'}",
                    "experiment_type": "INTERACTION",
                    "attack_type": "ddos",
                    "attack_intensity": "low",
                    "security_controls": controls,
                    "duration_seconds": 30,
                    "number_of_trials": 1,
                },
            ).json()
            client.post(
                f"/api/v1/research/experiments/{created['experiment_uuid']}/execute"
            )
            return [
                r["id"]
                for r in client.get(
                    f"/api/v1/research/experiments/{created['experiment_uuid']}/runs"
                ).json()["items"]
            ]

        baseline = runs([])
        control_a = runs(["firewall"])
        control_b = runs(["ids"])
        combined = runs(["firewall", "ids"])
        response = client.post(
            "/api/v1/research/interaction-effects",
            json={
                "control_a": "firewall",
                "control_b": "ids",
                "baseline_run_ids": baseline,
                "control_a_run_ids": control_a,
                "control_b_run_ids": control_b,
                "combined_run_ids": combined,
            },
        )
        assert response.status_code == 201
        data = response.json()
        row = data["results"][0]
        expected = (
            row["energy_ab"] - row["energy_a"] - row["energy_b"] + row["energy_baseline"]
        )
        assert row["interaction_effect"] == expected
        assert row["formula_version"] == "interaction_effect_v1"


class TestPhase7Regression:
    def test_amplification_formula_unchanged(self, client):
        def runs(controls):
            created = client.post(
                "/api/v1/research/experiments",
                json={
                    "name": f"regression_p7_{'_'.join(controls) or 'base'}",
                    "experiment_type": "DEFENSE_AMPLIFICATION",
                    "attack_type": "ddos",
                    "attack_intensity": "low",
                    "security_controls": controls,
                    "duration_seconds": 30,
                    "number_of_trials": 1,
                },
            ).json()
            client.post(
                f"/api/v1/research/experiments/{created['experiment_uuid']}/execute"
            )
            return [
                r["id"]
                for r in client.get(
                    f"/api/v1/research/experiments/{created['experiment_uuid']}/runs"
                ).json()["items"]
            ]

        baseline = runs([])
        defense = runs(["firewall"])
        response = client.post(
            "/api/v1/research/defense-energy-amplification",
            json={
                "control_name": "firewall",
                "baseline_run_ids": baseline,
                "defense_run_ids": defense,
            },
        )
        assert response.status_code == 201
        row = response.json()["results"][0]
        assert (
            row["additional_defense_energy"]
            == row["energy_attack_defense"] - row["energy_attack_only"]
        )
        assert (
            row["defense_energy_amplification"]
            == row["additional_defense_energy"] / row["attack_workload"]
        )
        assert row["formula_version"] == "defense_energy_amplification_v1"
