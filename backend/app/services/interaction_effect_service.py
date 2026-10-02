"""
Security-Control Interaction Effects Service.

Research question: How does the combined energy cost of multiple security
controls differ from the energy cost expected from applying those controls
individually?

For two security controls A and B:

    I(A,B) = E_AB - E_A - E_B + E_0

Where:
    E_0  = baseline energy with no security controls
    E_A  = energy with control A only
    E_B  = energy with control B only
    E_AB = energy with both controls A and B

Interaction Index = I(A,B) / E_0  (only when E_0 > 0)

Interpretation (neutral, no benefit/harm labeling):
    I approximately 0  -> approximately additive
    I > 0              -> super-additive
    I < 0              -> sub-additive

All four configurations must be comparable (same attack type, attack
intensity, workload value, workload unit, duration, environment, energy
provider, measurement mode). Incompatible runs are rejected.

Formula version: interaction_effect_v1
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.research import (
    Experiment,
    ExperimentRun,
    EnergyMeasurement,
    SecurityEffectiveness,
    InteractionResult,
)
from app.repositories.research_repo import (
    ExperimentRepository,
    ExperimentRunRepository,
    EnergyMeasurementRepository,
    SecurityEffectivenessRepository,
    InteractionResultRepository,
)
from app.engines.carbon.carbon_calculator import JOULES_PER_KWH, calculate_carbon
from app.engines.security.security_controls import (
    validate_control_id,
    SecurityControlError,
)
from app.schemas.research import (
    InteractionEffectResponse,
    InteractionEffectComputeResponse,
    InteractionEffectListResponse,
    InteractionStatisticsResponse,
    InteractionSecurityEffectivenessResponse,
    SecurityEffectivenessResponse,
    StatisticsSummary,
)

FORMULA_VERSION = "interaction_effect_v1"
ADDITIVE_TOLERANCE = 1e-9

RUN_LABELS = ("baseline", "control_a", "control_b", "combined")


class InteractionEffectError(Exception):
    pass


def calculate_interaction_values(
    energy_baseline: float,
    energy_a: float,
    energy_b: float,
    energy_ab: float,
    duration_s: float,
    carbon_intensity: Optional[float] = None,
) -> dict:
    interaction = energy_ab - energy_a - energy_b + energy_baseline

    if abs(interaction) <= ADDITIVE_TOLERANCE:
        interpretation = "approximately additive"
    elif interaction > 0:
        interpretation = "super-additive"
    else:
        interpretation = "sub-additive"

    interaction_index = (
        interaction / energy_baseline if energy_baseline > 0 else None
    )

    if duration_s > 0:
        power_baseline = energy_baseline / duration_s
        power_a = energy_a / duration_s
        power_b = energy_b / duration_s
        power_ab = energy_ab / duration_s
        interaction_power = power_ab - power_a - power_b + power_baseline
    else:
        power_baseline = power_a = power_b = power_ab = 0.0
        interaction_power = 0.0

    intensity = carbon_intensity or settings.DEFAULT_CARBON_INTENSITY

    carbon_baseline = calculate_carbon(
        energy_baseline / JOULES_PER_KWH, intensity, 0
    )["gross_co2_kg"]
    carbon_a = calculate_carbon(energy_a / JOULES_PER_KWH, intensity, 0)[
        "gross_co2_kg"
    ]
    carbon_b = calculate_carbon(energy_b / JOULES_PER_KWH, intensity, 0)[
        "gross_co2_kg"
    ]
    carbon_ab = calculate_carbon(energy_ab / JOULES_PER_KWH, intensity, 0)[
        "gross_co2_kg"
    ]
    interaction_carbon = carbon_ab - carbon_a - carbon_b + carbon_baseline

    return {
        "interaction_effect": interaction,
        "interaction_index": interaction_index,
        "interpretation": interpretation,
        "power_baseline": power_baseline,
        "power_a": power_a,
        "power_b": power_b,
        "power_ab": power_ab,
        "interaction_power": interaction_power,
        "carbon_baseline_kg": carbon_baseline,
        "carbon_a_kg": carbon_a,
        "carbon_b_kg": carbon_b,
        "carbon_ab_kg": carbon_ab,
        "interaction_carbon_kg": interaction_carbon,
        "carbon_intensity": intensity,
    }


def descriptive_statistics(values: list[float]) -> dict:
    n = len(values)
    mean_v = sum(values) / n
    sorted_v = sorted(values)
    median_v = (
        sorted_v[n // 2] if n % 2 == 1
        else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2
    )
    variance = sum((v - mean_v) ** 2 for v in values) / n if n > 1 else 0.0
    return {
        "mean": mean_v,
        "median": median_v,
        "std_dev": variance ** 0.5,
        "min": min(values),
        "max": max(values),
        "count": n,
    }


class InteractionEffectService:
    def __init__(self, db: Session):
        self.db = db
        self.experiment_repo = ExperimentRepository(db)
        self.run_repo = ExperimentRunRepository(db)
        self.measurement_repo = EnergyMeasurementRepository(db)
        self.effectiveness_repo = SecurityEffectivenessRepository(db)
        self.interaction_repo = InteractionResultRepository(db)

    @staticmethod
    def _normalize_control(control_id: str) -> str:
        return control_id.strip().lower()

    @staticmethod
    def _environment_key(experiment: Optional[Experiment]) -> str:
        if experiment is None:
            return "unknown"
        return "|".join(
            [
                str(experiment.software_version),
                str(experiment.configuration_version),
                str(experiment.environment_info),
            ]
        )

    def _validate_run_quartet(
        self,
        runs: dict[str, ExperimentRun],
        experiments: dict[str, Optional[Experiment]],
    ) -> list[str]:
        errors = []

        b = runs["baseline"]
        a = runs["control_a"]
        cb = runs["control_b"]
        ab = runs["combined"]

        if len({r.attack_type for r in (b, a, cb, ab)}) > 1:
            errors.append(
                "Attack type mismatch: "
                f"baseline={b.attack_type}, control_a={a.attack_type}, "
                f"control_b={cb.attack_type}, combined={ab.attack_type}"
            )

        if len({r.attack_intensity for r in (b, a, cb, ab)}) > 1:
            errors.append(
                "Attack intensity mismatch: "
                f"baseline={b.attack_intensity}, control_a={a.attack_intensity}, "
                f"control_b={cb.attack_intensity}, combined={ab.attack_intensity}"
            )

        if len({r.workload_value for r in (b, a, cb, ab)}) > 1:
            errors.append(
                "Workload value mismatch: "
                f"baseline={b.workload_value}, control_a={a.workload_value}, "
                f"control_b={cb.workload_value}, combined={ab.workload_value}"
            )

        if len({r.workload_unit for r in (b, a, cb, ab)}) > 1:
            errors.append(
                "Workload unit mismatch: "
                f"baseline={b.workload_unit}, control_a={a.workload_unit}, "
                f"control_b={cb.workload_unit}, combined={ab.workload_unit}"
            )

        durations = [r.duration_seconds or 60.0 for r in (b, a, cb, ab)]
        if len(set(durations)) > 1:
            errors.append(
                "Duration mismatch: "
                f"baseline={durations[0]}, control_a={durations[1]}, "
                f"control_b={durations[2]}, combined={durations[3]}"
            )

        if len({r.measurement_mode for r in (b, a, cb, ab)}) > 1:
            errors.append(
                "Measurement mode mismatch: "
                f"baseline={b.measurement_mode}, control_a={a.measurement_mode}, "
                f"control_b={cb.measurement_mode}, combined={ab.measurement_mode}"
            )

        environments = [
            self._environment_key(experiments[label]) for label in RUN_LABELS
        ]
        if len(set(environments)) > 1:
            errors.append(
                "Environment mismatch: "
                f"baseline={environments[0]}, control_a={environments[1]}, "
                f"control_b={environments[2]}, combined={environments[3]}"
            )

        if len({r.trial_number for r in (b, a, cb, ab)}) > 1:
            errors.append(
                "Trial mismatch: "
                f"baseline={b.trial_number}, control_a={a.trial_number}, "
                f"control_b={cb.trial_number}, combined={ab.trial_number}"
            )

        return errors

    def _load_run(self, label: str, run_id: int) -> ExperimentRun:
        run = self.run_repo.get_by_id(run_id)
        if not run:
            raise InteractionEffectError(f"{label} run not found: {run_id}")
        return run

    def _get_measurement(
        self, label: str, run_id: int
    ) -> EnergyMeasurement:
        measurement = self.measurement_repo.get_latest_by_run(run_id)
        if not measurement:
            raise InteractionEffectError(
                f"No energy measurement found for {label} run {run_id}"
            )
        return measurement

    def _validate_provider(self, measurements: dict[str, EnergyMeasurement]):
        sources = [measurements[label].source for label in RUN_LABELS]
        if len(set(sources)) > 1:
            raise InteractionEffectError(
                "Energy provider mismatch: "
                f"baseline={sources[0]}, control_a={sources[1]}, "
                f"control_b={sources[2]}, combined={sources[3]}"
            )

    def _effectiveness_for(
        self, row: InteractionResult
    ) -> InteractionSecurityEffectivenessResponse:
        def _load(run_id: Optional[int]):
            if run_id is None:
                return None
            effect = self.effectiveness_repo.get_by_run(run_id)
            if not effect:
                return None
            return SecurityEffectivenessResponse.model_validate(effect)

        return InteractionSecurityEffectivenessResponse(
            baseline=_load(row.baseline_run_id),
            control_a=_load(row.control_a_run_id),
            control_b=_load(row.control_b_run_id),
            combined=_load(row.combined_run_id),
        )

    def _to_response(
        self,
        row: InteractionResult,
        include_effectiveness: bool = False,
    ) -> InteractionEffectResponse:
        data = {
            column.name: getattr(row, column.name)
            for column in InteractionResult.__table__.columns
        }
        data["security_effectiveness"] = (
            self._effectiveness_for(row) if include_effectiveness else None
        )
        return InteractionEffectResponse(**data)

    def compute_interaction_effects(
        self,
        baseline_run_ids: list[int],
        control_a_run_ids: list[int],
        control_b_run_ids: list[int],
        combined_run_ids: list[int],
        control_a: str,
        control_b: str,
        experiment_id: Optional[int] = None,
        carbon_intensity: Optional[float] = None,
    ) -> InteractionEffectComputeResponse:
        control_a = self._normalize_control(control_a)
        control_b = self._normalize_control(control_b)

        for control in (control_a, control_b):
            try:
                validate_control_id(control)
            except SecurityControlError as e:
                raise InteractionEffectError(str(e))

        if control_a == control_b:
            raise InteractionEffectError(
                "control_a and control_b must be two different controls"
            )

        counts = {
            "baseline": len(baseline_run_ids),
            "control_a": len(control_a_run_ids),
            "control_b": len(control_b_run_ids),
            "combined": len(combined_run_ids),
        }
        if counts["baseline"] == 0:
            raise InteractionEffectError("Missing baseline run ids")
        if counts["control_a"] == 0:
            raise InteractionEffectError("Missing control A run ids")
        if counts["control_b"] == 0:
            raise InteractionEffectError("Missing control B run ids")
        if counts["combined"] == 0:
            raise InteractionEffectError("Missing combined run ids")
        if len(set(counts.values())) > 1:
            raise InteractionEffectError(
                "Run count mismatch: "
                f"baseline={counts['baseline']}, control_a={counts['control_a']}, "
                f"control_b={counts['control_b']}, combined={counts['combined']}"
            )

        if experiment_id is not None:
            experiment = self.experiment_repo.get_by_id(experiment_id)
            if not experiment:
                raise InteractionEffectError(
                    f"Experiment not found: {experiment_id}"
                )

        prepared: list[dict] = []

        for index in range(counts["baseline"]):
            run_ids = {
                "baseline": baseline_run_ids[index],
                "control_a": control_a_run_ids[index],
                "control_b": control_b_run_ids[index],
                "combined": combined_run_ids[index],
            }

            runs = {
                label: self._load_run(label, run_ids[label])
                for label in RUN_LABELS
            }
            experiments = {
                label: self.experiment_repo.get_by_id(runs[label].experiment_id)
                for label in RUN_LABELS
            }

            errors = self._validate_run_quartet(runs, experiments)
            if errors:
                raise InteractionEffectError(
                    "Runs not comparable: " + "; ".join(errors)
                )

            measurements = {
                label: self._get_measurement(label, run_ids[label])
                for label in RUN_LABELS
            }
            self._validate_provider(measurements)

            baseline_run = runs["baseline"]
            duration = baseline_run.duration_seconds or 60.0

            calc = calculate_interaction_values(
                energy_baseline=measurements["baseline"].energy_joules,
                energy_a=measurements["control_a"].energy_joules,
                energy_b=measurements["control_b"].energy_joules,
                energy_ab=measurements["combined"].energy_joules,
                duration_s=duration,
                carbon_intensity=carbon_intensity,
            )

            prepared.append(
                {
                    "experiment_id": (
                        experiment_id
                        if experiment_id is not None
                        else baseline_run.experiment_id
                    ),
                    "trial_number": index + 1,
                    "baseline_run_id": run_ids["baseline"],
                    "control_a_run_id": run_ids["control_a"],
                    "control_b_run_id": run_ids["control_b"],
                    "combined_run_id": run_ids["combined"],
                    "control_a": control_a,
                    "control_b": control_b,
                    "attack_type": baseline_run.attack_type,
                    "attack_intensity": baseline_run.attack_intensity,
                    "workload_value": baseline_run.workload_value,
                    "workload_unit": baseline_run.workload_unit,
                    "duration_seconds": duration,
                    "energy_baseline": measurements["baseline"].energy_joules,
                    "energy_a": measurements["control_a"].energy_joules,
                    "energy_b": measurements["control_b"].energy_joules,
                    "energy_ab": measurements["combined"].energy_joules,
                    **calc,
                    "measurement_mode": baseline_run.measurement_mode,
                    "energy_provider": measurements["baseline"].source,
                    "formula_version": FORMULA_VERSION,
                }
            )

        rows = [
            self.interaction_repo.create(row_data) for row_data in prepared
        ]

        responses = [
            self._to_response(row, include_effectiveness=True)
            for row in rows
        ]

        return InteractionEffectComputeResponse(
            total=len(responses),
            results=responses,
            statistics=self._build_statistics(rows),
        )

    def _build_statistics(
        self, rows: list[InteractionResult]
    ) -> InteractionStatisticsResponse:
        return InteractionStatisticsResponse(
            interaction_energy=StatisticsSummary(
                **descriptive_statistics(
                    [row.interaction_effect for row in rows]
                )
            ),
            interaction_power=StatisticsSummary(
                **descriptive_statistics(
                    [row.interaction_power or 0.0 for row in rows]
                )
            ),
            interaction_carbon=StatisticsSummary(
                **descriptive_statistics(
                    [row.interaction_carbon_kg or 0.0 for row in rows]
                )
            ),
            formula_version=FORMULA_VERSION,
        )

    def get_interaction_effect(
        self, interaction_id: int
    ) -> Optional[InteractionEffectResponse]:
        row = self.interaction_repo.get_by_id(interaction_id)
        if not row:
            return None
        return self._to_response(row, include_effectiveness=True)

    def list_interaction_effects(
        self,
        attack_type: Optional[str] = None,
        attack_intensity: Optional[str] = None,
        measurement_mode: Optional[str] = None,
        control_a: Optional[str] = None,
        control_b: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> InteractionEffectListResponse:
        rows = self.interaction_repo.filter_interactions(
            attack_type=attack_type,
            attack_intensity=attack_intensity,
            measurement_mode=measurement_mode,
            control_a=control_a,
            control_b=control_b,
            offset=offset,
            limit=limit,
        )
        return InteractionEffectListResponse(
            total=len(rows),
            items=[
                self._to_response(row, include_effectiveness=False)
                for row in rows
            ],
        )
