"""
Research summary and descriptive metrics reporting.

Aggregates already-persisted research records. This module never computes,
re-computes or modifies a Phase 5-7 formula and never synthesises an
observation: with an empty research store the summary reports zero counts and
the metrics report ``status="unavailable"`` with null statistics.

Descriptive statistics only. Statistical significance, confidence intervals
and hypothesis tests belong exclusively to the Phase 8 analytics service.
"""
import json
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.engines.analytics.statistics import (
    POPULATION_STD_CONVENTION,
    descriptive_statistics,
)
from app.models.research import (
    DefenseAmplificationResult,
    EnergyAttribution,
    EnergyMeasurement,
    Experiment,
    InteractionResult,
)
from app.repositories.research_repo import (
    DefenseAmplificationResultRepository,
    EnergyAttributionRepository,
    EnergyMeasurementRepository,
    ExperimentRepository,
    ExperimentRunRepository,
    InteractionResultRepository,
)
from app.schemas.research import (
    ResearchMetricBlock,
    ResearchMetricsResponse,
    ResearchSummaryResponse,
    StatisticsSummary,
)

ESTIMATED_MODE = "ESTIMATED"
MEASURED_MODE = "MEASURED"


class ResearchSummaryService:
    def __init__(self, db: Session):
        self.db = db
        self.experiment_repo = ExperimentRepository(db)
        self.run_repo = ExperimentRunRepository(db)
        self.measurement_repo = EnergyMeasurementRepository(db)
        self.attribution_repo = EnergyAttributionRepository(db)
        self.interaction_repo = InteractionResultRepository(db)
        self.amplification_repo = DefenseAmplificationResultRepository(db)

    @staticmethod
    def _parse_controls(payload: Optional[str]) -> List[str]:
        if not payload:
            return []
        try:
            parsed = json.loads(payload)
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        return [str(control) for control in parsed if str(control).strip()]

    def get_summary(self) -> ResearchSummaryResponse:
        measurement_counts = self.measurement_repo.count_by(
            EnergyMeasurement.measurement_mode
        )

        controls = set()
        for payload in self.experiment_repo.column_values(
            Experiment.security_controls
        ):
            controls.update(self._parse_controls(payload))

        carbon_observations = (
            self.attribution_repo.count_where_not_null(
                EnergyAttribution.marginal_carbon_kg
            )
            + self.interaction_repo.count_where_not_null(
                InteractionResult.interaction_carbon_kg
            )
            + self.amplification_repo.count_where_not_null(
                DefenseAmplificationResult.amplification_carbon_kg
            )
        )

        return ResearchSummaryResponse(
            total_experiments=self.experiment_repo.count(),
            total_trials=self.run_repo.count(),
            attack_types=self.experiment_repo.distinct_values(
                Experiment.attack_type
            ),
            security_controls=sorted(controls),
            measurement_modes=sorted(measurement_counts),
            estimated_trials=measurement_counts.get(ESTIMATED_MODE, 0),
            measured_trials=measurement_counts.get(MEASURED_MODE, 0),
            marginal_energy_observations=self.attribution_repo.count(),
            interaction_observations=self.interaction_repo.count(),
            amplification_observations=self.amplification_repo.count(),
            carbon_observations=carbon_observations,
        )

    @staticmethod
    def _block(
        values: List[float],
        unit: str,
        empty_reason: str,
    ) -> ResearchMetricBlock:
        numeric = [
            float(value)
            for value in values
            if value is not None and math.isfinite(float(value))
        ]
        if not numeric:
            return ResearchMetricBlock(
                status="unavailable",
                reason=empty_reason,
                unit=unit,
                observation_count=0,
                statistics=None,
            )

        statistics = descriptive_statistics(numeric)
        return ResearchMetricBlock(
            status="available",
            reason=None,
            unit=unit,
            observation_count=len(numeric),
            statistics=StatisticsSummary(
                mean=statistics["mean"],
                median=statistics["median"],
                std_dev=statistics["std_dev"],
                min=statistics["min"],
                max=statistics["max"],
                count=statistics["count"],
            ),
        )

    def get_metrics(self) -> ResearchMetricsResponse:
        return ResearchMetricsResponse(
            marginal_energy=self._block(
                self.attribution_repo.column_values(
                    EnergyAttribution.marginal_energy_joules,
                    exclude_null=True,
                ),
                unit="joules",
                empty_reason="No marginal energy observations recorded yet",
            ),
            marginal_power=self._block(
                self.attribution_repo.column_values(
                    EnergyAttribution.marginal_power_watts,
                    exclude_null=True,
                ),
                unit="watts",
                empty_reason="No marginal power observations recorded yet",
            ),
            marginal_carbon=self._block(
                self.attribution_repo.column_values(
                    EnergyAttribution.marginal_carbon_kg,
                    exclude_null=True,
                ),
                unit="kg_co2",
                empty_reason="No marginal carbon observations recorded yet",
            ),
            interaction_effect=self._block(
                self.interaction_repo.column_values(
                    InteractionResult.interaction_effect,
                    exclude_null=True,
                ),
                unit="joules",
                empty_reason="No interaction effect observations recorded yet",
            ),
            amplification_energy=self._block(
                self.amplification_repo.column_values(
                    DefenseAmplificationResult.additional_defense_energy,
                    exclude_null=True,
                ),
                unit="joules",
                empty_reason=(
                    "No defense energy amplification observations recorded yet"
                ),
            ),
            amplification_ratio=self._block(
                self.amplification_repo.column_values(
                    DefenseAmplificationResult.defense_energy_amplification,
                    exclude_null=True,
                ),
                unit="joules_per_workload_unit",
                empty_reason=(
                    "No defense energy amplification ratios recorded yet"
                ),
            ),
            std_dev_convention=POPULATION_STD_CONVENTION,
        )
