"""
Seed script for Carbon Guard demo database.
Generates realistic-looking but clearly synthetic data.
All data is labeled as simulated/demo data.
"""
import random
import uuid
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, SessionLocal
from app.models.security import SecurityEvent, Threat
from app.models.carbon import CarbonMetric, EnergyMetric
from app.models.workload import Workload, OptimizationResult
from app.models.ai import AIRecommendation
from app.models.system import SystemMetric
from app.models.settings import SystemSetting

ATTACK_TYPES = ["ddos", "brute_force", "port_scan", "sql_injection", "malware", "suspicious_login"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
STATUSES = ["detected", "investigating", "mitigated", "blocked", "false_positive"]
SOURCE_IPS = ["192.168.1.100", "192.168.1.101", "192.168.1.105", "10.0.0.50", "10.0.0.55", "172.16.0.25", "172.16.0.30"]
TARGET_IPS = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
DETECTION_METHODS = ["Rule-based detection", "ML anomaly detection", "Signature matching", "Behavioral analysis", "Heuristic analysis"]

EVENT_DESCRIPTIONS = {
    "ddos": "Distributed Denial of Service attack detected - abnormal traffic volume",
    "brute_force": "Brute force login attempt - multiple failed authentication attempts",
    "port_scan": "Port scanning activity detected - reconnaissance behavior",
    "sql_injection": "SQL injection attempt detected - malicious input patterns",
    "malware": "Malware activity detected - suspicious process behavior",
    "suspicious_login": "Suspicious login detected - unusual access pattern",
}

THREAT_EXPLANATIONS = {
    "ddos": "High request rate from concentrated sources with SYN flood characteristics.",
    "brute_force": "Rapid sequential login attempts targeting multiple accounts.",
    "port_scan": "Systematic port enumeration suggesting reconnaissance phase.",
    "sql_injection": "Malicious SQL patterns detected in HTTP request parameters.",
    "malware": "Known malware signatures identified in process execution.",
    "suspicious_login": "Login from unusual geographic location at atypical time.",
}

RECOMMENDATIONS = [
    {
        "type": "security",
        "recommendation": "Threat activity has increased 23% in the last 6 hours. Increase monitoring intensity on perimeter defenses.",
        "priority": "high",
        "reason": "Multiple DDoS and brute force attempts detected from similar source ranges.",
        "security_impact": "Improved detection rate and faster response time",
        "carbon_impact": "Temporary increase in monitoring workload energy",
        "confidence": 0.88,
    },
    {
        "type": "carbon",
        "recommendation": "Shift non-critical workloads to a lower-carbon period. Renewable energy availability is expected to increase in 2 hours.",
        "priority": "medium",
        "reason": "Current carbon intensity is above average. Low-carbon window predicted.",
        "security_impact": "No impact on security operations",
        "carbon_impact": "Estimated 18% reduction in workload emissions",
        "confidence": 0.82,
    },
    {
        "type": "energy",
        "recommendation": "Current workload has unusually high estimated energy consumption. Review resource allocation for log analysis tasks.",
        "priority": "medium",
        "reason": "Energy consumption 34% above baseline for current workload profile.",
        "security_impact": "Minimal - optimization preserves security functions",
        "carbon_impact": "Potential to save 0.4 kWh by optimizing log analysis scheduling",
        "confidence": 0.76,
    },
    {
        "type": "carbon",
        "recommendation": "Renewable energy availability is currently high at 45%. Schedule eligible security scans now.",
        "priority": "low",
        "reason": "Solar and wind availability optimal for next 3 hours.",
        "security_impact": "No impact on critical security tasks",
        "carbon_impact": "Carbon-efficient window for non-critical security operations",
        "confidence": 0.85,
    },
    {
        "type": "security",
        "recommendation": "Review firewall rules for detected source IP ranges. Multiple attack vectors observed.",
        "priority": "high",
        "reason": "Coordinated attack pattern from 192.168.1.x and 10.0.0.x ranges.",
        "security_impact": "Reduce attack surface and block known malicious sources",
        "carbon_impact": "Negligible energy impact from rule updates",
        "confidence": 0.91,
    },
    {
        "type": "general",
        "recommendation": "System operating within normal parameters. No immediate action required.",
        "priority": "low",
        "reason": "All metrics are within expected ranges.",
        "security_impact": "Continued normal operation",
        "carbon_impact": "Stable carbon footprint",
        "confidence": 0.90,
    },
]

WORKLOAD_TEMPLATES = [
    {"name": "Security Log Analysis", "type": "log_analysis", "priority": "medium", "critical": False, "cpu": 60, "mem": 256},
    {"name": "Real-time Traffic Monitor", "type": "traffic_monitor", "priority": "high", "critical": True, "cpu": 120, "mem": 512},
    {"name": "Vulnerability Scan", "type": "security_scan", "priority": "high", "critical": True, "cpu": 180, "mem": 1024},
    {"name": "Daily Backup", "type": "backup", "priority": "low", "critical": False, "cpu": 300, "mem": 128},
    {"name": "Report Generation", "type": "report_generation", "priority": "low", "critical": False, "cpu": 45, "mem": 256},
    {"name": "Patch Deployment", "type": "patch_deployment", "priority": "medium", "critical": False, "cpu": 90, "mem": 512},
    {"name": "IDS Signature Update", "type": "security_scan", "priority": "high", "critical": True, "cpu": 30, "mem": 128},
    {"name": "Compliance Audit Scan", "type": "security_scan", "priority": "medium", "critical": False, "cpu": 150, "mem": 512},
]


def seed_security_events(db, count=30):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    events = []
    for i in range(count):
        attack_type = random.choice(ATTACK_TYPES)
        severity = random.choice(SEVERITIES)
        hours_ago = random.uniform(0, 72)
        event = SecurityEvent(
            event_uuid=str(uuid.uuid4()),
            timestamp=now - timedelta(hours=hours_ago),
            event_type=attack_type,
            severity=severity,
            source_ip=random.choice(SOURCE_IPS),
            target_ip=random.choice(TARGET_IPS),
            target_port=random.randint(1, 65535),
            confidence=round(random.uniform(0.55, 0.98), 2),
            status=random.choice(STATUSES),
            detection_method=random.choice(DETECTION_METHODS),
            description=EVENT_DESCRIPTIONS.get(attack_type, "Security event detected"),
            risk_score=round(random.uniform(15, 95), 1),
            estimated_workload_cpu=round(random.uniform(5, 200), 1),
            estimated_energy_kwh=round(random.uniform(0.002, 0.1), 4),
            estimated_co2_kg=round(random.uniform(0.001, 0.05), 4),
        )
        events.append(event)
    db.add_all(events)
    db.commit()
    print(f"  Seeded {len(events)} security events")
    return events


def seed_threats(db, events, count=20):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    threats = []
    for i in range(min(count, len(events))):
        event = events[i]
        threat = Threat(
            threat_uuid=str(uuid.uuid4()),
            event_id=event.id,
            threat_type=event.event_type,
            severity=event.severity,
            confidence=event.confidence,
            risk_score=event.risk_score or 50.0,
            status=random.choice(["active", "active", "resolved"]),
            detected_at=event.timestamp,
            resolved_at=event.timestamp + timedelta(hours=random.randint(1, 24)) if random.random() > 0.6 else None,
            explanation=THREAT_EXPLANATIONS.get(event.event_type, "Threat detected through monitoring."),
            recommended_action=f"Investigate {event.event_type} from {event.source_ip}",
            anomaly_level=round(random.uniform(0.2, 0.9), 2),
        )
        threats.append(threat)
    db.add_all(threats)
    db.commit()
    print(f"  Seeded {len(threats)} threats")
    return threats


def seed_carbon_metrics(db, count=48):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = []
    for i in range(count):
        energy = round(random.uniform(1.5, 5.0), 2)
        carbon_intensity = round(random.uniform(350, 600), 1)
        renewable_pct = round(random.uniform(15, 55), 1)
        total_co2 = round(energy * carbon_intensity / 1000, 4)
        security_energy = round(energy * random.uniform(0.15, 0.35), 4)
        security_co2 = round(security_energy * carbon_intensity / 1000, 4)
        carbon_saved = round(total_co2 * random.uniform(0.05, 0.25), 4)

        metric = CarbonMetric(
            timestamp=now - timedelta(hours=(count - 1 - i)),
            total_energy_kwh=energy,
            total_co2_kg=total_co2,
            security_energy_kwh=security_energy,
            security_co2_kg=security_co2,
            carbon_saved_kg=carbon_saved,
            carbon_intensity=carbon_intensity,
            renewable_percentage=renewable_pct,
            workload_count=random.randint(3, 8),
            security_carbon_efficiency=round(random.uniform(55, 90), 1),
        )
        metrics.append(metric)
    db.add_all(metrics)
    db.commit()
    print(f"  Seeded {len(metrics)} carbon metrics")
    return metrics


def seed_energy_metrics(db, count=48):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = []
    for i in range(count):
        cpu = round(random.uniform(20, 80), 1)
        mem = round(random.uniform(10, 30), 1)
        net = round(random.uniform(5, 15), 1)
        total = round(cpu + mem + net + random.uniform(30, 60), 1)

        metric = EnergyMetric(
            timestamp=now - timedelta(hours=(count - 1 - i)),
            total_power_watts=total,
            cpu_power_watts=cpu,
            memory_power_watts=mem,
            network_power_watts=net,
            energy_kwh=round(total / 1000, 6),
            estimated=True,
        )
        metrics.append(metric)
    db.add_all(metrics)
    db.commit()
    print(f"  Seeded {len(metrics)} energy metrics")
    return metrics


def seed_workloads(db, count=8):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    workloads = []
    for i in range(min(count, len(WORKLOAD_TEMPLATES))):
        t = WORKLOAD_TEMPLATES[i]
        energy_kwh = round(t["cpu"] * 0.0001 + t["mem"] * 0.00001, 6)
        co2_kg = round(energy_kwh * 475 / 1000, 6)
        scheduled = now + timedelta(hours=random.randint(0, 6))

        workload = Workload(
            workload_uuid=str(uuid.uuid4()),
            name=t["name"],
            workload_type=t["type"],
            priority=t["priority"],
            is_security_critical=t["critical"],
            estimated_cpu_seconds=t["cpu"],
            estimated_memory_mb=t["mem"],
            estimated_energy_kwh=energy_kwh,
            estimated_co2_kg=co2_kg,
            status="scheduled",
            scheduled_time=scheduled,
            created_at=now,
        )
        workloads.append(workload)
    db.add_all(workloads)
    db.commit()
    print(f"  Seeded {len(workloads)} workloads")
    return workloads


def seed_recommendations(db, count=6):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    recs = []
    for i in range(min(count, len(RECOMMENDATIONS))):
        r = RECOMMENDATIONS[i]
        import json
        rec = AIRecommendation(
            timestamp=now - timedelta(hours=random.randint(0, 12)),
            recommendation_type=r["type"],
            recommendation=r["recommendation"],
            priority=r["priority"],
            reason=r["reason"],
            expected_security_impact=r.get("security_impact"),
            expected_carbon_impact=r.get("carbon_impact"),
            confidence=r["confidence"],
            factors_json=json.dumps([
                {"factor": "Analysis", "weight": 0.5, "value": "current_state"},
                {"factor": "Trend", "weight": 0.3, "value": "increasing"},
                {"factor": "Baseline", "weight": 0.2, "value": "normal"},
            ]),
            is_read=False,
            is_dismissed=False,
        )
        recs.append(rec)
    db.add_all(recs)
    db.commit()
    print(f"  Seeded {len(recs)} AI recommendations")
    return recs


def seed_system_metrics(db, count=24):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = []
    for i in range(count):
        metric = SystemMetric(
            timestamp=now - timedelta(hours=(count - 1 - i)),
            cpu_utilization=round(random.uniform(20, 70), 1),
            memory_utilization=round(random.uniform(30, 75), 1),
            active_workloads=random.randint(2, 6),
            security_engine_status="online",
            carbon_engine_status="online",
            ai_engine_status="online",
            database_status="online",
            api_status="online",
            simulated=True,
        )
        metrics.append(metric)
    db.add_all(metrics)
    db.commit()
    print(f"  Seeded {len(metrics)} system metrics")
    return metrics


def seed_settings(db):
    settings_data = [
        {"key": "carbon_intensity", "value": "475", "category": "carbon", "description": "Grid carbon intensity in gCO2/kWh"},
        {"key": "renewable_percentage", "value": "25", "category": "carbon", "description": "Default renewable energy percentage"},
        {"key": "max_delay_hours", "value": "4", "category": "optimizer", "description": "Maximum hours to delay non-critical workloads"},
        {"key": "minimum_savings_threshold", "value": "0.01", "category": "optimizer", "description": "Minimum CO2 savings to justify workload shifting"},
    ]
    added = 0
    for s in settings_data:
        existing = db.query(SystemSetting).filter(SystemSetting.key == s["key"]).first()
        if not existing:
            setting = SystemSetting(**s)
            db.add(setting)
            added += 1
    db.commit()
    print(f"  Seeded {added} system settings")


def main():
    print("=" * 60)
    print("Carbon Guard - Database Seed Script")
    print("ALL DATA IS SIMULATED/DEMO DATA")
    print("=" * 60)

    print("\nInitializing database...")
    init_db()

    db = SessionLocal()
    try:
        print("\nSeeding data...")
        seed_security_events(db)
        seed_threats(db, db.query(SecurityEvent).all())
        seed_carbon_metrics(db)
        seed_energy_metrics(db)
        seed_workloads(db)
        seed_recommendations(db)
        seed_system_metrics(db)
        seed_settings(db)

        print("\n" + "=" * 60)
        print("Seed completed successfully!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  Security Events: {db.query(SecurityEvent).count()}")
        print(f"  Threats: {db.query(Threat).count()}")
        print(f"  Carbon Metrics: {db.query(CarbonMetric).count()}")
        print(f"  Energy Metrics: {db.query(EnergyMetric).count()}")
        print(f"  Workloads: {db.query(Workload).count()}")
        print(f"  AI Recommendations: {db.query(AIRecommendation).count()}")
        print(f"  System Metrics: {db.query(SystemMetric).count()}")
        print(f"  System Settings: {db.query(SystemSetting).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
