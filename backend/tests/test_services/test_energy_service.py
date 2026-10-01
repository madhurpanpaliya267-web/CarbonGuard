import pytest
from unittest.mock import MagicMock, patch
from app.services.energy_service import EnergyService


class TestEnergyService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = EnergyService(self.db)

    def test_get_overview_with_existing_data(self):
        mock_current = MagicMock(energy_kwh=2.5, total_power_watts=150.0)
        mock_history = [
            MagicMock(energy_kwh=2.0, total_power_watts=120.0),
            MagicMock(energy_kwh=3.0, total_power_watts=180.0),
        ]
        self.service.energy_repo.get_latest = MagicMock(return_value=mock_current)
        self.service.energy_repo.get_history = MagicMock(return_value=mock_history)

        result = self.service.get_overview()
        assert result["current"] == mock_current
        assert len(result["history"]) == 2
        assert result["summary"]["total_energy"] == 5.0
        assert result["summary"]["avg_power"] == 150.0

    def test_get_overview_creates_default_when_no_data(self):
        self.service.energy_repo.get_latest = MagicMock(return_value=None)
        self.service.energy_repo.get_history = MagicMock(return_value=[])
        self.service.energy_repo.create = MagicMock(return_value=MagicMock(
            energy_kwh=0.15, total_power_watts=200.0,
        ))

        result = self.service.get_overview()
        self.service.energy_repo.create.assert_called_once()
        assert result["summary"]["total_energy"] == 0.0

    def test_get_current_with_data(self):
        mock_current = MagicMock(energy_kwh=2.5)
        self.service.energy_repo.get_latest = MagicMock(return_value=mock_current)
        result = self.service.get_current()
        assert result == mock_current

    def test_get_current_creates_default_when_none(self):
        self.service.energy_repo.get_latest = MagicMock(return_value=None)
        self.service.energy_repo.create = MagicMock(return_value=MagicMock(id=1))
        result = self.service.get_current()
        self.service.energy_repo.create.assert_called_once()

    def test_get_history(self):
        mock_history = [MagicMock(), MagicMock(), MagicMock()]
        self.service.energy_repo.get_history = MagicMock(return_value=mock_history)
        result = self.service.get_history(10)
        self.service.energy_repo.get_history.assert_called_once_with(10)
        assert len(result) == 3

    def test_summary_avg_power_empty_history(self):
        self.service.energy_repo.get_latest = MagicMock(return_value=MagicMock())
        self.service.energy_repo.get_history = MagicMock(return_value=[])
        result = self.service.get_overview()
        assert result["summary"]["avg_power"] == 0.0

    def test_overview_calls_estimate_when_no_current(self):
        self.service.energy_repo.get_latest = MagicMock(return_value=None)
        self.service.energy_repo.get_history = MagicMock(return_value=[])
        self.service.energy_repo.create = MagicMock(return_value=MagicMock())

        with patch("app.services.energy_service.estimate_energy_consumption") as mock_est:
            mock_est.return_value = {"energy_kwh": 0.2, "total_power_watts": 200.0}
            self.service.get_overview()
            mock_est.assert_called_once()
