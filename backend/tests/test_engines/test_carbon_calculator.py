from app.engines.carbon.carbon_calculator import (
    calculate_carbon,
    calculate_security_carbon_efficiency,
    calculate_carbon_per_workload,
    carbon_basis_label,
    joules_to_kwh,
    JOULES_PER_KWH,
)


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


class TestJoulesToKwh:
    def test_constant_is_single_source(self):
        assert JOULES_PER_KWH == 3_600_000

    def test_joules_to_kwh_exact(self):
        assert joules_to_kwh(3_600_000) == 1.0
        assert joules_to_kwh(0.0) == 0.0
        assert joules_to_kwh(1_800_000) == 0.5


class TestCarbonBasisLabel:
    def test_measured(self):
        assert carbon_basis_label("MEASURED") == "calculated_from_measured_energy"

    def test_estimated(self):
        assert carbon_basis_label("estimated") == "calculated_from_estimated_energy"

    def test_simulated(self):
        assert carbon_basis_label("simulated") == "calculated_from_simulated_energy"

    def test_missing_mode_is_unknown_not_measured(self):
        assert carbon_basis_label(None) == "calculated_from_unknown_energy_basis"
        assert carbon_basis_label("") == "calculated_from_unknown_energy_basis"


class TestCarbonPerWorkload:
    def test_available_divides_carbon_by_workload(self):
        result = calculate_carbon_per_workload(0.000041, 100.0, "requests_per_second")
        assert result["status"] == "available"
        assert result["value_kg"] == 0.000041 / 100.0
        assert result["unit"] == "kg/requests_per_second"
        assert result["reason"] is None

    def test_negative_carbon_keeps_sign(self):
        result = calculate_carbon_per_workload(-0.5, 10.0, "requests_per_second")
        assert result["status"] == "available"
        assert result["value_kg"] < 0

    def test_missing_carbon_is_unavailable(self):
        result = calculate_carbon_per_workload(None, 10.0, "requests_per_second")
        assert result["status"] == "unavailable"
        assert result["value_kg"] is None

    def test_missing_workload_is_unavailable(self):
        result = calculate_carbon_per_workload(0.5, None, "requests_per_second")
        assert result["status"] == "unavailable"
        assert "missing" in result["reason"]

    def test_zero_workload_is_division_by_zero(self):
        result = calculate_carbon_per_workload(0.5, 0.0, "requests_per_second")
        assert result["status"] == "unavailable"
        assert "zero" in result["reason"]

    def test_negative_workload_is_unavailable(self):
        result = calculate_carbon_per_workload(0.5, -1.0, "requests_per_second")
        assert result["status"] == "unavailable"

    def test_missing_unit_is_unavailable(self):
        result = calculate_carbon_per_workload(0.5, 10.0, None)
        assert result["status"] == "unavailable"
        assert "unit" in result["reason"]
