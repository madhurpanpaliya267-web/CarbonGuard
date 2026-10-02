"""
Research dataset export.

Builds CSV and JSON exports exclusively from already-persisted research
records. Rows are produced from Pydantic response DTOs, so no SQLAlchemy ORM
object is ever serialised into an export. An empty research store produces an
empty export: a CSV header row with no data rows, and JSON lists that are
empty rather than fabricated.
"""
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Type, Union

from sqlalchemy.orm import Session

from app.repositories.research_repo import (
    DefenseAmplificationResultRepository,
    EnergyAttributionRepository,
    ExperimentRepository,
    InteractionResultRepository,
)
from app.schemas.research import (
    DefenseAmplificationResponse,
    ExperimentResponse,
    InteractionEffectResponse,
    MarginalEnergyResponse,
    ResearchExportResponse,
)

CsvRow = Dict[str, object]
ResearchDto = Union[
    ExperimentResponse,
    MarginalEnergyResponse,
    InteractionEffectResponse,
    DefenseAmplificationResponse,
]

EXPORT_DATASETS = (
    "experiments",
    "marginal_energy",
    "interaction_effects",
    "defense_amplification",
)

CSV_COLUMNS: Dict[str, List[str]] = {
    "experiments": [
        "id",
        "experiment_uuid",
        "name",
        "experiment_type",
        "attack_type",
        "attack_intensity",
        "security_controls",
        "measurement_mode",
        "duration_seconds",
        "num_trials",
        "status",
        "created_at",
        "completed_at",
    ],
    "marginal_energy": [
        "id",
        "experiment_id",
        "attack_type",
        "attack_intensity",
        "workload_value",
        "workload_unit",
        "duration_seconds",
        "baseline_energy_joules",
        "security_energy_joules",
        "marginal_energy_joules",
        "baseline_power_watts",
        "security_power_watts",
        "marginal_power_watts",
        "marginal_energy_kwh",
        "marginal_carbon_kg",
        "carbon_intensity",
        "measurement_mode",
        "formula_version",
        "created_at",
    ],
    "interaction_effects": [
        "id",
        "experiment_id",
        "trial_number",
        "control_a",
        "control_b",
        "attack_type",
        "attack_intensity",
        "workload_value",
        "workload_unit",
        "duration_seconds",
        "energy_baseline",
        "energy_a",
        "energy_b",
        "energy_ab",
        "interaction_effect",
        "interaction_index",
        "interaction_carbon_kg",
        "carbon_intensity",
        "measurement_mode",
        "formula_version",
        "created_at",
    ],
    "defense_amplification": [
        "id",
        "experiment_id",
        "trial_number",
        "control_name",
        "attack_type",
        "attack_intensity",
        "attack_workload",
        "workload_unit",
        "duration_seconds",
        "energy_attack_only",
        "energy_attack_defense",
        "additional_defense_energy",
        "defense_energy_amplification",
        "power_amplification",
        "amplification_carbon_kg",
        "carbon_intensity",
        "measurement_mode",
        "num_paired_trials",
        "formula_version",
        "created_at",
    ],
}

DTO_BY_DATASET: Dict[str, Type[ResearchDto]] = {
    "experiments": ExperimentResponse,
    "marginal_energy": MarginalEnergyResponse,
    "interaction_effects": InteractionEffectResponse,
    "defense_amplification": DefenseAmplificationResponse,
}


class ResearchExportError(Exception):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ResearchExportService:
    def __init__(self, db: Session):
        self.db = db
        self.experiment_repo = ExperimentRepository(db)
        self.attribution_repo = EnergyAttributionRepository(db)
        self.interaction_repo = InteractionResultRepository(db)
        self.amplification_repo = DefenseAmplificationResultRepository(db)

    @staticmethod
    def validate_dataset(dataset: str) -> str:
        if dataset not in CSV_COLUMNS:
            raise ResearchExportError(
                f"Unsupported export dataset: {dataset}. "
                f"Valid datasets: {', '.join(EXPORT_DATASETS)}"
            )
        return dataset

    def _dtos(self, dataset: str) -> List[ResearchDto]:
        if dataset == "experiments":
            source = self.experiment_repo.list_all()
        elif dataset == "marginal_energy":
            source = self.attribution_repo.list_all()
        elif dataset == "interaction_effects":
            source = self.interaction_repo.list_all()
        else:
            source = self.amplification_repo.list_all()
        response_model = DTO_BY_DATASET[dataset]
        return [response_model.model_validate(row) for row in source]

    def export_json(self) -> ResearchExportResponse:
        datasets = {
            name: self._dtos(name)
            for name in EXPORT_DATASETS
        }
        return ResearchExportResponse(
            exported_at=_utcnow(),
            record_counts={
                name: len(records) for name, records in datasets.items()
            },
            experiments=datasets["experiments"],
            marginal_energy=datasets["marginal_energy"],
            interaction_effects=datasets["interaction_effects"],
            defense_amplification=datasets["defense_amplification"],
        )

    def export_csv(self, dataset: str) -> Tuple[List[str], List[CsvRow]]:
        self.validate_dataset(dataset)
        columns = CSV_COLUMNS[dataset]
        rows: List[CsvRow] = []
        for dto in self._dtos(dataset):
            payload = dto.model_dump(mode="json")
            rows.append({column: payload.get(column) for column in columns})
        return columns, rows
