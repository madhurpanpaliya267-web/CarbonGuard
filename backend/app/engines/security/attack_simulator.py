import random
import uuid
from datetime import datetime, timezone
from app.engines.security.threat_detector import (
    detect_event,
    generate_event_uuid,
    ATTACK_PROFILES,
    SIMULATED_IPS,
    TARGET_IPS,
)
from app.engines.security.risk_analyzer import analyze_risk
from app.engines.carbon.carbon_calculator import calculate_carbon
from app.engines.security.attack_profiles import (
    AttackIntensity,
    build_attack_profile,
    validate_attack_type,
    validate_intensity,
    AttackProfileError,
)


def simulate_attack(attack_type: str, intensity: str = None, duration_seconds: int = None) -> dict:
    if attack_type not in ATTACK_PROFILES:
        raise ValueError(f"Unknown attack type: {attack_type}. Supported: {list(ATTACK_PROFILES.keys())}")

    profile = ATTACK_PROFILES[attack_type]
    source_ip = random.choice(SIMULATED_IPS)
    target_ip = random.choice(TARGET_IPS)

    detection = detect_event({"attack_type": attack_type})

    risk = analyze_risk(
        severity=detection["severity"],
        confidence=detection["confidence"],
        frequency=random.randint(1, 5),
        anomaly_level=random.uniform(0.3, 0.9),
        resource_impact=random.uniform(0.2, 0.8),
    )

    cpu_seconds = detection["estimated_cpu_seconds"]
    energy_kwh = detection["estimated_energy_kwh"]
    carbon_result = calculate_carbon(energy_kwh)
    carbon_intensity = carbon_result["carbon_intensity"]
    co2_kg = carbon_result["gross_co2_kg"]

    recommendation = _generate_recommendation(attack_type, risk)

    research_profile = None
    if intensity is not None:
        try:
            research_profile = build_attack_profile(
                attack_type=attack_type,
                intensity=intensity,
                duration_seconds=duration_seconds,
            )
        except AttackProfileError:
            pass

    pipeline = [
        {"step": "Attack Simulation", "status": "completed", "detail": f"Simulated {attack_type} attack"},
        {"step": "Threat Detection", "status": "completed", "detail": f"Classified as {detection['threat_type']}"},
        {"step": "Threat Classification", "status": "completed", "detail": f"Severity: {detection['severity']}"},
        {"step": "Risk Score", "status": "completed", "detail": f"Risk: {risk['risk_score']}/100"},
        {"step": "Security Response", "status": "completed", "detail": "Event logged and analyzed"},
        {"step": "Computational Workload", "status": "completed", "detail": f"Est. CPU: {cpu_seconds}s"},
        {"step": "Energy Estimate", "status": "completed", "detail": f"Est. Energy: {energy_kwh} kWh"},
        {"step": "Carbon Impact", "status": "completed", "detail": f"Est. CO2: {co2_kg:.4f} kg"},
        {"step": "AI Recommendation", "status": "completed", "detail": recommendation["recommendation"][:80]},
    ]

    result = {
        "event": {
            "event_uuid": generate_event_uuid(),
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "event_type": attack_type,
            "severity": detection["severity"],
            "source_ip": source_ip,
            "target_ip": target_ip,
            "target_port": random.randint(1, 65535),
            "confidence": detection["confidence"],
            "status": "detected",
            "detection_method": detection["detection_method"],
            "description": detection["description"],
            "risk_score": risk["risk_score"],
            "estimated_workload_cpu": cpu_seconds,
            "estimated_energy_kwh": energy_kwh,
            "estimated_co2_kg": co2_kg,
        },
        "threat": {
            "threat_uuid": str(uuid.uuid4()),
            "threat_type": detection["threat_type"],
            "severity": detection["severity"],
            "confidence": detection["confidence"],
            "risk_score": risk["risk_score"],
            "status": "active",
            "detected_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "explanation": _generate_explanation(attack_type, detection, risk),
            "recommended_action": recommendation["recommendation"],
            "anomaly_level": risk["factors"][3]["value"],
        },
        "risk_assessment": risk,
        "workload_impact": {
            "cpu_seconds": cpu_seconds,
            "memory_mb": random.uniform(128, 512),
            "estimated_duration_seconds": cpu_seconds * 1.5,
        },
        "energy_impact": {
            "energy_kwh": energy_kwh,
            "power_watts": energy_kwh * 3600 / max(cpu_seconds, 1),
            "estimated": True,
        },
        "carbon_impact": {
            "co2_kg": co2_kg,
            "carbon_intensity": carbon_intensity,
            "renewable_offset_kg": carbon_result["renewable_offset_kg"],
            "net_co2_kg": carbon_result["net_co2_kg"],
            "estimated": True,
            "simulated": True,
            "calculation_breakdown": carbon_result["calculation_breakdown"],
        },
        "ai_recommendation": recommendation,
        "pipeline": pipeline,
    }

    if research_profile is not None:
        result["research_profile"] = research_profile.to_dict()

    return result


def _generate_recommendation(attack_type: str, risk: dict) -> dict:
    recommendations = {
        "ddos": {
            "recommendation": "Activate rate limiting and engage upstream filtering immediately.",
            "priority": "high",
            "expected_security_impact": "Mitigate DDoS traffic and protect target services",
            "expected_carbon_impact": "Increased monitoring workload may increase energy use temporarily",
        },
        "brute_force": {
            "recommendation": "Implement account lockout and enable CAPTCHA verification.",
            "priority": "medium",
            "expected_security_impact": "Prevent unauthorized access attempts",
            "expected_carbon_impact": "Minimal additional energy impact",
        },
        "port_scan": {
            "recommendation": "Review firewall rules and monitor for follow-up exploitation attempts.",
            "priority": "low",
            "expected_security_impact": "Detect potential reconnaissance activity",
            "expected_carbon_impact": "Negligible energy impact",
        },
        "sql_injection": {
            "recommendation": "Activate WAF rules and review database access patterns.",
            "priority": "high",
            "expected_security_impact": "Prevent data exfiltration and database compromise",
            "expected_carbon_impact": "Moderate increase in monitoring workload",
        },
        "malware": {
            "recommendation": "Isolate affected systems and initiate full security scan.",
            "priority": "critical",
            "expected_security_impact": "Contain malware spread and prevent data loss",
            "expected_carbon_impact": "Significant increase in computational workload for scanning",
        },
        "suspicious_login": {
            "recommendation": "Verify user identity and review recent access patterns.",
            "priority": "medium",
            "expected_security_impact": "Prevent potential account compromise",
            "expected_carbon_impact": "Minimal energy impact",
        },
        "phishing": {
            "recommendation": "Block malicious URLs and alert users about phishing attempt.",
            "priority": "high",
            "expected_security_impact": "Prevent credential theft and malware delivery",
            "expected_carbon_impact": "Minimal energy impact",
        },
    }

    rec = recommendations.get(attack_type, {
        "recommendation": "Investigate the security event and assess impact.",
        "priority": "medium",
        "expected_security_impact": "Improved threat awareness",
        "expected_carbon_impact": "Minimal",
    })

    return {
        "recommendation": rec["recommendation"],
        "priority": rec["priority"],
        "reason": f"Detected {attack_type} with risk score {risk['risk_score']}/100",
        "expected_security_impact": rec["expected_security_impact"],
        "expected_carbon_impact": rec["expected_carbon_impact"],
        "confidence": risk["confidence"],
        "factors": risk["factors"],
    }


def _generate_explanation(attack_type: str, detection: dict, risk: dict) -> str:
    factors = risk["factors"]
    top_factors = sorted(factors, key=lambda x: x["contribution"], reverse=True)[:3]
    factor_str = ", ".join([f["factor"] for f in top_factors])

    return (
        f"Prediction: {attack_type.upper()} attack detected. "
        f"Confidence: {detection['confidence'] * 100:.0f}%. "
        f"Important factors: {factor_str}. "
        f"Risk score: {risk['risk_score']}/100."
    )
