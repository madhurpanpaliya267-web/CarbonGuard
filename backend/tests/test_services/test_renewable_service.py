import pytest
from app.services.renewable_service import get_renewable_status


class TestRenewableService:
    def test_returns_required_keys(self):
        result = get_renewable_status()
        assert "renewable_percentage" in result
        assert "solar_availability" in result
        assert "wind_availability" in result
        assert "grid_carbon_intensity" in result
        assert "forecast" in result

    def test_forecast_length(self):
        result = get_renewable_status()
        assert len(result["forecast"]) == 24

    def test_forecast_entries_have_required_fields(self):
        result = get_renewable_status()
        for entry in result["forecast"]:
            assert "timestamp" in entry
            assert "solar" in entry
            assert "wind" in entry
            assert "renewable_pct" in entry
            assert "carbon_intensity" in entry

    def test_renewable_percentage_is_numeric(self):
        result = get_renewable_status()
        assert isinstance(result["renewable_percentage"], float)
        assert isinstance(result["solar_availability"], float)
        assert isinstance(result["wind_availability"], float)
        assert isinstance(result["grid_carbon_intensity"], float)

    def test_carbon_intensity_formula(self):
        result = get_renewable_status()
        solar = result["solar_availability"]
        wind = result["wind_availability"]
        expected_pct = (solar + wind) / 2
        expected_intensity = 475 * (1 - expected_pct / 200)
        assert abs(result["renewable_percentage"] - round(expected_pct, 1)) < 0.2
        assert abs(result["grid_carbon_intensity"] - round(expected_intensity, 1)) < 2.0

    def test_forecast_solar_varies_by_hour(self):
        result = get_renewable_status()
        solars = [f["solar"] for f in result["forecast"]]
        assert max(solars) != min(solars)

    def test_multiple_calls_return_different_values(self):
        r1 = get_renewable_status()
        r2 = get_renewable_status()
        assert r1["renewable_percentage"] != r2["renewable_percentage"] or \
               r1["solar_availability"] != r2["solar_availability"]
