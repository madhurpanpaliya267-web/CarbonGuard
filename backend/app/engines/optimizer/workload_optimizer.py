import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from app.config import settings


PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def generate_sample_workloads(count: int = 8) -> List[dict]:
    workload_templates = [
        {"name": "Security Log Analysis", "type": "log_analysis", "priority": "medium", "critical": False, "cpu": 60, "mem": 256},
        {"name": "Real-time Traffic Monitor", "type": "traffic_monitor", "priority": "high", "critical": True, "cpu": 120, "mem": 512},
        {"name": "Vulnerability Scan", "type": "security_scan", "priority": "high", "critical": True, "cpu": 180, "mem": 1024},
        {"name": "Daily Backup", "type": "backup", "priority": "low", "critical": False, "cpu": 300, "mem": 128},
        {"name": "Report Generation", "type": "report_generation", "priority": "low", "critical": False, "cpu": 45, "mem": 256},
        {"name": "Patch Deployment", "type": "patch_deployment", "priority": "medium", "critical": False, "cpu": 90, "mem": 512},
        {"name": "IDS Signature Update", "type": "security_scan", "priority": "high", "critical": True, "cpu": 30, "mem": 128},
        {"name": "Compliance Audit Scan", "type": "security_scan", "priority": "medium", "critical": False, "cpu": 150, "mem": 512},
    ]

    workloads = []
    now = _utcnow()

    for i in range(min(count, len(workload_templates))):
        t = workload_templates[i]
        energy_kwh = t["cpu"] * 0.0001 + t["mem"] * 0.00001
        co2_kg = energy_kwh * settings.DEFAULT_CARBON_INTENSITY / 1000
        scheduled = now + timedelta(hours=random.randint(0, 6))

        workloads.append({
            "workload_uuid": str(uuid.uuid4()),
            "name": t["name"],
            "workload_type": t["type"],
            "priority": t["priority"],
            "is_security_critical": t["critical"],
            "estimated_cpu_seconds": t["cpu"],
            "estimated_memory_mb": t["mem"],
            "estimated_energy_kwh": round(energy_kwh, 6),
            "estimated_co2_kg": round(co2_kg, 6),
            "status": "scheduled",
            "scheduled_time": scheduled,
            "optimized_time": None,
            "carbon_intensity_at_exec": None,
            "created_at": now,
        })

    return workloads


def optimize_workloads(workloads: List[dict], current_carbon_intensity: float = None) -> dict:
    if current_carbon_intensity is None:
        current_carbon_intensity = settings.DEFAULT_CARBON_INTENSITY

    critical = [w for w in workloads if w.get("is_security_critical", False)]
    non_critical = [w for w in workloads if not w.get("is_security_critical", False)]

    energy_before = sum(w.get("estimated_energy_kwh", 0) for w in workloads)
    co2_before = sum(w.get("estimated_co2_kg", 0) for w in workloads)

    for w in critical:
        w["optimized_time"] = w.get("scheduled_time")
        w["status"] = "scheduled"

    non_critical_sorted = sorted(non_critical, key=lambda w: PRIORITY_ORDER.get(w.get("priority", "medium"), 2))

    workloads_shifted = 0
    workloads_unchanged = 0
    details = []

    for w in non_critical_sorted:
        should_shift = random.random() > 0.4
        if should_shift:
            original_time = w["scheduled_time"] if isinstance(w["scheduled_time"], datetime) else datetime.fromisoformat(w["scheduled_time"])
            delay_hours = random.randint(1, settings.MAX_DELAY_HOURS)
            optimized_time = original_time + timedelta(hours=delay_hours)
            low_carbon_intensity = current_carbon_intensity * random.uniform(0.5, 0.8)

            w["optimized_time"] = optimized_time
            w["status"] = "delayed"
            w["carbon_intensity_at_exec"] = low_carbon_intensity
            workloads_shifted += 1

            new_co2 = w["estimated_energy_kwh"] * low_carbon_intensity / 1000
            co2_saved = w["estimated_co2_kg"] - new_co2

            details.append({
                "workload_uuid": w["workload_uuid"],
                "name": w["name"],
                "action": "shifted",
                "original_time": w["scheduled_time"],
                "optimized_time": w["optimized_time"],
                "delay_hours": delay_hours,
                "carbon_intensity_before": current_carbon_intensity,
                "carbon_intensity_after": low_carbon_intensity,
                "co2_saved_kg": round(max(0, co2_saved), 6),
            })
        else:
            w["optimized_time"] = w.get("scheduled_time")
            w["status"] = "scheduled"
            workloads_unchanged += 1

            details.append({
                "workload_uuid": w["workload_uuid"],
                "name": w["name"],
                "action": "unchanged",
                "reason": "No suitable low-carbon window found or savings below threshold",
            })

    energy_after = sum(w.get("estimated_energy_kwh", 0) for w in workloads)
    co2_after = 0
    for w in workloads:
        intensity = w.get("carbon_intensity_at_exec") or current_carbon_intensity
        co2_after += w["estimated_energy_kwh"] * intensity / 1000

    energy_saved = max(0, energy_before - energy_after)
    co2_saved = max(0, co2_before - co2_after)
    reduction_pct = (co2_saved / max(co2_before, 0.0001)) * 100

    return {
        "workloads_analyzed": len(workloads),
        "workloads_shifted": workloads_shifted,
        "workloads_unchanged": workloads_unchanged,
        "critical_protected": len(critical),
        "energy_before_kwh": round(energy_before, 6),
        "energy_after_kwh": round(energy_after, 6),
        "co2_before_kg": round(co2_before, 6),
        "co2_after_kg": round(co2_after, 6),
        "energy_saved_kwh": round(energy_saved, 6),
        "co2_saved_kg": round(co2_saved, 6),
        "reduction_percentage": round(reduction_pct, 1),
        "details": details,
    }
