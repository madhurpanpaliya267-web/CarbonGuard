"""
Marginal Energy Attribution Service.

Calculates the energy cost of security controls by comparing:
- Baseline: attack with NO security controls
- Security: attack WITH selected security controls

ΔE = E_security - E_baseline
ΔP = P_security - P_baseline
ΔC = C_security - C_baseline

Formula version: marginal_energy_v1
"""
import json
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.research import (
    Experiment,
    ExperimentRun,
    EnergyMeasurement,
    SecurityEffectiveness,
    EnergyAttribution,
)
from app.repositories.research_repo import (
    ExperimentRepository,
    ExperimentRunRepository,
    EnergyMeasurementRepository,
    SecurityEffectivenessRepository,
    EnergyAttributionRepository,
)
from app.engines.carbon.carbon_calculator import JOULES_PER_KWH, calculate_carbon

FORMULA_VERSION = "marginal_energy_v1"


class MarginalEnergyError(Exception):
    pass


class MarginalEnergyService:
    def __init__(self, db: Session):
        self.db = db
        self.experiment_repo = ExperimentRepository(db)
        self.run_repo = ExperimentRunRepository(db)
        self.measurement_repo = EnergyMeasurementRepository(db)
        self.effectiveness_repo = SecurityEffectivenessRepository(db)
        self.attribution_repo = EnergyAttributionRepository(db)

    def _validate_run_pair(
        self,
        baseline_run: ExperimentRun,
        security_run: ExperimentRun,
    ) -> list[str]:
        errors = []

        if baseline_run.attack_type != security_run.attack_type:
            errors.append(
                f"Attack type mismatch: baseline={baseline_run.attack_type}, "
                f"security={security_run.attack_type}"
            )

        if baseline_run.attack_intensity != security_run.attack_intensity:
            errors.append(
                f"Attack intensity mismatch: baseline={baseline_run.attack_intensity}, "
                f"security={security_run.attack_intensity}"
            )

        if baseline_run.workload_unit != security_run.workload_unit:
            errors.append(
                f"Workload unit mismatch: baseline={baseline_run.workload_unit}, "
                f"security={security_run.workload_unit}"
            )

        if baseline_run.workload_value != security_run.workload_value:
            errors.append(
                f"Workload value mismatch: baseline={baseline_run.workload_value}, "
                f"security={security_run.workload_value}"
            )

        if baseline_run.measurement_mode != security_run.measurement_mode:
            errors.append(
                f"Measurement mode mismatch: baseline={baseline_run.measurement_mode}, "
                f"security={security_run.measurement_mode}"
            )

        baseline_duration = baseline_run.duration_seconds or 60.0
        security_duration = security_run.duration_seconds or 60.0
        if baseline_duration != security_duration:
            errors.append(
                f"Duration mismatch: baseline={baseline_duration}, "
                f"security={security_duration}"
            )

        return errors

    def _get_measurement(self, run_id: int) -> EnergyMeasurement:
        measurement = self.measurement_repo.get_latest_by_run(run_id)
        if not measurement:
            raise MarginalEnergyError(f"No energy measurement found for run {run_id}")
        return measurement

    def _get_effectiveness(self, run_id: int) -> Optional[SecurityEffectiveness]:
        return self.effectiveness_repo.get_by_run(run_id)

    def _calculate_marginal(
        self,
        baseline_energy_j: float,
        security_energy_j: float,
        duration_s: float,
        carbon_intensity: Optional[float] = None,
    ) -> dict:
        marginal_energy_j = security_energy_j - baseline_energy_j

        baseline_power = baseline_energy_j / duration_s if duration_s > 0 else 0.0
        security_power = security_energy_j / duration_s if duration_s > 0 else 0.0
        marginal_power = security_power - baseline_power

        baseline_kwh = baseline_energy_j / JOULES_PER_KWH
        security_kwh = security_energy_j / JOULES_PER_KWH
        marginal_kwh = marginal_energy_j / JOULES_PER_KWH

        intensity = carbon_intensity or settings.DEFAULT_CARBON_INTENSITY

        baseline_carbon = calculate_carbon(baseline_kwh, intensity, 0)
        security_carbon = calculate_carbon(security_kwh, intensity, 0)
        marginal_carbon = calculate_carbon(marginal_kwh, intensity, 0)

        return {
            "baseline_energy_joules": baseline_energy_j,
            "security_energy_joules": security_energy_j,
            "marginal_energy_joules": marginal_energy_j,
            "baseline_power_watts": baseline_power,
            "security_power_watts": security_power,
            "marginal_power_watts": marginal_power,
            "baseline_energy_kwh": baseline_kwh,
            "security_energy_kwh": security_kwh,
            "marginal_energy_kwh": marginal_kwh,
            "baseline_carbon_kg": baseline_carbon["gross_co2_kg"],
            "security_carbon_kg": security_carbon["gross_co2_kg"],
            "marginal_carbon_kg": marginal_carbon["gross_co2_kg"],
            "carbon_intensity": intensity,
        }

    def compute_pair(
        self,
        experiment_id: Optional[int],
        baseline_run_id: int,
        security_run_id: int,
        carbon_intensity: Optional[float] = None,
    ) -> EnergyAttribution:
        baseline_run = self.run_repo.get_by_id(baseline_run_id)
        security_run = self.run_repo.get_by_id(security_run_id)

        if not baseline_run:
            raise MarginalEnergyError(f"Baseline run not found: {baseline_run_id}")
        if not security_run:
            raise MarginalEnergyError(f"Security run not found: {security_run_id}")

        if experiment_id is None:
            experiment_id = baseline_run.experiment_id

        errors = self._validate_run_pair(baseline_run, security_run)
        if errors:
            raise MarginalEnergyError("Runs not comparable: " + "; ".join(errors))

        baseline_me = self._get_measurement(baseline_run_id)
        security_me = self._get_measurement(security_run_id)

        duration = baseline_run.duration_seconds or 60.0

        calc = self._calculate_marginal(
            baseline_energy_j=baseline_me.energy_joules,
            security_energy_j=security_me.energy_joules,
            duration_s=duration,
            carbon_intensity=carbon_intensity,
        )

        attribution_data = {
            "experiment_id": experiment_id,
            "baseline_run_id": baseline_run_id,
            "security_run_id": security_run_id,
            "attack_type": baseline_run.attack_type,
            "attack_intensity": baseline_run.attack_intensity,
            "workload_value": baseline_run.workload_value,
            "workload_unit": baseline_run.workload_unit,
            "duration_seconds": duration,
            "measurement_mode": baseline_run.measurement_mode,
            "formula_version": FORMULA_VERSION,
            **calc,
        }

        return self.attribution_repo.create(attribution_data)

    def compute_for_experiment(
        self,
        experiment_uuid: str,
        carbon_intensity: Optional[float] = None,
    ) -> list[EnergyAttribution]:
        experiment = self.experiment_repo.get_by_uuid(experiment_uuid)
        if not experiment:
            raise MarginalEnergyError(f"Experiment not found: {experiment_uuid}")

        runs = self.run_repo.get_by_experiment(experiment.id)

        if len(runs) < 2:
            raise MarginalEnergyError(
                "Experiment needs at least 2 runs for comparison "
                f"(baseline + security). Got {len(runs)}"
            )

        attributions = []
        for security_run in runs[1:]:
            attribution = self.compute_pair(
                experiment_id=experiment.id,
                baseline_run_id=runs[0].id,
                security_run_id=security_run.id,
                carbon_intensity=carbon_intensity,
            )
            attributions.append(attribution)

        return attributions

    def compute_paired_statistics(
        self,
        baseline_run_ids: list[int],
        security_run_ids: list[int],
    ) -> dict:
        if len(baseline_run_ids) != len(security_run_ids):
            raise MarginalEnergyError(
                f"Baseline and security run counts must match: "
                f"{len(baseline_run_ids)} vs {len(security_run_ids)}"
            )

        if not baseline_run_ids:
            raise MarginalEnergyError("No runs provided for statistics")

        marginal_energies = []
        marginal_powers = []
        marginal_carbons = []

        for base_id, sec_id in zip(baseline_run_ids, security_run_ids):
            base_run = self.run_repo.get_by_id(base_id)
            sec_run = self.run_repo.get_by_id(sec_id)
            errors = self._validate_run_pair(base_run, sec_run)
            if errors:
                raise MarginalEnergyError("Runs not comparable: " + "; ".join(errors))

            base_me = self._get_measurement(base_id)
            sec_me = self._get_measurement(sec_id)
            duration = base_run.duration_seconds or 60.0

            calc = self._calculate_marginal(
                baseline_energy_j=base_me.energy_joules,
                security_energy_j=sec_me.energy_joules,
                duration_s=duration,
            )
            marginal_energies.append(calc["marginal_energy_joules"])
            marginal_powers.append(calc["marginal_power_watts"])
            marginal_carbons.append(calc["marginal_carbon_kg"])

        def _stats(values: list[float]) -> dict:
            n = len(values)
            mean_v = sum(values) / n
            sorted_v = sorted(values)
            median_v = sorted_v[n // 2] if n % 2 == 1 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2
            variance = sum((v - mean_v) ** 2 for v in values) / n if n > 1 else 0.0
            std_dev = variance ** 0.5
            return {
                "mean": mean_v,
                "median": median_v,
                "std_dev": std_dev,
                "min": min(values),
                "max": max(values),
                "count": n,
            }

        return {
            "marginal_energy": _stats(marginal_energies),
            "marginal_power": _stats(marginal_powers),
            "marginal_carbon": _stats(marginal_carbons),
            "formula_version": FORMULA_VERSION,
        }

    def get_attribution(self, attribution_id: int) -> Optional[EnergyAttribution]:
        return self.attribution_repo.get_by_id(attribution_id)

    def list_attributions(
        self,
        attack_type: Optional[str] = None,
        attack_intensity: Optional[str] = None,
        measurement_mode: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[EnergyAttribution]:
        return self.attribution_repo.filter_attributions(
            attack_type=attack_type,
            attack_intensity=attack_intensity,
            measurement_mode=measurement_mode,
            offset=offset,
            limit=limit,
        )

    def get_security_effectiveness(self, run_id: int) -> Optional[SecurityEffectiveness]:
        return self._get_effectiveness(run_id)
