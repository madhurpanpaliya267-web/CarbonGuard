"""
Centralized attack profile configuration for research experiments.

All attacks are SAFE, SYNTHETIC, and SIMULATED.
No real traffic, no external systems, no real attacks.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AttackIntensity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class WorkloadSpec:
    value: float
    unit: str

    def to_dict(self) -> dict:
        return {"value": self.value, "unit": self.unit}


@dataclass(frozen=True)
class AttackProfile:
    attack_type: str
    intensity: AttackIntensity
    workload: WorkloadSpec
    duration_seconds: int
    description: str
    detection_method: str
    severity_base: str
    cpu_range: tuple[float, float]
    energy_range: tuple[float, float]
    confidence_range: tuple[float, float]
    supported_controls: tuple[str, ...] = ()
    config_version: str = "1.0.0"

    def to_dict(self) -> dict:
        return {
            "attack_type": self.attack_type,
            "intensity": self.intensity.value,
            "workload": self.workload.to_dict(),
            "duration_seconds": self.duration_seconds,
            "description": self.description,
            "detection_method": self.detection_method,
            "severity_base": self.severity_base,
            "cpu_range": list(self.cpu_range),
            "energy_range": list(self.energy_range),
            "confidence_range": list(self.confidence_range),
            "supported_controls": list(self.supported_controls),
            "config_version": self.config_version,
        }


@dataclass(frozen=True)
class AttackProfileConfig:
    attack_type: str
    display_name: str
    description: str
    workload_unit: str
    intensity_configs: dict  # AttackIntensity -> dict of params
    supported_controls: tuple[str, ...] = ()
    config_version: str = "1.0.0"


DEFAULT_DURATION_SECONDS = 60


ATTACK_PROFILE_CONFIGS: dict[str, AttackProfileConfig] = {
    "ddos": AttackProfileConfig(
        attack_type="ddos",
        display_name="DDoS",
        description="Distributed Denial of Service attack",
        workload_unit="packets_per_second",
        supported_controls=("firewall", "ids", "ips", "waf"),
        intensity_configs={
            AttackIntensity.LOW: {
                "requests_per_second": 100,
                "packets_per_second": 500,
                "duration_seconds": 30,
            },
            AttackIntensity.MEDIUM: {
                "requests_per_second": 1000,
                "packets_per_second": 5000,
                "duration_seconds": 60,
            },
            AttackIntensity.HIGH: {
                "requests_per_second": 10000,
                "packets_per_second": 50000,
                "duration_seconds": 120,
            },
        },
    ),
    "brute_force": AttackProfileConfig(
        attack_type="brute_force",
        display_name="Brute Force",
        description="Brute force login attempt",
        workload_unit="login_attempts",
        supported_controls=("firewall", "authentication", "ids", "siem"),
        intensity_configs={
            AttackIntensity.LOW: {
                "login_attempts": 10,
                "duration_seconds": 30,
            },
            AttackIntensity.MEDIUM: {
                "login_attempts": 100,
                "duration_seconds": 60,
            },
            AttackIntensity.HIGH: {
                "login_attempts": 1000,
                "duration_seconds": 120,
            },
        },
    ),
    "port_scan": AttackProfileConfig(
        attack_type="port_scan",
        display_name="Port Scan",
        description="Port scanning reconnaissance activity",
        workload_unit="scan_requests",
        supported_controls=("firewall", "ids", "endpoint_security"),
        intensity_configs={
            AttackIntensity.LOW: {
                "scan_requests": 20,
                "connection_attempts": 50,
                "duration_seconds": 15,
            },
            AttackIntensity.MEDIUM: {
                "scan_requests": 200,
                "connection_attempts": 500,
                "duration_seconds": 30,
            },
            AttackIntensity.HIGH: {
                "scan_requests": 2000,
                "connection_attempts": 5000,
                "duration_seconds": 60,
            },
        },
    ),
    "sql_injection": AttackProfileConfig(
        attack_type="sql_injection",
        display_name="SQL Injection",
        description="SQL injection attempt",
        workload_unit="requests_per_second",
        supported_controls=("waf", "ids", "siem"),
        intensity_configs={
            AttackIntensity.LOW: {
                "requests_per_second": 5,
                "suspicious_queries": 10,
                "duration_seconds": 30,
            },
            AttackIntensity.MEDIUM: {
                "requests_per_second": 25,
                "suspicious_queries": 50,
                "duration_seconds": 60,
            },
            AttackIntensity.HIGH: {
                "requests_per_second": 100,
                "suspicious_queries": 200,
                "duration_seconds": 120,
            },
        },
    ),
    "suspicious_login": AttackProfileConfig(
        attack_type="suspicious_login",
        display_name="Suspicious Login",
        description="Suspicious login activity detected",
        workload_unit="login_attempts",
        supported_controls=("authentication", "siem", "endpoint_security"),
        intensity_configs={
            AttackIntensity.LOW: {
                "login_attempts": 5,
                "duration_seconds": 30,
            },
            AttackIntensity.MEDIUM: {
                "login_attempts": 25,
                "duration_seconds": 60,
            },
            AttackIntensity.HIGH: {
                "login_attempts": 100,
                "duration_seconds": 120,
            },
        },
    ),
    "malware": AttackProfileConfig(
        attack_type="malware",
        display_name="Malware-like Endpoint Activity",
        description="Malware-like endpoint activity detected",
        workload_unit="processed_events",
        supported_controls=("endpoint_security", "siem", "ids", "runtime_monitoring"),
        intensity_configs={
            AttackIntensity.LOW: {
                "events_per_second": 10,
                "processed_events": 300,
                "duration_seconds": 30,
            },
            AttackIntensity.MEDIUM: {
                "events_per_second": 50,
                "processed_events": 3000,
                "duration_seconds": 60,
            },
            AttackIntensity.HIGH: {
                "events_per_second": 200,
                "processed_events": 24000,
                "duration_seconds": 120,
            },
        },
    ),
    "phishing": AttackProfileConfig(
        attack_type="phishing",
        display_name="Phishing-like Activity",
        description="Phishing-like activity detected",
        workload_unit="processed_events",
        supported_controls=("waf", "siem", "endpoint_security", "logging"),
        intensity_configs={
            AttackIntensity.LOW: {
                "processed_events": 50,
                "duration_seconds": 30,
            },
            AttackIntensity.MEDIUM: {
                "processed_events": 250,
                "duration_seconds": 60,
            },
            AttackIntensity.HIGH: {
                "processed_events": 1000,
                "duration_seconds": 120,
            },
        },
    ),
}

ATTACK_SEVERITY_MAP = {
    "ddos": "HIGH",
    "brute_force": "MEDIUM",
    "port_scan": "LOW",
    "sql_injection": "HIGH",
    "suspicious_login": "MEDIUM",
    "malware": "CRITICAL",
    "phishing": "MEDIUM",
}


class AttackProfileError(Exception):
    pass


def get_supported_attack_types() -> list[str]:
    return list(ATTACK_PROFILE_CONFIGS.keys())


def get_supported_intensities() -> list[str]:
    return [i.value for i in AttackIntensity]


def validate_attack_type(attack_type: str) -> None:
    if attack_type not in ATTACK_PROFILE_CONFIGS:
        raise AttackProfileError(
            f"Unsupported attack type: {attack_type}. "
            f"Supported: {get_supported_attack_types()}"
        )


def validate_intensity(intensity: str) -> AttackIntensity:
    try:
        return AttackIntensity(intensity.lower())
    except ValueError:
        raise AttackProfileError(
            f"Unsupported intensity: {intensity}. "
            f"Supported: {get_supported_intensities()}"
        )


def build_attack_profile(
    attack_type: str,
    intensity: str,
    duration_seconds: Optional[int] = None,
    workload_override: Optional[float] = None,
) -> AttackProfile:
    validate_attack_type(attack_type)
    intensity_enum = validate_intensity(intensity)

    config = ATTACK_PROFILE_CONFIGS[attack_type]
    intensity_config = config.intensity_configs[intensity_enum]

    if duration_seconds is not None:
        if duration_seconds <= 0:
            raise AttackProfileError(
                f"Duration must be positive, got {duration_seconds}"
            )
        effective_duration = duration_seconds
    else:
        effective_duration = intensity_config.get(
            "duration_seconds", DEFAULT_DURATION_SECONDS
        )

    primary_value = workload_override if workload_override is not None else intensity_config.get(
        "packets_per_second",
        intensity_config.get("login_attempts",
        intensity_config.get("scan_requests",
        intensity_config.get("requests_per_second",
        intensity_config.get("processed_events", 0)))),
    )

    if primary_value < 0:
        raise AttackProfileError(
            f"Workload value must be non-negative, got {primary_value}"
        )

    return AttackProfile(
        attack_type=attack_type,
        intensity=intensity_enum,
        workload=WorkloadSpec(value=primary_value, unit=config.workload_unit),
        duration_seconds=effective_duration,
        description=config.description,
        detection_method=_detection_method_for(attack_type),
        severity_base=ATTACK_SEVERITY_MAP[attack_type],
        cpu_range=_cpu_range_for(attack_type, intensity_enum),
        energy_range=_energy_range_for(attack_type, intensity_enum),
        confidence_range=_confidence_range_for(attack_type),
        supported_controls=config.supported_controls,
        config_version=config.config_version,
    )


def _detection_method_for(attack_type: str) -> str:
    methods = {
        "ddos": "Traffic anomaly detection",
        "brute_force": "Authentication pattern analysis",
        "port_scan": "Network traffic monitoring",
        "sql_injection": "Input pattern matching",
        "suspicious_login": "Behavioral analysis",
        "malware": "Signature-based detection",
        "phishing": "Content and URL analysis",
    }
    return methods.get(attack_type, "Unknown")


def _cpu_range_for(attack_type: str, intensity: AttackIntensity) -> tuple[float, float]:
    base_ranges = {
        "ddos": (30, 120),
        "brute_force": (10, 40),
        "port_scan": (5, 15),
        "sql_injection": (15, 50),
        "suspicious_login": (5, 20),
        "malware": (50, 200),
        "phishing": (5, 25),
    }
    base_low, base_high = base_ranges.get(attack_type, (10, 50))
    multiplier = {AttackIntensity.LOW: 1.0, AttackIntensity.MEDIUM: 2.0, AttackIntensity.HIGH: 4.0}
    m = multiplier[intensity]
    return (base_low * m, base_high * m)


def _energy_range_for(attack_type: str, intensity: AttackIntensity) -> tuple[float, float]:
    base_ranges = {
        "ddos": (0.01, 0.05),
        "brute_force": (0.005, 0.02),
        "port_scan": (0.002, 0.008),
        "sql_injection": (0.008, 0.025),
        "suspicious_login": (0.002, 0.01),
        "malware": (0.025, 0.1),
        "phishing": (0.003, 0.015),
    }
    base_low, base_high = base_ranges.get(attack_type, (0.005, 0.03))
    multiplier = {AttackIntensity.LOW: 1.0, AttackIntensity.MEDIUM: 2.5, AttackIntensity.HIGH: 6.0}
    m = multiplier[intensity]
    return (base_low * m, base_high * m)


def _confidence_range_for(attack_type: str) -> tuple[float, float]:
    ranges = {
        "ddos": (0.75, 0.95),
        "brute_force": (0.70, 0.90),
        "port_scan": (0.60, 0.85),
        "sql_injection": (0.80, 0.95),
        "suspicious_login": (0.65, 0.88),
        "malware": (0.85, 0.98),
        "phishing": (0.70, 0.92),
    }
    return ranges.get(attack_type, (0.60, 0.80))


def list_attack_profiles() -> list[dict]:
    result = []
    for attack_type, config in ATTACK_PROFILE_CONFIGS.items():
        result.append({
            "attack_type": attack_type,
            "display_name": config.display_name,
            "description": config.description,
            "workload_unit": config.workload_unit,
            "intensity_levels": list(config.intensity_configs.keys()),
            "supported_controls": list(config.supported_controls),
            "config_version": config.config_version,
        })
    return result


def list_intensity_configs(attack_type: str) -> dict:
    validate_attack_type(attack_type)
    config = ATTACK_PROFILE_CONFIGS[attack_type]
    return {
        intensity.value: params
        for intensity, params in config.intensity_configs.items()
    }
