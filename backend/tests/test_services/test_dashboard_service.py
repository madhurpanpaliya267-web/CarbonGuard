import pytest
from unittest.mock import MagicMock, patch
from app.services.dashboard_service import DashboardService


class TestDashboardService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = DashboardService(self.db)

    @patch("app.services.dashboard_service.SystemMetricRepository")
    @patch("app.services.dashboard_service.AIRecommendationRepository")
    @patch("app.services.dashboard_service.WorkloadRepository")
    @patch("app.services.dashboard_service.EnergyMetricRepository")
    @patch("app.services.dashboard_service.CarbonMetricRepository")
    @patch("app.services.dashboard_service.ThreatRepository")
    @patch("app.services.dashboard_service.SecurityEventRepository")
    def test_get_metrics_returns_all_keys(
        self, mock_event_repo, mock_threat_repo, mock_carbon_repo,
        mock_energy_repo, mock_workload_repo, mock_ai_repo, mock_system_repo,
    ):
        mock_threat_repo.return_value.count_active.return_value = 3
        mock_event_repo.return_value.count.return_value = 50
        mock_carbon_repo.return_value.get_latest.return_value = MagicMock()
        mock_energy_repo.return_value.get_latest.return_value = MagicMock()
        mock_system_repo.return_value.get_latest.return_value = MagicMock()

        result = self.service.get_metrics()
        expected_keys = [
            "carbon_guard_score", "security_risk_score", "current_threat_level",
            "active_threats", "threats_detected_24h", "threats_blocked_24h",
            "energy_consumption_kwh", "estimated_co2_kg", "carbon_saved_kg",
            "renewable_percentage", "current_workload", "security_carbon_efficiency",
        ]
        for key in expected_keys:
            assert key in result

    @patch("app.services.dashboard_service.SystemMetricRepository")
    @patch("app.services.dashboard_service.AIRecommendationRepository")
    @patch("app.services.dashboard_service.WorkloadRepository")
    @patch("app.services.dashboard_service.EnergyMetricRepository")
    @patch("app.services.dashboard_service.CarbonMetricRepository")
    @patch("app.services.dashboard_service.ThreatRepository")
    @patch("app.services.dashboard_service.SecurityEventRepository")
    def test_threat_level_scales_with_active_threats(
        self, mock_event_repo, mock_threat_repo, mock_carbon_repo,
        mock_energy_repo, mock_workload_repo, mock_ai_repo, mock_system_repo,
    ):
        mock_threat_repo.return_value.count_active.return_value = 0
        mock_event_repo.return_value.count.return_value = 0
        mock_carbon_repo.return_value.get_latest.return_value = None
        mock_energy_repo.return_value.get_latest.return_value = None
        mock_system_repo.return_value.get_latest.return_value = None

        result = self.service.get_metrics()
        assert result["current_threat_level"] == "LOW"

    @patch("app.services.dashboard_service.SystemMetricRepository")
    @patch("app.services.dashboard_service.AIRecommendationRepository")
    @patch("app.services.dashboard_service.WorkloadRepository")
    @patch("app.services.dashboard_service.EnergyMetricRepository")
    @patch("app.services.dashboard_service.CarbonMetricRepository")
    @patch("app.services.dashboard_service.ThreatRepository")
    @patch("app.services.dashboard_service.SecurityEventRepository")
    def test_metrics_are_numeric(
        self, mock_event_repo, mock_threat_repo, mock_carbon_repo,
        mock_energy_repo, mock_workload_repo, mock_ai_repo, mock_system_repo,
    ):
        mock_threat_repo.return_value.count_active.return_value = 2
        mock_event_repo.return_value.count.return_value = 10
        mock_carbon_repo.return_value.get_latest.return_value = MagicMock()
        mock_energy_repo.return_value.get_latest.return_value = MagicMock()
        mock_system_repo.return_value.get_latest.return_value = MagicMock()

        result = self.service.get_metrics()
        assert isinstance(result["carbon_guard_score"], float)
        assert isinstance(result["security_risk_score"], float)
        assert isinstance(result["energy_consumption_kwh"], float)
        assert isinstance(result["active_threats"], int)

    def test_threat_activity_chart(self):
        result = self.service.get_threat_activity_chart("24h")
        assert "data_points" in result
        assert len(result["data_points"]) == 24
        for dp in result["data_points"]:
            assert "timestamp" in dp
            assert "count" in dp
            assert "critical" in dp

    def test_carbon_emissions_chart(self):
        result = self.service.get_carbon_emissions_chart("24h")
        assert "data_points" in result
        assert len(result["data_points"]) == 24
        for dp in result["data_points"]:
            assert "co2_kg" in dp
            assert "energy_kwh" in dp

    def test_energy_consumption_chart(self):
        result = self.service.get_energy_consumption_chart("24h")
        assert "data_points" in result
        assert len(result["data_points"]) == 24
        for dp in result["data_points"]:
            assert "total" in dp
            assert "security" in dp
            assert "non_security" in dp

    def test_carbon_savings_chart_cumulative(self):
        result = self.service.get_carbon_savings_chart()
        assert "data_points" in result
        assert len(result["data_points"]) == 30
        for dp in result["data_points"]:
            assert "saved_kg" in dp
            assert "cumulative_saved_kg" in dp
        data = result["data_points"]
        for i in range(1, len(data)):
            assert data[i]["cumulative_saved_kg"] >= data[i - 1]["cumulative_saved_kg"]

    def test_threat_categories_chart_percentages_sum(self):
        result = self.service.get_threat_categories_chart()
        assert "categories" in result
        total_pct = sum(c["percentage"] for c in result["categories"])
        assert abs(total_pct - 100.0) < 1.0

    def test_threat_severity_chart_percentages_sum(self):
        result = self.service.get_threat_severity_chart()
        assert "severities" in result
        total_pct = sum(s["percentage"] for s in result["severities"])
        assert abs(total_pct - 100.0) < 1.0
