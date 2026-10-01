import pytest
from unittest.mock import MagicMock, patch
from app.services.workload_service import OptimizerService


class TestOptimizerService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = OptimizerService(self.db)

    def test_get_workloads_returns_existing(self):
        mock_workloads = [MagicMock(id=1), MagicMock(id=2)]
        self.service.workload_repo.get_all = MagicMock(return_value=mock_workloads)
        result = self.service.get_workloads()
        assert len(result) == 2

    def test_get_workloads_creates_samples_when_empty(self):
        self.service.workload_repo.get_all = MagicMock(side_effect=[[], [MagicMock(), MagicMock()]])
        self.service.workload_repo.create = MagicMock(return_value=MagicMock(id=1))

        with patch("app.services.workload_service.generate_sample_workloads") as mock_gen:
            mock_gen.return_value = [{"name": "w1"}, {"name": "w2"}]
            result = self.service.get_workloads()
            assert len(result) == 2
            assert self.service.workload_repo.create.call_count == 2

    def test_run_optimization_with_workloads(self):
        mock_workloads = [
            MagicMock(
                id=1, workload_uuid="uuid-1", name="W1", workload_type="log_analysis",
                priority="medium", is_security_critical=False, estimated_cpu_seconds=60,
                estimated_memory_mb=256, estimated_energy_kwh=0.01, estimated_co2_kg=0.005,
                status="scheduled", scheduled_time=None, optimized_time=None,
            ),
        ]
        self.service.workload_repo.get_all = MagicMock(return_value=mock_workloads)

        mock_result_db = MagicMock(id=1)
        self.service.result_repo.create = MagicMock(return_value=mock_result_db)

        with patch("app.services.workload_service.optimize_workloads") as mock_opt:
            mock_opt.return_value = {
                "workloads_analyzed": 1, "workloads_shifted": 0, "workloads_unchanged": 1,
                "critical_protected": 0, "energy_before_kwh": 0.01, "energy_after_kwh": 0.01,
                "co2_before_kg": 0.005, "co2_after_kg": 0.005, "energy_saved_kwh": 0.0,
                "co2_saved_kg": 0.0, "reduction_percentage": 0.0,
            }
            result = self.service.run_optimization()
            assert "result_id" in result
            assert "comparison" in result

    def test_run_optimization_creates_samples_when_empty(self):
        self.service.workload_repo.get_all = MagicMock(side_effect=[[], [MagicMock(id=1)]])
        self.service.workload_repo.create = MagicMock(return_value=MagicMock(id=1))
        self.service.result_repo.create = MagicMock(return_value=MagicMock(id=1))

        with patch("app.services.workload_service.generate_sample_workloads") as mock_gen:
            mock_gen.return_value = [{"name": "w1"}]
            with patch("app.services.workload_service.optimize_workloads") as mock_opt:
                mock_opt.return_value = {
                    "workloads_analyzed": 1, "workloads_shifted": 0, "workloads_unchanged": 1,
                    "critical_protected": 0, "energy_before_kwh": 0.01, "energy_after_kwh": 0.01,
                    "co2_before_kg": 0.005, "co2_after_kg": 0.005, "energy_saved_kwh": 0.0,
                    "co2_saved_kg": 0.0, "reduction_percentage": 0.0,
                }
                result = self.service.run_optimization()
                assert "result_id" in result

    def test_get_history(self):
        mock_history = [MagicMock(id=1), MagicMock(id=2)]
        self.service.result_repo.get_history = MagicMock(return_value=mock_history)
        result = self.service.get_history()
        assert len(result) == 2
        self.service.result_repo.get_history.assert_called_once_with(10)

    def test_get_comparison_with_data(self):
        mock_latest = MagicMock(
            energy_before_kwh=0.1, co2_before_kg=0.05,
            energy_after_kwh=0.08, co2_after_kg=0.04,
            energy_saved_kwh=0.02, co2_saved_kg=0.01, reduction_percentage=20.0,
        )
        self.service.result_repo.get_latest = MagicMock(return_value=mock_latest)
        result = self.service.get_comparison()
        assert result["before"]["energy_kwh"] == 0.1
        assert result["after"]["energy_kwh"] == 0.08
        assert result["comparison"]["energy_saved"] == 0.02
        assert result["comparison"]["reduction_pct"] == 20.0

    def test_get_comparison_no_data(self):
        self.service.result_repo.get_latest = MagicMock(return_value=None)
        result = self.service.get_comparison()
        assert result["before"] == {}
        assert result["after"] == {}
        assert result["comparison"] == {}
        assert result["details"] == []
