"""
Security control registry for research experiments.

Provides a centralized registry of security controls with metadata.
Controls are purely descriptive — no real enforcement logic.
Energy cost is handled by the EnergyMeasurementProvider, not here.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ControlCategory(Enum):
    NETWORK = "network"
    ENDPOINT = "endpoint"
    IDENTITY = "identity"
    DATA = "data"
    MONITORING = "monitoring"
    APPLICATION = "application"


@dataclass(frozen=True)
class SecurityControl:
    control_id: str
    display_name: str
    category: ControlCategory
    description: str
    supported_attack_types: tuple[str, ...]
    config_parameters: dict = field(default_factory=dict)
    enabled_by_default: bool = True

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "display_name": self.display_name,
            "category": self.category.value,
            "description": self.description,
            "supported_attack_types": list(self.supported_attack_types),
            "config_parameters": self.config_parameters,
            "enabled_by_default": self.enabled_by_default,
        }


SECURITY_CONTROLS: dict[str, SecurityControl] = {
    "firewall": SecurityControl(
        control_id="firewall",
        display_name="Firewall",
        category=ControlCategory.NETWORK,
        description="Network traffic filtering and access control",
        supported_attack_types=("ddos", "brute_force", "port_scan"),
        config_parameters={
            "rules_count": {"type": "int", "default": 100, "description": "Number of active firewall rules"},
            "block_threshold_pps": {"type": "int", "default": 1000, "description": "Packets per second threshold for blocking"},
        },
    ),
    "ids": SecurityControl(
        control_id="ids",
        display_name="Intrusion Detection System",
        category=ControlCategory.NETWORK,
        description="Network-based intrusion detection and alerting",
        supported_attack_types=("ddos", "brute_force", "port_scan", "sql_injection", "malware"),
        config_parameters={
            "signature_count": {"type": "int", "default": 50000, "description": "Number of detection signatures"},
            "alert_threshold": {"type": "float", "default": 0.7, "description": "Confidence threshold for alerts"},
        },
    ),
    "ips": SecurityControl(
        control_id="ips",
        display_name="Intrusion Prevention System",
        category=ControlCategory.NETWORK,
        description="Active intrusion prevention and automated blocking",
        supported_attack_types=("ddos", "brute_force", "sql_injection"),
        config_parameters={
            "auto_block": {"type": "bool", "default": True, "description": "Enable automatic blocking"},
            "response_time_ms": {"type": "int", "default": 100, "description": "Response time in milliseconds"},
        },
    ),
    "waf": SecurityControl(
        control_id="waf",
        display_name="Web Application Firewall",
        category=ControlCategory.APPLICATION,
        description="Web application layer protection against HTTP attacks",
        supported_attack_types=("ddos", "sql_injection", "phishing"),
        config_parameters={
            "rule_set": {"type": "str", "default": "owasp_top_10", "description": "Active rule set"},
            "request_inspection": {"type": "bool", "default": True, "description": "Enable deep request inspection"},
        },
    ),
    "endpoint_security": SecurityControl(
        control_id="endpoint_security",
        display_name="Endpoint Security",
        category=ControlCategory.ENDPOINT,
        description="Host-based threat detection and prevention",
        supported_attack_types=("malware", "port_scan", "suspicious_login", "phishing"),
        config_parameters={
            "real_time_scan": {"type": "bool", "default": True, "description": "Enable real-time file scanning"},
            "behavioral_analysis": {"type": "bool", "default": True, "description": "Enable behavioral analysis"},
        },
    ),
    "authentication": SecurityControl(
        control_id="authentication",
        display_name="Authentication System",
        category=ControlCategory.IDENTITY,
        description="Identity verification and access control",
        supported_attack_types=("brute_force", "suspicious_login"),
        config_parameters={
            "mfa_enabled": {"type": "bool", "default": True, "description": "Multi-factor authentication enabled"},
            "lockout_threshold": {"type": "int", "default": 5, "description": "Failed attempts before lockout"},
            "lockout_duration_seconds": {"type": "int", "default": 900, "description": "Lockout duration"},
        },
    ),
    "encryption": SecurityControl(
        control_id="encryption",
        display_name="Encryption",
        category=ControlCategory.DATA,
        description="Data encryption at rest and in transit",
        supported_attack_types=("sql_injection", "malware", "phishing"),
        config_parameters={
            "algorithm": {"type": "str", "default": "AES-256-GCM", "description": "Encryption algorithm"},
            "tls_version": {"type": "str", "default": "1.3", "description": "TLS version for transit encryption"},
        },
    ),
    "siem": SecurityControl(
        control_id="siem",
        display_name="SIEM",
        category=ControlCategory.MONITORING,
        description="Security Information and Event Management",
        supported_attack_types=("ddos", "brute_force", "sql_injection", "suspicious_login", "malware", "phishing"),
        config_parameters={
            "retention_days": {"type": "int", "default": 90, "description": "Log retention period in days"},
            "correlation_rules": {"type": "int", "default": 200, "description": "Number of correlation rules"},
        },
    ),
    "runtime_monitoring": SecurityControl(
        control_id="runtime_monitoring",
        display_name="Runtime Monitoring",
        category=ControlCategory.MONITORING,
        description="Application runtime behavior monitoring",
        supported_attack_types=("malware", "sql_injection"),
        config_parameters={
            "sampling_rate": {"type": "float", "default": 1.0, "description": "Sampling rate (0.0 to 1.0)"},
            "anomaly_detection": {"type": "bool", "default": True, "description": "Enable anomaly detection"},
        },
    ),
    "logging": SecurityControl(
        control_id="logging",
        display_name="Logging",
        category=ControlCategory.MONITORING,
        description="Comprehensive audit and security logging",
        supported_attack_types=("phishing", "brute_force", "suspicious_login"),
        config_parameters={
            "log_level": {"type": "str", "default": "INFO", "description": "Logging level"},
            "structured_logging": {"type": "bool", "default": True, "description": "Enable structured JSON logging"},
        },
    ),
}


class SecurityControlError(Exception):
    pass


def get_supported_control_ids() -> list[str]:
    return list(SECURITY_CONTROLS.keys())


def validate_control_id(control_id: str) -> None:
    if control_id not in SECURITY_CONTROLS:
        raise SecurityControlError(
            f"Unknown security control: {control_id}. "
            f"Supported: {get_supported_control_ids()}"
        )


def get_control(control_id: str) -> SecurityControl:
    validate_control_id(control_id)
    return SECURITY_CONTROLS[control_id]


def list_controls() -> list[dict]:
    return [ctrl.to_dict() for ctrl in SECURITY_CONTROLS.values()]


def list_controls_by_category(category: ControlCategory) -> list[SecurityControl]:
    return [ctrl for ctrl in SECURITY_CONTROLS.values() if ctrl.category == category]


def get_controls_for_attack(attack_type: str) -> list[SecurityControl]:
    return [
        ctrl for ctrl in SECURITY_CONTROLS.values()
        if attack_type in ctrl.supported_attack_types
    ]


def get_attack_types_for_control(control_id: str) -> tuple[str, ...]:
    validate_control_id(control_id)
    return SECURITY_CONTROLS[control_id].supported_attack_types
