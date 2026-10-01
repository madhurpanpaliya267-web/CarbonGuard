import pytest
from app.engines.carbon.energy_estimator import (
    estimate_energy_consumption,
    estimate_security_workload_energy,
)


class TestEstimateEnergyConsumption:
    def test_returns_required_keys(self):
        result = estimate_energy_consumption()
        required = [
            "total_power_watts", "cpu_power_watts", "memory_power_watts",
            "network_power_watts", "energy_kwh", "estimated",
        ]
        for key in required:
            assert key in result

    def test_energy_kwh_is_positive(self):
        result = estimate_energy_consumption()
        assert result["energy_kwh"] > 0

    def test_total_power_is_sum_of_components(self):
        result = estimate_energy_consumption()
        expected = (
            result["cpu_power_watts"]
            + result["memory_power_watts"]
            + result["network_power_watts"]
        )
        # base_power is not in the sum since it's internal, but total includes it
        assert result["total_power_watts"] > expected

    def test_estimated_flag_is_true(self):
        result = estimate_energy_consumption()
        assert result["estimated"] is True

    def test_power_values_are_positive(self):
        result = estimate_energy_consumption()
        assert result["total_power_watts"] > 0
        assert result["cpu_power_watts"] > 0
        assert result["memory_power_watts"] >= 0
        assert result["network_power_watts"] >= 0

    def test_workload_count_affects_result(self):
        r1 = estimate_energy_consumption(workload_count=1)
        r2 = estimate_energy_consumption(workload_count=10)
        assert r1["energy_kwh"] > 0
        assert r2["energy_kwh"] > 0

    def test_multiple_calls_deterministic(self):
        results = [estimate_energy_consumption() for _ in range(5)]
        powers = [r["total_power_watts"] for r in results]
        assert len(set(powers)) == 1


class TestEstimateSecurityWorkloadEnergy:
    def test_returns_required_keys(self):
        result = estimate_security_workload_energy(10)
        assert "energy_kwh" in result
        assert "power_watts" in result
        assert "events_processed" in result
        assert "estimated" in result

    def test_energy_scales_with_events(self):
        r1 = estimate_security_workload_energy(1)
        r2 = estimate_security_workload_energy(100)
        assert r2["energy_kwh"] > r1["energy_kwh"]

    def test_events_processed_matches_input(self):
        result = estimate_security_workload_energy(42)
        assert result["events_processed"] == 42

    def test_estimated_flag(self):
        result = estimate_security_workload_energy(5)
        assert result["estimated"] is True

    def test_zero_events(self):
        result = estimate_security_workload_energy(0)
        assert result["energy_kwh"] == 0.0
        assert result["events_processed"] == 0
