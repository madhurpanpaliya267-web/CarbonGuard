import pytest
from unittest.mock import MagicMock, patch
from app.services.carbon_service import CarbonService


class TestCarbonService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = CarbonService(self.db)

    def test_get_overview_with_existing_data(self):
        mock_current = MagicMock(
            total_energy_kwh=3.0, total_co2_kg=1.5, security_energy_kwh=0.8,
            security_co2_kg=0.4, carbon_saved_kg=2.0, carbon_intensity=475.0,
            renewable_percentage=30.0, workload_count=5, security_carbon_efficiency=70.0,
        )
        mock_history = [
            MagicMock(total_energy_kwh=2.5, total_co2_kg=1.2, carbon_saved_kg=1.5, security_carbon_efficiency=65.0),
            MagicMock(total_energy_kwh=3.5, total_co2_kg=1.8, carbon_saved_kg=2.5, security_carbon_efficiency=75.0),
        ]
        self.service.carbon_repo.get_latest = MagicMock(return_value=mock_current)
        self.service.carbon_repo.get_history = MagicMock(return_value=mock_history)

        result = self.service.get_overview()
        assert result["current"] == mock_current
        assert len(result["history"]) == 2
        assert result["summary"]["total_energy"] == 6.0
        assert result["summary"]["total_co2"] == 3.0
        assert result["summary"]["total_saved"] == 4.0
        assert result["summary"]["avg_efficiency"] == 70.0

    def test_get_overview_creates_default_when_no_data(self):
        self.service.carbon_repo.get_latest = MagicMock(return_value=None)
        self.service.carbon_repo.get_history = MagicMock(return_value=[])
        self.service.carbon_repo.create = MagicMock(return_value=MagicMock(
            total_energy_kwh=3.2, total_co2_kg=1.52, security_energy_kwh=0.8,
            security_co2_kg=0.38, carbon_saved_kg=2.1, carbon_intensity=475.0,
            renewable_percentage=34.0, workload_count=5, security_carbon_efficiency=72.5,
        ))

        result = self.service.get_overview()
        self.service.carbon_repo.create.assert_called_once()
        assert result["summary"]["total_energy"] == 0.0

    def test_get_current_with_data(self):
        mock_current = MagicMock(total_energy_kwh=3.0)
        self.service.carbon_repo.get_latest = MagicMock(return_value=mock_current)
        result = self.service.get_current()
        assert result == mock_current

    def test_get_current_creates_default_when_none(self):
        self.service.carbon_repo.get_latest = MagicMock(return_value=None)
        self.service.carbon_repo.create = MagicMock(return_value=MagicMock(id=1))
        result = self.service.get_current()
        self.service.carbon_repo.create.assert_called_once()
        call_data = self.service.carbon_repo.create.call_args[0][0]
        assert call_data["total_energy_kwh"] == 3.2

    def test_get_history(self):
        mock_history = [MagicMock(), MagicMock()]
        self.service.carbon_repo.get_history = MagicMock(return_value=mock_history)
        result = self.service.get_history(10)
        self.service.carbon_repo.get_history.assert_called_once_with(10)
        assert len(result) == 2

    def test_calculate(self):
        result = self.service.calculate(1.0, 475.0, 25.0)
        assert "gross_co2_kg" in result
        assert "net_co2_kg" in result
        assert result["energy_kwh"] == 1.0

    def test_get_efficiency_with_data(self):
        self.service.threat_repo.count_active = MagicMock(return_value=10)
        mock_carbon = MagicMock(security_energy_kwh=2.0, security_co2_kg=1.0)
        self.service.carbon_repo.get_latest = MagicMock(return_value=mock_carbon)

        result = self.service.get_efficiency()
        assert "efficiency_score" in result
        assert "rating" in result

    def test_get_efficiency_no_data(self):
        self.service.threat_repo.count_active = MagicMock(return_value=0)
        self.service.carbon_repo.get_latest = MagicMock(return_value=None)

        result = self.service.get_efficiency()
        assert "efficiency_score" in result

    def test_summary_avg_efficiency_empty_history(self):
        self.service.carbon_repo.get_latest = MagicMock(return_value=MagicMock(
            total_energy_kwh=1.0, total_co2_kg=0.5, carbon_saved_kg=0.3,
            security_carbon_efficiency=80.0,
        ))
        self.service.carbon_repo.get_history = MagicMock(return_value=[])
        result = self.service.get_overview()
        assert result["summary"]["avg_efficiency"] == 0.0
