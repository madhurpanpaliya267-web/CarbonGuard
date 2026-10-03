"""
CarbonGuard end-to-end pipeline orchestration.

Connects the EXISTING subsystems into one lifecycle run without duplicating
any underlying calculation:

    AttackSimulation   -> engines.security.attack_simulator.simulate_attack
    ThreatDetection    -> engines.security.threat_detector (via simulate)
    ThreatAssessment   -> engines.security.risk_analyzer (via simulate)
    AdaptiveDefense    -> engines.security.security_controls.select_controls_for_threat
    EnergyImpact       -> engines.energy.factory provider (Phase 5/6/7 abstraction)
    CarbonImpact       -> engines.carbon.carbon_calculator.calculate_carbon
    ResearchObservation-> services.research_service (Phase 11 storage)
    Analytics          -> existing persisted feeds (/research/summary, /security/stats)

Research integrity rules:
- Attack data is SYNTHETIC/SIMULATED and always labelled as such.
- Energy values carry their measurement mode (ESTIMATED / MEASURED / SIMULATED).
- Carbon is always derived from an energy value plus a carbon-intensity source
  and carries an explicit carbon basis; it is never presented as measured.
- Control selection is rule-based, never claimed to be optimal.
- Failures in optional stages degrade gracefully with explicit status/reason
  fields instead of failing the whole run.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.engines.carbon.carbon_calculator import calculate_carbon, carbon_basis_label
from app.engines.energy.factory import get_provider
from app.engines.security.attack_profiles import (
    AttackProfileError,
    build_attack_profile,
    validate_attack_type,
    validate_intensity,
)
from app.engines.security.attack_simulator import simulate_attack
from app.engines.security.security_controls import select_controls_for_threat
from app.services.research_service import ExperimentError, ResearchExperimentService
from app.services.security_service import SecurityService

PIPELINE_VERSION = "13.0.0"
DEFAULT_DURATION_SECONDS = 60


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def _row_to_dict(row):
    """Serialise a persisted ORM row (or pass a dict through unchanged)."""
    if isinstance(row, dict):
        return row
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class CarbonGuardOrchestrationService:
    """Runs the complete CarbonGuard lifecycle for one synthetic attack."""

    def __init__(self, db: Optional[Session]):
        self.db = db

    def run(
        self,
        attack_type: str,
        intensity: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        measurement_provider: str = "estimated",
        record_research: bool = False,
        experiment_uuid: Optional[str] = None,
        carbon_intensity: Optional[float] = None,
        renewable_percentage: Optional[float] = None,
    ) -> dict:
        warnings: list[dict] = []

        # --- validation (invalid input raises -> API maps to 400) ---
        validate_attack_type(attack_type)
        try:
            get_provider(measurement_provider)  # ValueError on unknown provider
        except ValueError:
            raise
        except Exception:
            pass  # availability is checked again at measurement time
        profile = None
        if intensity is not None:
            validate_intensity(intensity)
            profile = build_attack_profile(
                attack_type=attack_type,
                intensity=intensity,
                duration_seconds=duration_seconds,
            )

        duration = duration_seconds or (
            profile.duration_seconds if profile else DEFAULT_DURATION_SECONDS
        )

        # --- Attack simulation + detection + classification + risk ---
        sim = simulate_attack(
            attack_type,
            intensity=intensity,
            duration_seconds=duration_seconds,
        )

        # --- persistence (events/threats feed dashboard + security stats) ---
        try:
            persisted = SecurityService(self.db).persist_simulation(sim)
            event = _row_to_dict(persisted["event"])
            threat = _row_to_dict(persisted["threat"])
            if event.get("id") is None or threat.get("id") is None:
                raise RuntimeError("persisted rows are missing ids")
            persist_warning = None
        except Exception as exc:  # persistence must not kill the pipeline
            event = sim["event"]
            threat = sim["threat"]
            persist_warning = {
                "stage": "Persistence",
                "reason": f"Event/threat persistence failed: {exc}",
            }
            warnings.append(persist_warning)

        detection = sim["threat"]
        risk = sim["risk_assessment"]
        severity = detection["severity"]

        # --- Adaptive defense: rule-based control selection ---
        defense = select_controls_for_threat(
            attack_type=attack_type,
            severity=severity,
            risk_score=risk.get("risk_score"),
        )
        control_ids = defense["selected"]
        recommendation = sim["ai_recommendation"]
        defense["response"] = recommendation["recommendation"]
        defense["recommendation"] = recommendation
        defense["activated"] = bool(control_ids)

        # --- Energy impact via the existing provider abstraction ---
        energy = self._measure_energy(
            provider_name=measurement_provider,
            duration=duration,
            control_count=len(control_ids),
            intensity=intensity,
            warnings=warnings,
        )

        # --- Carbon impact via the existing calculator ---
        carbon = self._calculate_carbon(
            energy=energy,
            carbon_intensity=carbon_intensity,
            renewable_percentage=renewable_percentage,
            warnings=warnings,
        )

        # --- Baseline vs defense comparison (only when both sides measured) ---
        comparison = self._compare_baseline_to_defense(
            provider_name=measurement_provider,
            duration=duration,
            control_count=len(control_ids),
            intensity=intensity,
            energy=energy,
            carbon=carbon,
            warnings=warnings,
        )

        # --- Research observation (Phase 11 storage, optional) ---
        research = self._record_research(
            record_research=record_research,
            experiment_uuid=experiment_uuid,
            attack_type=attack_type,
            intensity=intensity,
            profile=profile,
            control_ids=control_ids,
            energy=energy,
            carbon=carbon,
            severity=severity,
            response=defense["response"],
            risk_score=risk.get("risk_score"),
            warnings=warnings,
        )

        stages = self._build_stages(sim, defense, energy, carbon, research)

        analytics = {
            "status": "completed" if persist_warning is None else "partial",
            "recorded": research.get("status") == "recorded",
            "feeds": self._analytics_feeds(persist_warning, research),
            "detail": (
                "Persisted events/threats aggregate through /api/v1/security/stats, "
                "/api/v1/threats/stats and /api/v1/dashboard; research observations "
                "aggregate through /api/v1/research/summary and /api/v1/research/metrics."
            ),
        }

        provenance = {
            "data_classification": "SYNTHETIC",
            "simulated_attack": True,
            "measurement_mode": energy.get("measurement_mode"),
            "measurement_source": energy.get("measurement_source"),
            "carbon_basis": carbon.get("carbon_basis"),
            "energy_engine": f"energy_provider:{energy.get('provider') or measurement_provider}",
            "carbon_engine": "calculate_carbon",
            "control_selection": "rule_based",
            "pipeline_version": PIPELINE_VERSION,
            "generated_at": _now_iso(),
            "notes": (
                "Synthetic attack data; energy is ESTIMATED unless a hardware "
                "provider reports MEASURED; carbon is calculated from energy x "
                "carbon intensity and is never hardware-measured."
            ),
        }

        status = "completed"
        if energy["status"] != "completed" or carbon["status"] != "completed":
            status = "partial"
        if research.get("status") == "failed":
            status = "partial"
        if persist_warning is not None:
            status = "partial"

        attack_section = {
            "attack_type": attack_type,
            "intensity": intensity or (profile.intensity.value if profile else None),
            "duration_seconds": duration,
            "description": sim["event"].get("description"),
            "detection_method": sim["event"].get("detection_method"),
            "detection_confidence": sim["event"].get("confidence"),
            "detection_estimate": {
                "energy_kwh": sim["energy_impact"].get("energy_kwh"),
                "co2_kg": sim["carbon_impact"].get("co2_kg"),
                "source": "threat_detector_profile",
                "note": "Detection-stage estimate; defense energy below comes from the provider abstraction.",
            },
            "workload": sim["workload_impact"],
            "attack_profile": profile.to_dict() if profile else None,
            "synthetic": True,
        }

        return {
            "status": status,
            "event": event,
            "attack": attack_section,
            "threat": threat,
            "risk": risk,
            "defense": defense,
            "security_controls": control_ids,
            "energy": energy,
            "carbon": carbon,
            "comparison": comparison,
            "research": research,
            "analytics": analytics,
            "provenance": provenance,
            "stages": stages,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # stage helpers
    # ------------------------------------------------------------------

    def _measure_energy(
        self,
        provider_name: str,
        duration: float,
        control_count: int,
        intensity: Optional[str],
        warnings: list[dict],
    ) -> dict:
        try:
            provider = get_provider(provider_name)
            if not provider.is_available():
                raise RuntimeError(
                    f"Energy provider '{provider_name}' reports unavailable"
                )
            reading = provider.get_measurement(
                duration_seconds=duration,
                workload_count=1,
                security_controls_active=control_count,
                attack_intensity=intensity,
            )
            return {
                "status": "completed",
                "energy_joules": reading.energy_joules,
                "energy_kwh": round(reading.energy_kwh, 8),
                "power_watts": reading.power_watts,
                "duration_seconds": reading.duration_seconds,
                "measurement_mode": reading.mode.value,
                "measurement_source": reading.source,
                "provider": provider_name,
                "security_controls_active": control_count,
                "estimated": reading.mode.value == "ESTIMATED",
                "reason": None,
            }
        except Exception as exc:
            reason = f"Energy measurement unavailable: {exc}"
            warnings.append({"stage": "Energy", "reason": reason})
            return {
                "status": "unavailable",
                "energy_joules": None,
                "energy_kwh": None,
                "power_watts": None,
                "duration_seconds": duration,
                "measurement_mode": None,
                "measurement_source": None,
                "provider": provider_name,
                "security_controls_active": control_count,
                "estimated": None,
                "reason": reason,
            }

    def _calculate_carbon(
        self,
        energy: dict,
        carbon_intensity: Optional[float],
        renewable_percentage: Optional[float],
        warnings: list[dict],
    ) -> dict:
        if energy.get("status") != "completed":
            reason = "Carbon unavailable because energy measurement is unavailable"
            return {
                "status": "unavailable",
                "reason": reason,
                "energy_kwh": None,
                "carbon_intensity": None,
                "renewable_pct": None,
                "gross_co2_kg": None,
                "renewable_offset_kg": None,
                "net_co2_kg": None,
                "carbon_basis": None,
                "measurement_mode": None,
                "calculation_breakdown": None,
            }

        mode = energy.get("measurement_mode")
        try:
            result = calculate_carbon(
                energy["energy_kwh"],
                carbon_intensity,
                renewable_percentage,
            )
            return {
                "status": "completed",
                "reason": None,
                "energy_kwh": result["energy_kwh"],
                "carbon_intensity": result["carbon_intensity"],
                "renewable_pct": result["renewable_pct"],
                "gross_co2_kg": result["gross_co2_kg"],
                "renewable_offset_kg": result["renewable_offset_kg"],
                "net_co2_kg": result["net_co2_kg"],
                "carbon_basis": carbon_basis_label(mode),
                "measurement_mode": mode,
                "calculation_breakdown": result["calculation_breakdown"],
            }
        except Exception as exc:
            reason = f"Carbon calculation unavailable: {exc}"
            warnings.append({"stage": "Carbon", "reason": reason})
            return {
                "status": "unavailable",
                "reason": reason,
                "energy_kwh": energy.get("energy_kwh"),
                "carbon_intensity": None,
                "renewable_pct": None,
                "gross_co2_kg": None,
                "renewable_offset_kg": None,
                "net_co2_kg": None,
                "carbon_basis": None,
                "measurement_mode": mode,
                "calculation_breakdown": None,
            }

    def _compare_baseline_to_defense(
        self,
        provider_name: str,
        duration: float,
        control_count: int,
        intensity: Optional[str],
        energy: dict,
        carbon: dict,
        warnings: list[dict],
    ) -> dict:
        """Paired same-provider baseline (0 controls) vs defense (N controls).

        Same duration, same provider, same coefficients on both sides, so the
        difference is a like-for-like model comparison. Phase 5/6/7 formulas
        (marginal energy, interaction effect, defense energy amplification)
        are untouched; those remain available for persisted run pairs via the
        research endpoints.
        """
        unavailable = {
            "status": "unavailable",
            "reason": "Energy or carbon unavailable; no valid baseline/defense comparison",
            "basis": None,
            "measurement_mode": None,
            "baseline_energy_kwh": None,
            "defense_energy_kwh": None,
            "energy_difference_kwh": None,
            "baseline_carbon_kg": None,
            "defense_carbon_kg": None,
            "carbon_difference_kg": None,
            "direction": None,
        }
        if energy.get("status") != "completed" or carbon.get("status") != "completed":
            return unavailable

        try:
            provider = get_provider(provider_name)
            baseline_reading = provider.get_measurement(
                duration_seconds=duration,
                workload_count=1,
                security_controls_active=0,
                attack_intensity=intensity,
            )
            baseline_carbon = calculate_carbon(
                baseline_reading.energy_kwh,
                carbon.get("carbon_intensity"),
                carbon.get("renewable_pct"),
            )
        except Exception as exc:
            reason = f"Baseline comparison unavailable: {exc}"
            warnings.append({"stage": "Comparison", "reason": reason})
            return {**unavailable, "reason": reason}

        baseline_kwh = round(baseline_reading.energy_kwh, 8)
        defense_kwh = energy["energy_kwh"]
        energy_diff = round(defense_kwh - baseline_kwh, 8)
        baseline_co2 = baseline_carbon["net_co2_kg"]
        defense_co2 = carbon["net_co2_kg"]
        carbon_diff = round(defense_co2 - baseline_co2, 8)

        if energy_diff > 0:
            direction = "additional_energy"
            interpretation = (
                "Activated controls add energy/carbon overhead relative to "
                "the no-controls baseline"
            )
        elif energy_diff < 0:
            direction = "energy_saved"
            interpretation = "Defense configuration uses less energy than the baseline"
        else:
            direction = "neutral"
            interpretation = "No energy difference between baseline and defense"

        mode = energy.get("measurement_mode")
        return {
            "status": "available",
            "reason": None,
            "basis": f"paired_{(mode or 'unknown').lower()}_same_provider",
            "measurement_mode": mode,
            "baseline_energy_kwh": baseline_kwh,
            "defense_energy_kwh": defense_kwh,
            "energy_difference_kwh": energy_diff,
            "baseline_carbon_kg": baseline_co2,
            "defense_carbon_kg": defense_co2,
            "carbon_difference_kg": carbon_diff,
            "direction": direction,
            "interpretation": interpretation,
        }

    def _record_research(
        self,
        record_research: bool,
        experiment_uuid: Optional[str],
        attack_type: str,
        intensity: Optional[str],
        profile,
        control_ids: list[str],
        energy: dict,
        carbon: dict,
        severity: str,
        response: str,
        risk_score: Optional[float],
        warnings: list[dict],
    ) -> dict:
        if not record_research:
            return {
                "status": "not_requested",
                "reason": None,
                "experiment_uuid": None,
                "run_id": None,
                "trial_number": None,
            }

        if not experiment_uuid:
            reason = "experiment_uuid is required to record a research observation"
            warnings.append({"stage": "Research Observation", "reason": reason})
            return {
                "status": "failed",
                "reason": reason,
                "experiment_uuid": None,
                "run_id": None,
                "trial_number": None,
            }

        if energy.get("status") != "completed":
            reason = "Research observation skipped: energy measurement unavailable"
            warnings.append({"stage": "Research Observation", "reason": reason})
            return {
                "status": "failed",
                "reason": reason,
                "experiment_uuid": experiment_uuid,
                "run_id": None,
                "trial_number": None,
            }

        try:
            result = ResearchExperimentService(self.db).record_pipeline_observation(
                experiment_uuid,
                attack_type=attack_type,
                attack_intensity=intensity or "medium",
                security_controls=control_ids,
                measurement_mode=energy["measurement_mode"],
                measurement_source=energy["measurement_source"],
                energy_joules=energy["energy_joules"],
                power_watts=energy["power_watts"],
                duration_seconds=energy["duration_seconds"],
                threat_severity=severity,
                security_response=response,
                risk_score=risk_score or 0.0,
                carbon_net_kg=carbon.get("net_co2_kg"),
                carbon_basis=carbon.get("carbon_basis"),
                carbon_intensity=carbon.get("carbon_intensity"),
                attack_profile=profile.to_dict() if profile else None,
            )
            return {**result, "reason": None}
        except ExperimentError as exc:
            reason = str(exc)
            warnings.append({"stage": "Research Observation", "reason": reason})
            return {
                "status": "failed",
                "reason": reason,
                "experiment_uuid": experiment_uuid,
                "run_id": None,
                "trial_number": None,
            }
        except Exception as exc:
            reason = f"Research persistence failed: {exc}"
            warnings.append({"stage": "Research Observation", "reason": reason})
            return {
                "status": "failed",
                "reason": reason,
                "experiment_uuid": experiment_uuid,
                "run_id": None,
                "trial_number": None,
            }

    @staticmethod
    def _analytics_feeds(persist_warning: Optional[dict], research: dict) -> list[str]:
        feeds = []
        if persist_warning is None:
            feeds.extend([
                "security_stats",
                "threat_stats",
                "dashboard",
            ])
        if research.get("status") == "recorded":
            feeds.extend(["research_summary", "research_metrics"])
        return feeds

    @staticmethod
    def _build_stages(
        sim: dict,
        defense: dict,
        energy: dict,
        carbon: dict,
        research: dict,
    ) -> list[dict]:
        step_renames = {
            "Energy Estimate": "Detection Energy Estimate",
            "Carbon Impact": "Detection Carbon Estimate",
        }
        stages = [
            {
                "step": step_renames.get(step["step"], step["step"]),
                "status": step["status"],
                "detail": step["detail"],
            }
            for step in sim.get("pipeline", [])
        ]

        stages.append({
            "step": "Defense Selection",
            "status": "completed" if defense["selected"] else "skipped",
            "detail": (
                f"{len(defense['selected'])} control(s) selected "
                f"({defense['tier']}, rule-based): "
                f"{', '.join(defense['selected']) or 'none'}"
            ),
        })

        if energy["status"] == "completed":
            detail = (
                f"{energy['energy_kwh']} kWh @ {energy['power_watts']} W for "
                f"{energy['duration_seconds']}s with "
                f"{energy['security_controls_active']} control(s) "
                f"[{energy['measurement_mode']}]"
            )
            status = "completed"
        else:
            detail = energy.get("reason") or "unavailable"
            status = "failed"
        stages.append({
            "step": "Defense Energy Measurement",
            "status": status,
            "detail": detail,
        })

        if carbon["status"] == "completed":
            detail = (
                f"net {carbon['net_co2_kg']} kg CO2 "
                f"[{carbon['carbon_basis']}]"
            )
            status = "completed"
        else:
            detail = carbon.get("reason") or "unavailable"
            status = "failed"
        stages.append({
            "step": "Defense Carbon Calculation",
            "status": status,
            "detail": detail,
        })

        research_status = research.get("status")
        stage_status = {
            "recorded": "completed",
            "not_requested": "skipped",
        }.get(research_status, "failed")
        stages.append({
            "step": "Research Observation",
            "status": stage_status,
            "detail": (
                f"run {research.get('run_id')} (trial {research.get('trial_number')}) "
                f"recorded on experiment {research.get('experiment_uuid')}"
                if research_status == "recorded"
                else research.get("reason") or research_status
            ),
        })

        stages.append({
            "step": "Analytics",
            "status": "completed",
            "detail": "Run persisted to feeds consumed by dashboard/research analytics",
        })
        return stages
