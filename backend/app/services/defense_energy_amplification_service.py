"""
Defense Energy Amplification Service.

Research question: How much additional energy does a security defense consume
when operating during an attack, compared with the same attack workload
without that defense?

    ADE = E_attack+defense - E_attack+baseline
    DEA = ADE / Attack_Workload

Where:
    E_attack+baseline = energy of the attack workload without the defense
    E_attack+defense  = energy of the same attack workload with the defense

DEA is expressed per workload unit (e.g., joules per packet). It is NOT
universally comparable across different workload units; the workload unit is
preserved on every result.

The comparison is paired and controlled: baseline and defense runs must match
on attack type, attack intensity, workload value, workload unit, duration,
environment, software/config version, energy provider, and measurement mode.
Only the defense configuration may differ.

Relation to other phases:
    Phase 5 (marginal energy):  dE = E_security - E_baseline
    Phase 6 (interaction):      I(A,B) = E_AB - E_A - E_B + E_0
    Phase 7 (this service):     ADE = E_attack+defense - E_attack+baseline

Formula version: defense_energy_amplification_v1
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.research import (
    Experiment,
    ExperimentRun,
    EnergyMeasurement,
    DefenseAmplificationResult,
)
from app.repositories.research_repo import (
    ExperimentRepository,
    ExperimentRunRepository,
    EnergyMeasurementRepository,
    DefenseAmplificationResultRepository,
)
from app.engines.carbon.carbon_calculator import JOULES_PER_KWH, calculate_carbon
from app.engines.security.security_controls import (
    validate_control_id,
    SecurityControlError,
)
from app.services.interaction_effect_service import descriptive_statistics
from app.schemas.research import (
    DefenseAmplificationResponse,
    DefenseAmplificationComputeResponse,
    DefenseAmplificationListResponse,
    DefenseAmplificationStatisticsResponse,
    StatisticsSummary,
)

FORMULA_VERSION = "defense_energy_amplification_v1"


class DefenseEnergyAmplificationError(Exception):
    pass


def calculate_amplification_values(
    baseline_energy: float,
    defense_energy: float,
    attack_workload: float,
    duration_s: float,
    carbon_intensity: Optional[float] = None,
) -> dict:
    if baseline_energy < 0:
        raise DefenseEnergyAmplificationError(
            f"Negative baseline energy: {baseline_energy}"
        )
    if defense_energy < 0:
        raise DefenseEnergyAmplificationError(
            f"Negative defense energy: {defense_energy}"
        )
    if attack_workload is None:
        raise DefenseEnergyAmplificationError("Invalid workload: None")
    if attack_workload < 0:
        raise DefenseEnergyAmplificationError(
            f"Invalid workload value: {attack_workload}"
        )
    if attack_workload == 0:
        raise DefenseEnergyAmplificationError(
            "Zero workload: DEA cannot be computed (division by zero)"
        )
    if duration_s is None or duration_s <= 0:
        raise DefenseEnergyAmplificationError(
            f"Invalid duration: {duration_s}"
        )

    amplification = defense_energy - baseline_energy
    ratio = amplification / attack_workload

    power_baseline = baseline_energy / duration_s
    power_defense = defense_energy / duration_s
    power_amplification = power_defense - power_baseline

    intensity = carbon_intensity or settings.DEFAULT_CARBON_INTENSITY
    carbon_baseline = calculate_carbon(
        baseline_energy / JOULES_PER_KWH, intensity, 0
    )["gross_co2_kg"]
    carbon_defense = calculate_carbon(
        defense_energy / JOULES_PER_KWH, intensity, 0
    )["gross_co2_kg"]
    amplification_carbon = carbon_defense - carbon_baseline

    return {
        "additional_defense_energy": amplification,
        "defense_energy_amplification": ratio,
        "power_baseline": power_baseline,
        "power_defense": power_defense,
        "power_amplification": power_amplification,
        "carbon_baseline_kg": carbon_baseline,
        "carbon_defense_kg": carbon_defense,
        "amplification_carbon_kg": amplification_carbon,
        "carbon_intensity": intensity,
    }


class DefenseEnergyAmplificationService:
    def __init__(self, db: Session):
        self.db = db
        self.experiment_repo = ExperimentRepository(db)
        self.run_repo = ExperimentRunRepository(db)
        self.measurement_repo = EnergyMeasurementRepository(db)
        self.amplification_repo = DefenseAmplificationResultRepository(db)

    @staticmethod
    def _normalize_control(control_id: str) -> str:
        return control_id.strip().lower()

    @staticmethod
    def _controls_key(run: ExperimentRun) -> str:
        raw = run.security_controls or "[]"
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return "|".join(sorted(str(c).strip().lower() for c in parsed))
        except (ValueError, TypeError):
            pass
        return str(raw).strip()

    @staticmethod
    def _effective_duration(run: ExperimentRun) -> float:
        return run.duration_seconds or 60.0

    def _validate_pair(
        self,
        baseline_run: ExperimentRun,
        defense_run: ExperimentRun,
        baseline_experiment: Optional[Experiment],
        defense_experiment: Optional[Experiment],
    ) -> list[str]:
        errors = []

        if baseline_run.attack_type != defense_run.attack_type:
            errors.append(
                "Attack type mismatch: "
                f"baseline={baseline_run.attack_type}, "
                f"defense={defense_run.attack_type}"
            )

        if baseline_run.attack_intensity != defense_run.attack_intensity:
            errors.append(
                "Attack intensity mismatch: "
                f"baseline={baseline_run.attack_intensity}, "
                f"defense={defense_run.attack_intensity}"
            )

        if baseline_run.workload_value != defense_run.workload_value:
            errors.append(
                "Workload value mismatch: "
                f"baseline={baseline_run.workload_value}, "
                f"defense={defense_run.workload_value}"
            )

        if baseline_run.workload_unit != defense_run.workload_unit:
            errors.append(
                "Workload unit mismatch: "
                f"baseline={baseline_run.workload_unit}, "
                f"defense={defense_run.workload_unit}"
            )

        baseline_duration = self._effective_duration(baseline_run)
        defense_duration = self._effective_duration(defense_run)
        if baseline_duration != defense_duration:
            errors.append(
                "Duration mismatch: "
                f"baseline={baseline_duration}, defense={defense_duration}"
            )

        if baseline_run.measurement_mode != defense_run.measurement_mode:
            errors.append(
                "Measurement mode mismatch: "
                f"baseline={baseline_run.measurement_mode}, "
                f"defense={defense_run.measurement_mode}"
            )

        baseline_env = (
            baseline_experiment.environment_info if baseline_experiment else None
        )
        defense_env = (
            defense_experiment.environment_info if defense_experiment else None
        )
        if baseline_env != defense_env:
            errors.append(
                "Environment mismatch: "
                f"baseline={baseline_env}, defense={defense_env}"
            )

        baseline_sw = (
            (baseline_experiment.software_version, baseline_experiment.configuration_version)
            if baseline_experiment
            else (None, None)
        )
        defense_sw = (
            (defense_experiment.software_version, defense_experiment.configuration_version)
            if defense_experiment
            else (None, None)
        )
        if baseline_sw != defense_sw:
            errors.append(
                "Software/config version mismatch: "
                f"baseline={baseline_sw[0]}/{baseline_sw[1]}, "
                f"defense={defense_sw[0]}/{defense_sw[1]}"
            )

        if baseline_run.trial_number != defense_run.trial_number:
            errors.append(
                "Trial mismatch: "
                f"baseline={baseline_run.trial_number}, "
                f"defense={defense_run.trial_number}"
            )

        if self._controls_key(baseline_run) == self._controls_key(defense_run):
            errors.append(
                "Identical baseline and defense configurations: "
                f"controls=[{self._controls_key(baseline_run)}] - "
                "amplification cannot be computed"
            )

        return errors

    def _validate_workload(self, label: str, run: ExperimentRun) -> float:
        workload = run.workload_value
        if workload is None:
            raise DefenseEnergyAmplificationError(
                f"Invalid workload value for {label} run {run.id}: None"
            )
        if workload < 0:
            raise DefenseEnergyAmplificationError(
                f"Invalid workload value for {label} run {run.id}: {workload}"
            )
        if workload == 0:
            raise DefenseEnergyAmplificationError(
                f"Zero workload for {label} run {run.id}: "
                "DEA cannot be computed (division by zero)"
            )
        return workload

    def _validate_duration(self, label: str, run: ExperimentRun) -> None:
        if run.duration_seconds is not None and run.duration_seconds <= 0:
            raise DefenseEnergyAmplificationError(
                f"Invalid duration for {label} run {run.id}: "
                f"{run.duration_seconds}"
            )

    def _get_measurement(
        self, label: str, run_id: int
    ) -> EnergyMeasurement:
        measurement = self.measurement_repo.get_latest_by_run(run_id)
        if not measurement:
            raise DefenseEnergyAmplificationError(
                f"No energy measurement found for {label} run {run_id}"
            )
        return measurement

    def _validate_energy(self, label: str, run_id: int, measurement: EnergyMeasurement) -> None:
        if measurement.energy_joules < 0:
            raise DefenseEnergyAmplificationError(
                f"Negative energy measurement for {label} run {run_id}: "
                f"{measurement.energy_joules}"
            )

    def _validate_provider(
        self,
        baseline_measurement: EnergyMeasurement,
        defense_measurement: EnergyMeasurement,
    ) -> None:
        if baseline_measurement.source != defense_measurement.source:
            raise DefenseEnergyAmplificationError(
                "Energy provider mismatch: "
                f"baseline={baseline_measurement.source}, "
                f"defense={defense_measurement.source}"
            )

    def _build_statistics(
        self,
        amplifications: list[float],
        ratios: list[float],
        power_amplifications: list[float],
        carbon_amplifications: list[float],
    ) -> DefenseAmplificationStatisticsResponse:
        return DefenseAmplificationStatisticsResponse(
            amplification_energy=StatisticsSummary(
                **descriptive_statistics(amplifications)
            ),
            amplification_ratio=StatisticsSummary(
                **descriptive_statistics(ratios)
            ),
            power_amplification=StatisticsSummary(
                **descriptive_statistics(power_amplifications)
            ),
            carbon_amplification=StatisticsSummary(
                **descriptive_statistics(carbon_amplifications)
            ),
            formula_version=FORMULA_VERSION,
        )

    def _to_response(
        self, row: DefenseAmplificationResult
    ) -> DefenseAmplificationResponse:
        data = {
            column.name: getattr(row, column.name)
            for column in DefenseAmplificationResult.__table__.columns
        }
        raw_stats = data.pop("statistics_json", None)
        if raw_stats:
            data["statistics"] = json.loads(raw_stats)
        else:
            data["statistics"] = None
        return DefenseAmplificationResponse(**data)

    def compute_amplification(
        self,
        baseline_run_ids: list[int],
        defense_run_ids: list[int],
        control_name: str,
        experiment_id: Optional[int] = None,
        carbon_intensity: Optional[float] = None,
    ) -> DefenseAmplificationComputeResponse:
        control_name = self._normalize_control(control_name)
        try:
            validate_control_id(control_name)
        except SecurityControlError as e:
            raise DefenseEnergyAmplificationError(str(e))

        if not baseline_run_ids:
            raise DefenseEnergyAmplificationError("Missing baseline run ids")
        if not defense_run_ids:
            raise DefenseEnergyAmplificationError("Missing defense run ids")
        if len(baseline_run_ids) != len(defense_run_ids):
            raise DefenseEnergyAmplificationError(
                "Run count mismatch: "
                f"baseline={len(baseline_run_ids)}, "
                f"defense={len(defense_run_ids)}"
            )

        if experiment_id is not None:
            experiment = self.experiment_repo.get_by_id(experiment_id)
            if not experiment:
                raise DefenseEnergyAmplificationError(
                    f"Experiment not found: {experiment_id}"
                )

        prepared: list[dict] = []
        amplifications: list[float] = []
        ratios: list[float] = []
        power_amplifications: list[float] = []
        carbon_amplifications: list[float] = []

        for index in range(len(baseline_run_ids)):
            baseline_id = baseline_run_ids[index]
            defense_id = defense_run_ids[index]

            baseline_run = self.run_repo.get_by_id(baseline_id)
            if not baseline_run:
                raise DefenseEnergyAmplificationError(
                    f"Baseline run not found: {baseline_id}"
                )
            defense_run = self.run_repo.get_by_id(defense_id)
            if not defense_run:
                raise DefenseEnergyAmplificationError(
                    f"Defense run not found: {defense_id}"
                )

            if baseline_id == defense_id:
                raise DefenseEnergyAmplificationError(
                    "Identical baseline and defense runs: "
                    f"run {baseline_id} cannot be compared with itself"
                )

            baseline_experiment = self.experiment_repo.get_by_id(
                baseline_run.experiment_id
            )
            defense_experiment = self.experiment_repo.get_by_id(
                defense_run.experiment_id
            )

            errors = self._validate_pair(
                baseline_run, defense_run, baseline_experiment, defense_experiment
            )
            if errors:
                raise DefenseEnergyAmplificationError(
                    "Runs not comparable: " + "; ".join(errors)
                )

            workload = self._validate_workload("baseline", baseline_run)
            if baseline_run.workload_unit is None:
                raise DefenseEnergyAmplificationError(
                    f"Invalid workload unit for baseline run {baseline_run.id}: None"
                )
            self._validate_duration("baseline", baseline_run)
            self._validate_duration("defense", defense_run)

            baseline_measurement = self._get_measurement("baseline", baseline_id)
            defense_measurement = self._get_measurement("defense", defense_id)
            self._validate_energy("baseline", baseline_id, baseline_measurement)
            self._validate_energy("defense", defense_id, defense_measurement)
            self._validate_provider(baseline_measurement, defense_measurement)

            duration = self._effective_duration(baseline_run)

            calc = calculate_amplification_values(
                baseline_energy=baseline_measurement.energy_joules,
                defense_energy=defense_measurement.energy_joules,
                attack_workload=workload,
                duration_s=duration,
                carbon_intensity=carbon_intensity,
            )

            amplifications.append(calc["additional_defense_energy"])
            ratios.append(calc["defense_energy_amplification"])
            power_amplifications.append(calc["power_amplification"])
            carbon_amplifications.append(calc["amplification_carbon_kg"])

            prepared.append(
                {
                    "experiment_id": (
                        experiment_id
                        if experiment_id is not None
                        else baseline_run.experiment_id
                    ),
                    "trial_number": index + 1,
                    "baseline_run_id": baseline_id,
                    "defense_run_id": defense_id,
                    "control_name": control_name,
                    "attack_type": baseline_run.attack_type,
                    "attack_intensity": baseline_run.attack_intensity,
                    "attack_workload": workload,
                    "workload_unit": baseline_run.workload_unit,
                    "duration_seconds": duration,
                    "energy_attack_only": baseline_measurement.energy_joules,
                    "energy_attack_defense": defense_measurement.energy_joules,
                    **calc,
                    "measurement_mode": baseline_run.measurement_mode,
                    "energy_provider": baseline_measurement.source,
                    "environment_info": (
                        baseline_experiment.environment_info
                        if baseline_experiment
                        else None
                    ),
                    "software_version": (
                        baseline_experiment.software_version
                        if baseline_experiment
                        else None
                    ),
                    "configuration_version": (
                        baseline_experiment.configuration_version
                        if baseline_experiment
                        else None
                    ),
                    "num_paired_trials": len(baseline_run_ids),
                    "formula_version": FORMULA_VERSION,
                }
            )

        statistics = self._build_statistics(
            amplifications, ratios, power_amplifications, carbon_amplifications
        )
        stats_json = json.dumps(statistics.model_dump())
        for row_data in prepared:
            row_data["statistics_json"] = stats_json

        rows = [
            self.amplification_repo.create(row_data) for row_data in prepared
        ]

        return DefenseAmplificationComputeResponse(
            total=len(rows),
            results=[self._to_response(row) for row in rows],
            statistics=statistics,
        )

    def get_amplification(
        self, amplification_id: int
    ) -> Optional[DefenseAmplificationResponse]:
        row = self.amplification_repo.get_by_id(amplification_id)
        if not row:
            return None
        return self._to_response(row)

    def list_amplification(
        self,
        attack_type: Optional[str] = None,
        attack_intensity: Optional[str] = None,
        measurement_mode: Optional[str] = None,
        control_name: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> DefenseAmplificationListResponse:
        rows = self.amplification_repo.filter_amplification(
            attack_type=attack_type,
            attack_intensity=attack_intensity,
            measurement_mode=measurement_mode,
            control_name=control_name,
            offset=offset,
            limit=limit,
        )
        return DefenseAmplificationListResponse(
            total=len(rows),
            items=[self._to_response(row) for row in rows],
        )
