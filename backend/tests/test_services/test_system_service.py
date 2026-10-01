import pytest
from unittest.mock import MagicMock
from app.services.system_service import SystemService


class TestSystemService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = SystemService(self.db)

    def test_get_health_with_existing_data(self):
        mock_health = MagicMock(
            cpu_utilization=45.0, memory_utilization=60.0, active_workloads=4,
            security_engine_status="online", carbon_engine_status="online",
            ai_engine_status="online", database_status="online", api_status="online",
            simulated=True,
        )
        self.service.metric_repo.get_latest = MagicMock(return_value=mock_health)
        result = self.service.get_health()
        assert result == mock_health

    def test_get_health_creates_default_when_none(self):
        self.service.metric_repo.get_latest = MagicMock(return_value=None)
        self.service.metric_repo.create = MagicMock(return_value=MagicMock(id=1))

        result = self.service.get_health()
        self.service.metric_repo.create.assert_called_once()
        call_data = self.service.metric_repo.create.call_args[0][0]
        assert "cpu_utilization" in call_data
        assert "memory_utilization" in call_data
        assert call_data["security_engine_status"] == "online"
        assert call_data["simulated"] is True

    def test_get_history(self):
        mock_history = [MagicMock(), MagicMock()]
        self.service.metric_repo.get_history = MagicMock(return_value=mock_history)
        result = self.service.get_history(25)
        self.service.metric_repo.get_history.assert_called_once_with(25)
        assert len(result) == 2

    def test_create_current_metrics_ranges(self):
        self.service.metric_repo.get_latest = MagicMock(return_value=None)
        self.service.metric_repo.create = MagicMock(return_value=MagicMock(id=1))

        self.service.get_health()
        call_data = self.service.metric_repo.create.call_args[0][0]
        assert 20 <= call_data["cpu_utilization"] <= 70
        assert 30 <= call_data["memory_utilization"] <= 75
        assert 2 <= call_data["active_workloads"] <= 6

    def test_default_metric_statuses(self):
        self.service.metric_repo.get_latest = MagicMock(return_value=None)
        self.service.metric_repo.create = MagicMock(return_value=MagicMock(id=1))

        self.service.get_health()
        call_data = self.service.metric_repo.create.call_args[0][0]
        assert call_data["security_engine_status"] == "online"
        assert call_data["carbon_engine_status"] == "online"
        assert call_data["ai_engine_status"] == "online"
        assert call_data["database_status"] == "online"
        assert call_data["api_status"] == "online"
