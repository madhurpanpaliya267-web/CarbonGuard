import uuid
from datetime import datetime


ATTACK_PROFILES = {
    "ddos": {
        "base_severity": "HIGH",
        "confidence_range": (0.75, 0.95),
        "description": "Distributed Denial of Service attack detected",
        "detection_method": "Traffic anomaly detection",
        "cpu_range": (30, 120),
        "energy_range": (0.01, 0.05),
    },
    "brute_force": {
        "base_severity": "MEDIUM",
        "confidence_range": (0.70, 0.90),
        "description": "Brute force login attempt detected",
        "detection_method": "Authentication pattern analysis",
        "cpu_range": (10, 40),
        "energy_range": (0.005, 0.02),
    },
    "port_scan": {
        "base_severity": "LOW",
        "confidence_range": (0.60, 0.85),
        "description": "Port scanning activity detected",
        "detection_method": "Network traffic monitoring",
        "cpu_range": (5, 15),
        "energy_range": (0.002, 0.008),
    },
    "sql_injection": {
        "base_severity": "HIGH",
        "confidence_range": (0.80, 0.95),
        "description": "SQL injection attempt detected",
        "detection_method": "Input pattern matching",
        "cpu_range": (15, 50),
        "energy_range": (0.008, 0.025),
    },
    "malware": {
        "base_severity": "CRITICAL",
        "confidence_range": (0.85, 0.98),
        "description": "Malware activity detected",
        "detection_method": "Signature-based detection",
        "cpu_range": (50, 200),
        "energy_range": (0.025, 0.1),
    },
    "suspicious_login": {
        "base_severity": "MEDIUM",
        "confidence_range": (0.65, 0.88),
        "description": "Suspicious login activity detected",
        "detection_method": "Behavioral analysis",
        "cpu_range": (5, 20),
        "energy_range": (0.002, 0.01),
    },
    "phishing": {
        "base_severity": "MEDIUM",
        "confidence_range": (0.70, 0.92),
        "description": "Phishing-like activity detected",
        "detection_method": "Content and URL analysis",
        "cpu_range": (5, 25),
        "energy_range": (0.003, 0.015),
    },
}

SIMULATED_IPS = [
    "192.168.1.100", "192.168.1.101", "192.168.1.102",
    "10.0.0.50", "10.0.0.51", "172.16.0.25",
]

TARGET_IPS = [
    "10.0.0.1", "10.0.0.2", "10.0.0.3",
]


def _random_in_range(range_tuple: tuple) -> float:
    import random
    return random.uniform(range_tuple[0], range_tuple[1])


def classify_severity(attack_type: str, base_severity: str) -> str:
    severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    base_idx = severity_order.index(base_severity)
    import random
    jitter = random.choice([-1, 0, 0, 1])
    idx = max(0, min(3, base_idx + jitter))
    return severity_order[idx]


def detect_event(event_data: dict) -> dict:
    attack_type = event_data.get("attack_type", "unknown")
    profile = ATTACK_PROFILES.get(attack_type)

    if not profile:
        return {
            "threat_type": "unknown",
            "confidence": 0.5,
            "severity": "MEDIUM",
            "risk_score": 50.0,
            "detection_method": "Unknown",
            "description": "Unknown attack type detected",
        }

    confidence = _random_in_range(profile["confidence_range"])
    severity = classify_severity(attack_type, profile["base_severity"])

    return {
        "threat_type": attack_type,
        "confidence": round(confidence, 2),
        "severity": severity,
        "detection_method": profile["detection_method"],
        "description": profile["description"],
        "estimated_cpu_seconds": round(_random_in_range(profile["cpu_range"]), 1),
        "estimated_energy_kwh": round(_random_in_range(profile["energy_range"]), 4),
    }


def generate_event_uuid() -> str:
    return str(uuid.uuid4())
