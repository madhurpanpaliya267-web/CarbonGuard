from app.engines.carbon.carbon_calculator import calculate_carbon, calculate_security_carbon_efficiency


class TestCarbonCalculator:
    def test_calculate_carbon_basic(self):
        result = calculate_carbon(1.0, 475.0, 25.0)
        assert "gross_co2_kg" in result
        assert "net_co2_kg" in result
        assert result["gross_co2_kg"] > 0

    def test_calculate_carbon_zero_energy(self):
        result = calculate_carbon(0.0, 475.0, 25.0)
        assert result["gross_co2_kg"] == 0.0

    def test_calculate_carbon_full_renewable(self):
        result = calculate_carbon(1.0, 475.0, 100.0)
        assert result["net_co2_kg"] <= result["gross_co2_kg"]

    def test_security_carbon_efficiency(self):
        result = calculate_security_carbon_efficiency(10, 2.0, 1.0)
        assert "efficiency_score" in result
        assert "rating" in result
        assert 0 <= result["efficiency_score"] <= 100
