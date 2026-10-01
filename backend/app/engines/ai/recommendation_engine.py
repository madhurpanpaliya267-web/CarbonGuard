from typing import List
from datetime import datetime


def generate_recommendations(
    active_threats: int,
    energy_kwh: float,
    co2_kg: float,
    renewable_pct: float,
    carbon_intensity: float,
    workload_count: int,
    recent_events_count: int = 0,
) -> List[dict]:
    recommendations = []

    if active_threats > 3:
        recommendations.append({
            "recommendation_type": "security",
            "recommendation": "Threat activity has increased significantly. Increase monitoring intensity and review firewall rules.",
            "priority": "high",
            "reason": f"{active_threats} active threats detected, exceeding normal threshold.",
            "expected_security_impact": "Improved threat detection and response time",
            "expected_carbon_impact": "Temporary increase in monitoring workload energy",
            "confidence": 0.85,
            "factors": [
                {"factor": "Active threat count", "value": active_threats, "weight": 0.4},
                {"factor": "Recent event rate", "value": recent_events_count, "weight": 0.3},
                {"factor": "Historical baseline", "value": "above average", "weight": 0.3},
            ],
        })

    if energy_kwh > 5.0:
        recommendations.append({
            "recommendation_type": "energy",
            "recommendation": "Current workload has unusually high estimated energy consumption. Review and optimize resource allocation.",
            "priority": "medium",
            "reason": f"Energy consumption ({energy_kwh:.2f} kWh) exceeds typical operating levels.",
            "expected_security_impact": "Minimal - optimization preserves security functions",
            "expected_carbon_impact": f"Potential to reduce energy by {energy_kwh * 0.15:.2f} kWh",
            "confidence": 0.78,
            "factors": [
                {"factor": "Current energy", "value": energy_kwh, "weight": 0.5},
                {"factor": "Baseline comparison", "value": "above average", "weight": 0.3},
                {"factor": "Workload count", "value": workload_count, "weight": 0.2},
            ],
        })

    if renewable_pct > 60:
        recommendations.append({
            "recommendation_type": "carbon",
            "recommendation": "Renewable energy availability is currently high. Schedule eligible non-critical workloads now.",
            "priority": "medium",
            "reason": f"Renewable energy at {renewable_pct:.0f}% - excellent window for carbon-efficient operations.",
            "expected_security_impact": "No impact on security operations",
            "expected_carbon_impact": "Significant carbon reduction by shifting workloads to renewable-heavy period",
            "confidence": 0.82,
            "factors": [
                {"factor": "Renewable percentage", "value": renewable_pct, "weight": 0.5},
                {"factor": "Carbon intensity", "value": carbon_intensity, "weight": 0.3},
                {"factor": "Workload eligibility", "value": workload_count, "weight": 0.2},
            ],
        })

    if co2_kg > 1.0:
        recommendations.append({
            "recommendation_type": "carbon",
            "recommendation": "Estimated CO2 emissions are elevated. Consider carbon-aware scheduling for non-critical tasks.",
            "priority": "medium",
            "reason": f"Current CO2 estimate ({co2_kg:.2f} kg) is above optimal levels.",
            "expected_security_impact": "No impact on critical security tasks",
            "expected_carbon_impact": f"Potential to reduce emissions by {co2_kg * 0.2:.2f} kg CO2",
            "confidence": 0.75,
            "factors": [
                {"factor": "Current CO2", "value": co2_kg, "weight": 0.4},
                {"factor": "Carbon intensity", "value": carbon_intensity, "weight": 0.3},
                {"factor": "Renewable offset", "value": renewable_pct, "weight": 0.3},
            ],
        })

    if active_threats > 0 and renewable_pct < 30:
        recommendations.append({
            "recommendation_type": "workload",
            "recommendation": "High threat activity with low renewable availability. Prioritize security workloads and defer non-critical tasks.",
            "priority": "high",
            "reason": "Security-critical operations need immediate resources during elevated threat levels.",
            "expected_security_impact": "Ensures adequate resources for threat response",
            "expected_carbon_impact": "Non-critical deferral reduces unnecessary emissions",
            "confidence": 0.88,
            "factors": [
                {"factor": "Active threats", "value": active_threats, "weight": 0.4},
                {"factor": "Renewable availability", "value": renewable_pct, "weight": 0.3},
                {"factor": "Carbon intensity", "value": carbon_intensity, "weight": 0.3},
            ],
        })

    if not recommendations:
        recommendations.append({
            "recommendation_type": "general",
            "recommendation": "System operating within normal parameters. No immediate action required.",
            "priority": "low",
            "reason": "All metrics are within expected ranges.",
            "expected_security_impact": "Continued normal operation",
            "expected_carbon_impact": "Stable carbon footprint",
            "confidence": 0.90,
            "factors": [
                {"factor": "System status", "value": "normal", "weight": 1.0},
            ],
        })

    return recommendations
