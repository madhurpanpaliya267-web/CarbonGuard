import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from app.engines.optimizer.workload_optimizer import (
    generate_sample_workloads,
    optimize_workloads,
    PRIORITY_ORDER,
)


class TestGenerateSampleWorkloads:
    def test_default_count(self):
        workloads = generate_sample_workloads()
        assert len(workloads) == 8

    def test_custom_count(self):
        workloads = generate_sample_workloads(3)
        assert len(workloads) == 3

    def test_exceeding_count_returns_max(self):
        workloads = generate_sample_workloads(100)
        assert len(workloads) == 8

    def test_each_workload_has_required_fields(self):
        workloads = generate_sample_workloads()
        required_fields = [
            "workload_uuid", "name", "workload_type", "priority",
            "is_security_critical", "estimated_cpu_seconds", "estimated_memory_mb",
            "estimated_energy_kwh", "estimated_co2_kg", "status",
            "scheduled_time", "created_at",
        ]
        for w in workloads:
            for field in required_fields:
                assert field in w, f"Missing field {field} in workload"

    def test_workloads_have_unique_uuids(self):
        workloads = generate_sample_workloads()
        uuids = [w["workload_uuid"] for w in workloads]
        assert len(uuids) == len(set(uuids))

    def test_workloads_are_scheduled_status(self):
        workloads = generate_sample_workloads()
        for w in workloads:
            assert w["status"] == "scheduled"

    def test_energy_and_co2_are_positive(self):
        workloads = generate_sample_workloads()
        for w in workloads:
            assert w["estimated_energy_kwh"] > 0
            assert w["estimated_co2_kg"] > 0


class TestOptimizeWorkloads:
    def _make_workload(self, uuid="test-uuid", name="Test", priority="medium",
                       critical=False, energy=0.01, co2=0.005, hours_from_now=2):
        return {
            "workload_uuid": uuid,
            "name": name,
            "workload_type": "test",
            "priority": priority,
            "is_security_critical": critical,
            "estimated_cpu_seconds": 60,
            "estimated_memory_mb": 256,
            "estimated_energy_kwh": energy,
            "estimated_co2_kg": co2,
            "status": "scheduled",
            "scheduled_time": datetime.now() + timedelta(hours=hours_from_now),
            "optimized_time": None,
        }

    def test_returns_required_keys(self):
        workloads = [self._make_workload()]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        required_keys = [
            "workloads_analyzed", "workloads_shifted", "workloads_unchanged",
            "critical_protected", "energy_before_kwh", "energy_after_kwh",
            "co2_before_kg", "co2_after_kg", "energy_saved_kwh",
            "co2_saved_kg", "reduction_percentage", "details",
        ]
        for key in required_keys:
            assert key in result

    def test_critical_workloads_not_shifted(self):
        workloads = [
            self._make_workload(uuid="crit-1", critical=True, priority="critical"),
            self._make_workload(uuid="non-1", critical=False, priority="low"),
        ]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        assert result["critical_protected"] == 1

    def test_workload_counts_consistent(self):
        workloads = [
            self._make_workload(uuid="w1", critical=True),
            self._make_workload(uuid="w2", critical=False),
            self._make_workload(uuid="w3", critical=False),
        ]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        assert result["workloads_analyzed"] == 3
        assert result["workloads_shifted"] + result["workloads_unchanged"] == 2

    def test_energy_before_equals_sum(self):
        workloads = [
            self._make_workload(uuid="w1", energy=0.01),
            self._make_workload(uuid="w2", energy=0.02),
        ]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        assert abs(result["energy_before_kwh"] - 0.03) < 1e-6

    def test_co2_saved_non_negative(self):
        workloads = [self._make_workload(uuid=f"w{i}") for i in range(5)]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        assert result["co2_saved_kg"] >= 0
        assert result["energy_saved_kwh"] >= 0

    def test_reduction_percentage_bounded(self):
        workloads = [self._make_workload(uuid=f"w{i}") for i in range(5)]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        assert 0 <= result["reduction_percentage"] <= 100

    def test_empty_workloads(self):
        result = optimize_workloads([], current_carbon_intensity=475.0)
        assert result["workloads_analyzed"] == 0
        assert result["energy_before_kwh"] == 0

    def test_details_list_populated(self):
        workloads = [self._make_workload(uuid="w1"), self._make_workload(uuid="w2")]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        assert len(result["details"]) == 2
        for detail in result["details"]:
            assert "workload_uuid" in detail
            assert "action" in detail
            assert detail["action"] in ("shifted", "unchanged")

    def test_shifted_workloads_have_delay_info(self):
        workloads = [self._make_workload(uuid="w1", critical=False, priority="low")]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        shifted = [d for d in result["details"] if d["action"] == "shifted"]
        if shifted:
            assert "delay_hours" in shifted[0]
            assert "carbon_intensity_after" in shifted[0]

    def test_default_carbon_intensity(self):
        workloads = [self._make_workload()]
        result = optimize_workloads(workloads)
        assert result["workloads_analyzed"] == 1

    def test_non_critical_sorted_by_priority(self):
        workloads = [
            self._make_workload(uuid="low", name="low", priority="low", critical=False),
            self._make_workload(uuid="high", name="high", priority="high", critical=False),
            self._make_workload(uuid="med", name="med", priority="medium", critical=False),
        ]
        result = optimize_workloads(workloads, current_carbon_intensity=475.0)
        detail_names = [d["name"] for d in result["details"]]
        high_idx = detail_names.index("high")
        med_idx = detail_names.index("med")
        low_idx = detail_names.index("low")
        assert high_idx < med_idx < low_idx
