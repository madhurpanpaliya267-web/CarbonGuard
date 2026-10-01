import pytest
from unittest.mock import patch
from app.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    def setup_method(self):
        self.service = AnalyticsService()

    def test_security_analytics_returns_required_keys(self):
        result = self.service.get_security_analytics("7d")
        assert "attacks_over_time" in result
        assert "categories" in result
        assert "severity_dist" in result
        assert "top_sources" in result

    def test_security_analytics_categories_count(self):
        result = self.service.get_security_analytics()
        assert len(result["categories"]) == 6
        for cat in result["categories"]:
            assert "type" in cat
            assert "count" in cat
            assert cat["count"] >= 0

    def test_security_analytics_severity_dist(self):
        result = self.service.get_security_analytics()
        assert len(result["severity_dist"]) == 4
        levels = {s["level"] for s in result["severity_dist"]}
        assert levels == {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

    def test_security_analytics_time_series_24h(self):
        result = self.service.get_security_analytics("24h")
        assert len(result["attacks_over_time"]) == 1

    def test_security_analytics_time_series_7d(self):
        result = self.service.get_security_analytics("7d")
        assert len(result["attacks_over_time"]) == 7

    def test_security_analytics_time_series_30d(self):
        result = self.service.get_security_analytics("30d")
        assert len(result["attacks_over_time"]) == 30

    def test_security_analytics_unknown_period_defaults_to_7(self):
        result = self.service.get_security_analytics("unknown")
        assert len(result["attacks_over_time"]) == 7

    def test_carbon_analytics_returns_required_keys(self):
        result = self.service.get_carbon_analytics()
        assert "emissions_over_time" in result
        assert "savings_over_time" in result
        assert "efficiency_trend" in result

    def test_carbon_analytics_savings_cumulative(self):
        result = self.service.get_carbon_analytics("7d")
        savings = result["savings_over_time"]
        assert len(savings) == 7
        for i in range(1, len(savings)):
            assert savings[i]["cumulative_kg"] >= savings[i - 1]["cumulative_kg"]

    def test_energy_analytics_returns_required_keys(self):
        result = self.service.get_energy_analytics()
        assert "usage_over_time" in result
        assert "by_type" in result
        assert "peak_hours" in result

    def test_energy_analytics_peak_hours_count(self):
        result = self.service.get_energy_analytics()
        assert len(result["peak_hours"]) == 24
        hours = {p["hour"] for p in result["peak_hours"]}
        assert hours == set(range(24))

    def test_energy_analytics_by_type_count(self):
        result = self.service.get_energy_analytics()
        assert len(result["by_type"]) == 4

    def test_optimization_analytics_returns_required_keys(self):
        result = self.service.get_optimization_analytics()
        assert "runs" in result
        assert "avg_reduction" in result
        assert "total_saved_kg" in result
        assert "best_reduction" in result

    def test_optimization_analytics_ranges(self):
        result = self.service.get_optimization_analytics()
        assert 5 <= result["runs"] <= 20
        assert 15 <= result["avg_reduction"] <= 35
        assert 5 <= result["total_saved_kg"] <= 25
        assert 30 <= result["best_reduction"] <= 50

    def test_time_series_dates_are_strings(self):
        result = self.service.get_security_analytics("7d")
        for point in result["attacks_over_time"]:
            assert isinstance(point["date"], str)
            assert len(point["date"]) == 10
