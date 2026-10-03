import pytest
from app.engines.energy.provider import EnergyMeasurementProvider, EnergyReading, MeasurementMode
from app.engines.energy.estimated_provider import EstimatedEnergyProvider, EstimationCoefficients
from app.engines.energy.hardware_providers import RaplEnergyProvider, KeplerEnergyProvider, ExternalMeterProvider
from app.engines.energy.factory import get_provider, get_default_provider, reset_default_provider, list_providers
from app.engines.carbon.energy_estimator import estimate_energy_consumption, estimate_security_workload_energy


class TestEnergyReading:
    def test_to_dict(self):
        reading = EnergyReading(
            energy_joules=100.0,
            power_watts=2.0,
            duration_seconds=50.0,
            source="estimated",
            mode=MeasurementMode.ESTIMATED,
        )
        d = reading.to_dict()
        assert d["energy_joules"] == 100.0
        assert d["power_watts"] == 2.0
        assert d["duration_seconds"] == 50.0
        assert d["source"] == "estimated"
        assert d["mode"] == "ESTIMATED"
        assert "timestamp" in d

    def test_energy_kwh_conversion(self):
        reading = EnergyReading(
            energy_joules=3_600_000,
            power_watts=100.0,
            duration_seconds=3600.0,
            source="test",
            mode=MeasurementMode.ESTIMATED,
        )
        assert reading.energy_kwh == 1.0

    def test_measurement_mode_values(self):
        assert MeasurementMode.MEASURED.value == "MEASURED"
        assert MeasurementMode.ESTIMATED.value == "ESTIMATED"
        assert MeasurementMode.SIMULATED.value == "SIMULATED"


class TestEstimatedEnergyProvider:
    def test_returns_energy_reading(self):
        provider = EstimatedEnergyProvider()
        reading = provider.get_measurement(duration_seconds=60.0)
        assert isinstance(reading, EnergyReading)
        assert reading.energy_joules > 0
        assert reading.power_watts > 0
        assert reading.duration_seconds == 60.0

    def test_mode_is_estimated(self):
        provider = EstimatedEnergyProvider()
        assert provider.get_mode() == MeasurementMode.ESTIMATED

    def test_source_is_estimated(self):
        provider = EstimatedEnergyProvider()
        assert provider.get_source_name() == "estimated"

    def test_is_available(self):
        provider = EstimatedEnergyProvider()
        assert provider.is_available() is True

    def test_deterministic_same_inputs(self):
        provider = EstimatedEnergyProvider()
        r1 = provider.get_measurement(
            duration_seconds=60.0,
            cpu_usage_pct=50.0,
            memory_usage_pct=40.0,
            network_usage_mbps=10.0,
            workload_count=2,
            security_controls_active=3,
            attack_intensity="MEDIUM",
        )
        r2 = provider.get_measurement(
            duration_seconds=60.0,
            cpu_usage_pct=50.0,
            memory_usage_pct=40.0,
            network_usage_mbps=10.0,
            workload_count=2,
            security_controls_active=3,
            attack_intensity="MEDIUM",
        )
        assert r1.energy_joules == r2.energy_joules
        assert r1.power_watts == r2.power_watts

    def test_deterministic_repeated_calls(self):
        provider = EstimatedEnergyProvider()
        results = set()
        for _ in range(20):
            r = provider.get_measurement(
                duration_seconds=30.0,
                cpu_usage_pct=25.0,
                memory_usage_pct=35.0,
            )
            results.add(r.energy_joules)
        assert len(results) == 1, "EstimatedEnergyProvider must be deterministic"

    def test_different_cpu_produces_different_estimate(self):
        provider = EstimatedEnergyProvider()
        r_low = provider.get_measurement(duration_seconds=60.0, cpu_usage_pct=10.0)
        r_high = provider.get_measurement(duration_seconds=60.0, cpu_usage_pct=90.0)
        assert r_high.energy_joules > r_low.energy_joules

    def test_different_memory_produces_different_estimate(self):
        provider = EstimatedEnergyProvider()
        r_low = provider.get_measurement(duration_seconds=60.0, memory_usage_pct=10.0)
        r_high = provider.get_measurement(duration_seconds=60.0, memory_usage_pct=90.0)
        assert r_high.energy_joules > r_low.energy_joules

    def test_different_workload_count_produces_different_estimate(self):
        provider = EstimatedEnergyProvider()
        r1 = provider.get_measurement(duration_seconds=60.0, workload_count=1)
        r5 = provider.get_measurement(duration_seconds=60.0, workload_count=5)
        assert r5.energy_joules > r1.energy_joules

    def test_different_controls_produces_different_estimate(self):
        provider = EstimatedEnergyProvider()
        r0 = provider.get_measurement(duration_seconds=60.0, security_controls_active=0)
        r3 = provider.get_measurement(duration_seconds=60.0, security_controls_active=3)
        assert r3.energy_joules > r0.energy_joules

    def test_attack_intensity_affects_estimate(self):
        provider = EstimatedEnergyProvider()
        r_none = provider.get_measurement(duration_seconds=60.0)
        r_low = provider.get_measurement(duration_seconds=60.0, attack_intensity="LOW")
        r_medium = provider.get_measurement(duration_seconds=60.0, attack_intensity="MEDIUM")
        r_high = provider.get_measurement(duration_seconds=60.0, attack_intensity="HIGH")
        assert r_high.energy_joules > r_medium.energy_joules
        assert r_medium.energy_joules > r_low.energy_joules
        assert r_none.energy_joules == r_medium.energy_joules

    def test_duration_affects_energy(self):
        provider = EstimatedEnergyProvider()
        r30 = provider.get_measurement(duration_seconds=30.0)
        r60 = provider.get_measurement(duration_seconds=60.0)
        assert r60.energy_joules == r30.energy_joules * 2

    def test_custom_coefficients(self):
        custom = EstimationCoefficients(base_power_watts=200.0)
        provider = EstimatedEnergyProvider(coefficients=custom)
        reading = provider.get_measurement(duration_seconds=60.0)
        assert reading.power_watts >= 200.0

    def test_metadata_includes_coefficients(self):
        provider = EstimatedEnergyProvider()
        reading = provider.get_measurement(duration_seconds=60.0)
        assert reading.metadata is not None
        assert "coefficients" in reading.metadata
        assert "workload_count" in reading.metadata
        assert "attack_intensity" in reading.metadata

    def test_no_randomness_across_calls(self):
        provider = EstimatedEnergyProvider()
        readings = [
            provider.get_measurement(duration_seconds=10.0, cpu_usage_pct=float(i))
            for i in range(10)
        ]
        powers = [r.power_watts for r in readings]
        assert len(set(powers)) == 10, "Each different input must produce a different output"


class TestHardwareProviders:
    def test_rapl_unavailable(self):
        provider = RaplEnergyProvider()
        assert provider.is_available() is False
        assert provider.get_mode() == MeasurementMode.MEASURED

    def test_rapl_raises(self):
        provider = RaplEnergyProvider()
        with pytest.raises(NotImplementedError, match="RAPL"):
            provider.get_measurement(duration_seconds=1.0)

    def test_kepler_unavailable(self):
        provider = KeplerEnergyProvider()
        assert provider.is_available() is False
        assert provider.get_mode() == MeasurementMode.MEASURED

    def test_kepler_raises(self):
        provider = KeplerEnergyProvider()
        with pytest.raises(NotImplementedError, match="Kepler"):
            provider.get_measurement(duration_seconds=1.0)

    def test_external_meter_unavailable(self):
        provider = ExternalMeterProvider()
        assert provider.is_available() is False
        assert provider.get_mode() == MeasurementMode.MEASURED

    def test_external_meter_raises(self):
        provider = ExternalMeterProvider()
        with pytest.raises(NotImplementedError, match="External meter"):
            provider.get_measurement(duration_seconds=1.0)

    def test_hardware_source_names(self):
        assert RaplEnergyProvider().get_source_name() == "rapl"
        assert KeplerEnergyProvider().get_source_name() == "kepler"
        assert ExternalMeterProvider().get_source_name() == "external_meter"


class TestProviderFactory:
    def test_get_estimated_provider(self):
        provider = get_provider("estimated")
        assert isinstance(provider, EstimatedEnergyProvider)

    def test_get_rapl_provider(self):
        provider = get_provider("rapl")
        assert isinstance(provider, RaplEnergyProvider)

    def test_get_kepler_provider(self):
        provider = get_provider("kepler")
        assert isinstance(provider, KeplerEnergyProvider)

    def test_get_external_provider(self):
        provider = get_provider("external")
        assert isinstance(provider, ExternalMeterProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown energy provider"):
            get_provider("nonexistent")

    def test_default_provider_is_estimated(self):
        reset_default_provider()
        provider = get_default_provider()
        assert isinstance(provider, EstimatedEnergyProvider)

    def test_list_providers(self):
        providers = list_providers()
        assert "estimated" in providers
        assert "rapl" in providers
        assert "kepler" in providers
        assert "external" in providers
        assert providers["estimated"]["available"] is True
        assert providers["rapl"]["available"] is False


class TestEnergyEstimatorCompatibility:
    def test_estimate_energy_consumption_returns_expected_keys(self):
        result = estimate_energy_consumption(workload_count=1)
        assert "total_power_watts" in result
        assert "energy_kwh" in result
        assert "estimated" in result
        assert "measurement_mode" in result

    def test_estimate_energy_consumption_deterministic(self):
        r1 = estimate_energy_consumption(workload_count=1)
        r2 = estimate_energy_consumption(workload_count=1)
        assert r1["energy_kwh"] == r2["energy_kwh"]
        assert r1["total_power_watts"] == r2["total_power_watts"]

    def test_estimate_security_workload_energy_returns_expected_keys(self):
        result = estimate_security_workload_energy(security_events_count=10)
        assert "energy_kwh" in result
        assert "power_watts" in result
        assert "events_processed" in result
        assert "estimated" in result
        assert "measurement_mode" in result

    def test_estimate_security_workload_energy_scales_with_events(self):
        r10 = estimate_security_workload_energy(security_events_count=10)
        r100 = estimate_security_workload_energy(security_events_count=100)
        assert r100["energy_kwh"] > r10["energy_kwh"]

    def test_measurement_mode_is_estimated(self):
        result = estimate_energy_consumption()
        assert result["measurement_mode"] == "ESTIMATED"
