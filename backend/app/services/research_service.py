"""
Research Experiment Engine.

Executes controlled, reproducible experiments that record:
- Attack simulation results
- Energy measurements
- Security effectiveness
- Workload metadata

All experiments are LOCAL SYNTHETIC SIMULATIONS.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.research import (
    Experiment,
    ExperimentRun,
    EnergyMeasurement,
    SecurityEffectiveness,
)
from app.repositories.research_repo import (
    ExperimentRepository,
    ExperimentRunRepository,
    EnergyMeasurementRepository,
    SecurityEffectivenessRepository,
)
from app.engines.security.attack_profiles import (
    build_attack_profile,
    validate_attack_type,
    validate_intensity,
    AttackProfileError,
    get_supported_attack_types,
    get_supported_intensities,
)
from app.engines.security.security_controls import (
    validate_control_id,
    get_supported_control_ids,
    SecurityControlError,
)
from app.engines.security.attack_simulator import simulate_attack
from app.engines.energy.factory import get_provider


VALID_EXPERIMENT_TYPES = {"MARGINAL_ENERGY", "INTERACTION", "DEFENSE_AMPLIFICATION"}
VALID_PROVIDERS = {"estimated", "rapl", "kepler", "external"}

LIFECYCLE_STATUSES = {
    "created": {"validating"},
    "validating": {"running", "failed"},
    "running": {"measuring", "failed", "cancelled"},
    "measuring": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}

CONFIG_VERSION = "1.0.0"


class ExperimentError(Exception):
    pass


def _normalize_controls(controls: list[str]) -> list[str]:
    return sorted(set(c.strip().lower() for c in controls if c.strip()))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ResearchExperimentService:
    def __init__(self, db: Session):
        self.db = db
        self.experiment_repo = ExperimentRepository(db)
        self.run_repo = ExperimentRunRepository(db)
        self.measurement_repo = EnergyMeasurementRepository(db)
        self.effectiveness_repo = SecurityEffectivenessRepository(db)

    def validate_experiment_config(self, config: dict) -> dict:
        errors = []

        if config.get("experiment_type") not in VALID_EXPERIMENT_TYPES:
            errors.append(f"Invalid experiment_type: {config.get('experiment_type')}. Valid: {sorted(VALID_EXPERIMENT_TYPES)}")

        attack_type = config.get("attack_type")
        try:
            validate_attack_type(attack_type)
        except AttackProfileError as e:
            errors.append(str(e))

        intensity = config.get("attack_intensity")
        try:
            validate_intensity(intensity)
        except AttackProfileError as e:
            errors.append(str(e))

        controls = config.get("security_controls", [])
        for ctrl in controls:
            try:
                validate_control_id(ctrl)
            except SecurityControlError as e:
                errors.append(str(e))

        provider = config.get("measurement_provider", "estimated")
        if provider not in VALID_PROVIDERS:
            errors.append(f"Invalid measurement_provider: {provider}. Valid: {sorted(VALID_PROVIDERS)}")

        num_trials = config.get("number_of_trials", 1)
        if not isinstance(num_trials, int) or num_trials < 1 or num_trials > 20:
            errors.append(f"number_of_trials must be 1-20, got {num_trials}")

        duration = config.get("duration_seconds", 60)
        if not isinstance(duration, (int, float)) or duration <= 0 or duration > 3600:
            errors.append(f"duration_seconds must be 1-3600, got {duration}")

        if errors:
            raise ExperimentError("Validation failed: " + "; ".join(errors))

        return config

    def create_experiment(self, config: dict) -> Experiment:
        self.validate_experiment_config(config)

        controls = _normalize_controls(config.get("security_controls", []))
        attack_type = config["attack_type"]
        intensity = config["attack_intensity"]
        duration = config.get("duration_seconds", 60)
        num_trials = config.get("number_of_trials", 1)

        attack_profile = build_attack_profile(
            attack_type=attack_type,
            intensity=intensity,
            duration_seconds=duration,
            workload_override=config.get("attack_workload"),
        )

        workload_profile = f"{attack_type}_{intensity}"
        controls_json = json.dumps(controls) if controls else "[]"

        experiment_data = {
            "name": config.get("name", f"Experiment {attack_type} {intensity}"),
            "description": config.get("description"),
            "experiment_type": config["experiment_type"],
            "attack_type": attack_type,
            "attack_intensity": intensity,
            "workload_profile": workload_profile,
            "security_controls": controls_json,
            "measurement_mode": config.get("measurement_provider", "estimated").upper(),
            "duration_seconds": float(duration),
            "num_trials": num_trials,
            "carbon_intensity": config.get("carbon_intensity"),
            "renewable_pct": config.get("renewable_pct"),
            "software_version": settings.APP_VERSION,
            "configuration_version": CONFIG_VERSION,
            "random_seed": config.get("random_seed"),
            "status": "created",
            "notes": config.get("notes"),
        }

        return self.experiment_repo.create(experiment_data)

    def execute_experiment(self, experiment_uuid: str) -> Experiment:
        experiment = self.experiment_repo.get_by_uuid(experiment_uuid)
        if not experiment:
            raise ExperimentError(f"Experiment not found: {experiment_uuid}")

        self._transition_status(experiment, "validating")
        self._transition_status(experiment, "running")

        try:
            controls = json.loads(experiment.security_controls or "[]")
            num_trials = experiment.num_trials

            for trial_num in range(1, num_trials + 1):
                self._execute_trial(experiment, trial_num, controls)

            self._transition_status(experiment, "measuring")
            self._transition_status(experiment, "completed")
            experiment.completed_at = _now_utc()
            self.db.commit()

        except Exception as e:
            self._transition_status(experiment, "failed")
            experiment.notes = f"Execution failed: {str(e)}"
            self.db.commit()
            raise

        return experiment

    def _execute_trial(self, experiment: Experiment, trial_num: int, controls: list[str]):
        run_data = {
            "experiment_id": experiment.id,
            "trial_number": trial_num,
            "attack_type": experiment.attack_type,
            "attack_intensity": experiment.attack_intensity,
            "workload_profile": experiment.workload_profile,
            "security_controls": json.dumps(controls),
            "control_count": len(controls),
            "measurement_mode": experiment.measurement_mode,
            "start_time": _now_utc(),
            "status": "running",
        }

        run = self.run_repo.create(run_data)

        try:
            attack_result = simulate_attack(experiment.attack_type)

            attack_profile = build_attack_profile(
                attack_type=experiment.attack_type,
                intensity=experiment.attack_intensity,
                duration_seconds=int(experiment.duration_seconds),
            )

            run.workload_value = attack_profile.workload.value
            run.workload_unit = attack_profile.workload.unit
            run.attack_parameters = json.dumps(attack_profile.to_dict())
            self.run_repo.update(run, {
                "workload_value": run.workload_value,
                "workload_unit": run.workload_unit,
                "attack_parameters": run.attack_parameters,
            })

            provider = get_provider(experiment.measurement_mode.lower())
            energy_reading = provider.get_measurement(
                duration_seconds=experiment.duration_seconds,
                workload_count=1,
                attack_intensity=experiment.attack_intensity,
                security_controls_active=len(controls),
            )

            measurement_data = {
                "run_id": run.id,
                "energy_joules": energy_reading.energy_joules,
                "power_watts": energy_reading.power_watts,
                "duration_seconds": experiment.duration_seconds,
                "cpu_usage_pct": energy_reading.cpu_usage_pct,
                "memory_usage_pct": energy_reading.memory_usage_pct,
                "network_usage_mbps": energy_reading.network_usage_mbps,
                "source": energy_reading.source,
                "measurement_mode": energy_reading.mode.value,
            }
            self.measurement_repo.create(measurement_data)

            threat_info = attack_result.get("threat", {})
            risk_info = attack_result.get("risk_assessment", {})
            effectiveness_data = {
                "run_id": run.id,
                "detection_rate": threat_info.get("confidence"),
                "detection_latency_ms": None,
                "false_positive_rate": None,
                "mitigation_time_ms": None,
                "threat_severity": threat_info.get("severity"),
                "security_response": threat_info.get("recommended_action"),
                "security_score": risk_info.get("risk_score"),
                "controls_active": json.dumps(controls) if controls else "[]",
                "controls_config": json.dumps({"controls": controls}),
            }
            self.effectiveness_repo.create(effectiveness_data)

            self.run_repo.update(run, {
                "end_time": _now_utc(),
                "duration_seconds": experiment.duration_seconds,
                "status": "completed",
            })

        except Exception as e:
            self.run_repo.update(run, {
                "end_time": _now_utc(),
                "status": "failed",
                "error_message": str(e),
            })
            raise

    def _transition_status(self, experiment: Experiment, new_status: str):
        current = experiment.status
        valid_transitions = LIFECYCLE_STATUSES.get(current, set())
        if new_status not in valid_transitions:
            raise ExperimentError(
                f"Invalid status transition: {current} -> {new_status}. "
                f"Valid: {sorted(valid_transitions)}"
            )
        experiment.status = new_status
        self.db.commit()

    def get_experiment(self, experiment_uuid: str) -> Optional[Experiment]:
        return self.experiment_repo.get_by_uuid(experiment_uuid)

    def list_experiments(
        self,
        experiment_type: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Experiment]:
        return self.experiment_repo.filter_experiments(
            experiment_type=experiment_type,
            status=status,
            offset=offset,
            limit=limit,
        )

    def get_experiment_runs(self, experiment_uuid: str) -> list[ExperimentRun]:
        experiment = self.experiment_repo.get_by_uuid(experiment_uuid)
        if not experiment:
            raise ExperimentError(f"Experiment not found: {experiment_uuid}")
        return self.run_repo.get_by_experiment(experiment.id)

    def get_run_measurements(self, run_id: int) -> list[EnergyMeasurement]:
        return self.measurement_repo.get_by_run(run_id)

    def get_run_effectiveness(self, run_id: int) -> Optional[SecurityEffectiveness]:
        return self.effectiveness_repo.get_by_run(run_id)

    def get_experiment_summary(self, experiment_uuid: str) -> dict:
        experiment = self.get_experiment(experiment_uuid)
        if not experiment:
            raise ExperimentError(f"Experiment not found: {experiment_uuid}")

        runs = self.get_experiment_runs(experiment_uuid)
        all_measurements = []
        all_effects = []
        for run in runs:
            all_measurements.extend(self.get_run_measurements(run.id))
            effect = self.get_run_effectiveness(run.id)
            if effect:
                all_effects.append(effect)

        return {
            "experiment": experiment,
            "runs": runs,
            "measurements": all_measurements,
            "security_effects": all_effects,
        }

    def get_experiment_status(self, experiment_uuid: str) -> dict:
        experiment = self.get_experiment(experiment_uuid)
        if not experiment:
            raise ExperimentError(f"Experiment not found: {experiment_uuid}")

        runs = self.get_experiment_runs(experiment_uuid)
        completed = sum(1 for r in runs if r.status == "completed")
        failed = sum(1 for r in runs if r.status == "failed")

        return {
            "experiment_uuid": experiment.experiment_uuid,
            "status": experiment.status,
            "total_runs": len(runs),
            "completed_runs": completed,
            "failed_runs": failed,
        }
