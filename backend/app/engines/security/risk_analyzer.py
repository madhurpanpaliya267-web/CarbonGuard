import random
from typing import List


SEVERITY_WEIGHTS = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.5,
    "LOW": 0.25,
}


def analyze_risk(
    severity: str,
    confidence: float,
    frequency: int = 1,
    anomaly_level: float = 0.5,
    resource_impact: float = 0.5,
) -> dict:
    severity_weight = 0.30
    confidence_weight = 0.20
    frequency_weight = 0.20
    anomaly_weight = 0.15
    impact_weight = 0.15

    severity_normalized = SEVERITY_WEIGHTS.get(severity, 0.5)
    frequency_factor = min(1.0, frequency / 10)

    risk_score = (
        severity_weight * severity_normalized +
        confidence_weight * confidence +
        frequency_weight * frequency_factor +
        anomaly_weight * anomaly_level +
        impact_weight * resource_impact
    ) * 100

    risk_score = max(0, min(100, risk_score))

    factors = [
        {
            "factor": "Attack Severity",
            "weight": severity_weight,
            "value": severity,
            "contribution": round(severity_weight * severity_normalized * 100, 1),
            "description": f"Severity level: {severity}",
        },
        {
            "factor": "Detection Confidence",
            "weight": confidence_weight,
            "value": confidence,
            "contribution": round(confidence_weight * confidence * 100, 1),
            "description": f"Confidence: {confidence * 100:.0f}%",
        },
        {
            "factor": "Event Frequency",
            "weight": frequency_weight,
            "value": frequency,
            "contribution": round(frequency_weight * frequency_factor * 100, 1),
            "description": f"{frequency} similar events detected",
        },
        {
            "factor": "Anomaly Level",
            "weight": anomaly_weight,
            "value": anomaly_level,
            "contribution": round(anomaly_weight * anomaly_level * 100, 1),
            "description": f"Anomaly score: {anomaly_level:.2f}",
        },
        {
            "factor": "Resource Impact",
            "weight": impact_weight,
            "value": resource_impact,
            "contribution": round(impact_weight * resource_impact * 100, 1),
            "description": f"Estimated impact: {resource_impact:.2f}",
        },
    ]

    if risk_score >= 80:
        risk_severity = "CRITICAL"
    elif risk_score >= 60:
        risk_severity = "HIGH"
    elif risk_score >= 40:
        risk_severity = "MEDIUM"
    else:
        risk_severity = "LOW"

    return {
        "risk_score": round(risk_score, 1),
        "severity": risk_severity,
        "confidence": round(confidence, 2),
        "factors": factors,
    }
