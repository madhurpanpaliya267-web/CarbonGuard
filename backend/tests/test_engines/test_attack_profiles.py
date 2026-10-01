import pytest
from app.engines.security.attack_profiles import (
    AttackIntensity,
    WorkloadSpec,
    AttackProfile,
    AttackProfileConfig,
    AttackProfileError,
    ATTACK_PROFILE_CONFIGS,
    get_supported_attack_types,
    get_supported_intensities,
    validate_attack_type,
    validate_intensity,
    build_attack_profile,
    list_attack_profiles,
    list_intensity_configs,
)


class TestAttackIntensity:
    def test_has_three_levels(self):
        assert len(AttackIntensity) == 3

    def test_values(self):
        assert AttackIntensity.LOW.value == "low"
        assert AttackIntensity.MEDIUM.value == "medium"
        assert AttackIntensity.HIGH.value == "high"


class TestSupportedAttackTypes:
    def test_all_seven_types_exist(self):
        types = get_supported_attack_types()
        assert len(types) == 7
        expected = {"ddos", "brute_force", "port_scan", "sql_injection",
                     "suspicious_login", "malware", "phishing"}
        assert set(types) == expected

    def test_attack_profile_configs_has_all(self):
        assert len(ATTACK_PROFILE_CONFIGS) == 7


class TestSupportedIntensities:
    def test_has_three_levels(self):
        intensities = get_supported_intensities()
        assert len(intensities) == 3
        assert set(intensities) == {"low", "medium", "high"}


class TestWorkloadSpec:
    def test_to_dict(self):
        w = WorkloadSpec(value=100.0, unit="packets_per_second")
        d = w.to_dict()
        assert d["value"] == 100.0
        assert d["unit"] == "packets_per_second"

    def test_frozen(self):
        w = WorkloadSpec(value=10.0, unit="test")
        with pytest.raises(AttributeError):
            w.value = 20.0


class TestAttackProfile:
    def test_to_dict(self):
        p = AttackProfile(
            attack_type="ddos",
            intensity=AttackIntensity.LOW,
            workload=WorkloadSpec(value=500.0, unit="packets_per_second"),
            duration_seconds=30,
            description="test",
            detection_method="test",
            severity_base="HIGH",
            cpu_range=(30.0, 120.0),
            energy_range=(0.01, 0.05),
            confidence_range=(0.75, 0.95),
        )
        d = p.to_dict()
        assert d["attack_type"] == "ddos"
        assert d["intensity"] == "low"
        assert d["workload"]["value"] == 500.0
        assert d["config_version"] == "1.0.0"


class TestValidateAttackType:
    def test_valid(self):
        validate_attack_type("ddos")

    def test_invalid(self):
        with pytest.raises(AttackProfileError, match="Unsupported attack type"):
            validate_attack_type("nonexistent")


class TestValidateIntensity:
    def test_valid(self):
        assert validate_intensity("low") == AttackIntensity.LOW
        assert validate_intensity("medium") == AttackIntensity.MEDIUM
        assert validate_intensity("high") == AttackIntensity.HIGH

    def test_case_insensitive(self):
        assert validate_intensity("LOW") == AttackIntensity.LOW

    def test_invalid(self):
        with pytest.raises(AttackProfileError, match="Unsupported intensity"):
            validate_intensity("extreme")


class TestBuildAttackProfile:
    def test_ddos_low(self):
        p = build_attack_profile("ddos", "low")
        assert p.attack_type == "ddos"
        assert p.intensity == AttackIntensity.LOW
        assert p.workload.unit == "packets_per_second"
        assert p.workload.value > 0
        assert p.duration_seconds > 0

    def test_ddos_medium(self):
        p = build_attack_profile("ddos", "medium")
        assert p.intensity == AttackIntensity.MEDIUM
        assert p.workload.value >= 5000

    def test_ddos_high(self):
        p = build_attack_profile("ddos", "high")
        assert p.intensity == AttackIntensity.HIGH
        assert p.workload.value >= 50000

    def test_brute_force(self):
        p = build_attack_profile("brute_force", "medium")
        assert p.workload.unit == "login_attempts"
        assert p.workload.value == 100

    def test_port_scan(self):
        p = build_attack_profile("port_scan", "high")
        assert p.workload.unit == "scan_requests"
        assert p.workload.value >= 2000

    def test_sql_injection(self):
        p = build_attack_profile("sql_injection", "low")
        assert p.workload.unit == "requests_per_second"
        assert p.workload.value == 5

    def test_suspicious_login(self):
        p = build_attack_profile("suspicious_login", "high")
        assert p.workload.unit == "login_attempts"
        assert p.workload.value == 100

    def test_malware(self):
        p = build_attack_profile("malware", "medium")
        assert p.workload.unit == "processed_events"
        assert p.workload.value == 3000

    def test_phishing(self):
        p = build_attack_profile("phishing", "low")
        assert p.workload.unit == "processed_events"
        assert p.workload.value == 50

    def test_custom_duration(self):
        p = build_attack_profile("ddos", "low", duration_seconds=45)
        assert p.duration_seconds == 45

    def test_invalid_duration_negative(self):
        with pytest.raises(AttackProfileError, match="Duration must be positive"):
            build_attack_profile("ddos", "low", duration_seconds=-1)

    def test_invalid_duration_zero(self):
        with pytest.raises(AttackProfileError, match="Duration must be positive"):
            build_attack_profile("ddos", "low", duration_seconds=0)

    def test_negative_workload_rejected(self):
        with pytest.raises(AttackProfileError, match="non-negative"):
            build_attack_profile("ddos", "low", workload_override=-100)

    def test_invalid_attack_type(self):
        with pytest.raises(AttackProfileError, match="Unsupported attack type"):
            build_attack_profile("nonexistent", "low")

    def test_invalid_intensity(self):
        with pytest.raises(AttackProfileError, match="Unsupported intensity"):
            build_attack_profile("ddos", "extreme")

    def test_config_version_preserved(self):
        p = build_attack_profile("ddos", "low")
        assert p.config_version == "1.0.0"

    def test_supported_controls_populated(self):
        p = build_attack_profile("ddos", "low")
        assert len(p.supported_controls) > 0
        assert "firewall" in p.supported_controls

    def test_severity_base_populated(self):
        p = build_attack_profile("ddos", "low")
        assert p.severity_base in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_cpu_range_valid(self):
        p = build_attack_profile("ddos", "low")
        assert p.cpu_range[0] < p.cpu_range[1]
        assert p.cpu_range[0] > 0

    def test_energy_range_valid(self):
        p = build_attack_profile("ddos", "low")
        assert p.energy_range[0] < p.energy_range[1]
        assert p.energy_range[0] > 0


class TestListAttackProfiles:
    def test_returns_all_seven(self):
        profiles = list_attack_profiles()
        assert len(profiles) == 7

    def test_has_required_fields(self):
        profiles = list_attack_profiles()
        for p in profiles:
            assert "attack_type" in p
            assert "display_name" in p
            assert "description" in p
            assert "workload_unit" in p
            assert "intensity_levels" in p
            assert "supported_controls" in p


class TestListIntensityConfigs:
    def test_ddos_has_three(self):
        configs = list_intensity_configs("ddos")
        assert len(configs) == 3
        assert "low" in configs
        assert "medium" in configs
        assert "high" in configs

    def test_invalid_type(self):
        with pytest.raises(AttackProfileError):
            list_intensity_configs("nonexistent")


class TestDeterminism:
    def test_same_inputs_same_profile(self):
        p1 = build_attack_profile("ddos", "medium", duration_seconds=60)
        p2 = build_attack_profile("ddos", "medium", duration_seconds=60)
        assert p1.attack_type == p2.attack_type
        assert p1.intensity == p2.intensity
        assert p1.workload.value == p2.workload.value
        assert p1.duration_seconds == p2.duration_seconds

    def test_same_inputs_same_workload(self):
        p1 = build_attack_profile("brute_force", "high")
        p2 = build_attack_profile("brute_force", "high")
        assert p1.workload.value == p2.workload.value

    def test_different_intensity_different_workload(self):
        low = build_attack_profile("ddos", "low")
        high = build_attack_profile("ddos", "high")
        assert high.workload.value > low.workload.value
