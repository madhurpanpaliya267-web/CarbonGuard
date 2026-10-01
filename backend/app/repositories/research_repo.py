from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.research import (
    Experiment,
    ExperimentRun,
    EnergyMeasurement,
    SecurityEffectiveness,
    ResearchMetric,
    InteractionResult,
    DefenseAmplificationResult,
    EnergyAttribution,
)
from app.repositories.base import BaseRepository


class ExperimentRepository(BaseRepository[Experiment]):
    def __init__(self, db: Session):
        super().__init__(Experiment, db)

    def get_by_uuid(self, experiment_uuid: str) -> Optional[Experiment]:
        query = select(Experiment).where(Experiment.experiment_uuid == experiment_uuid)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_by_type(self, experiment_type: str) -> List[Experiment]:
        query = (
            select(Experiment)
            .where(Experiment.experiment_type == experiment_type)
            .order_by(Experiment.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_status(self, status: str) -> List[Experiment]:
        query = (
            select(Experiment)
            .where(Experiment.status == status)
            .order_by(Experiment.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def filter_experiments(
        self,
        experiment_type: Optional[str] = None,
        attack_type: Optional[str] = None,
        measurement_mode: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Experiment]:
        query = select(Experiment)
        if experiment_type:
            query = query.where(Experiment.experiment_type == experiment_type)
        if attack_type:
            query = query.where(Experiment.attack_type == attack_type)
        if measurement_mode:
            query = query.where(Experiment.measurement_mode == measurement_mode)
        if status:
            query = query.where(Experiment.status == status)
        query = query.order_by(Experiment.created_at.desc()).offset(offset).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())


class ExperimentRunRepository(BaseRepository[ExperimentRun]):
    def __init__(self, db: Session):
        super().__init__(ExperimentRun, db)

    def get_by_experiment(self, experiment_id: int) -> List[ExperimentRun]:
        query = (
            select(ExperimentRun)
            .where(ExperimentRun.experiment_id == experiment_id)
            .order_by(ExperimentRun.trial_number)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_uuid(self, run_uuid: str) -> Optional[ExperimentRun]:
        query = select(ExperimentRun).where(ExperimentRun.run_uuid == run_uuid)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_completed_runs(self, experiment_id: int) -> List[ExperimentRun]:
        query = (
            select(ExperimentRun)
            .where(ExperimentRun.experiment_id == experiment_id)
            .where(ExperimentRun.status == "completed")
            .order_by(ExperimentRun.trial_number)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())


class EnergyMeasurementRepository(BaseRepository[EnergyMeasurement]):
    def __init__(self, db: Session):
        super().__init__(EnergyMeasurement, db)

    def get_by_run(self, run_id: int) -> List[EnergyMeasurement]:
        query = (
            select(EnergyMeasurement)
            .where(EnergyMeasurement.run_id == run_id)
            .order_by(EnergyMeasurement.timestamp)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_latest_by_run(self, run_id: int) -> Optional[EnergyMeasurement]:
        query = (
            select(EnergyMeasurement)
            .where(EnergyMeasurement.run_id == run_id)
            .order_by(EnergyMeasurement.timestamp.desc())
            .limit(1)
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()


class SecurityEffectivenessRepository(BaseRepository[SecurityEffectiveness]):
    def __init__(self, db: Session):
        super().__init__(SecurityEffectiveness, db)

    def get_by_run(self, run_id: int) -> Optional[SecurityEffectiveness]:
        query = select(SecurityEffectiveness).where(SecurityEffectiveness.run_id == run_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()


class ResearchMetricRepository(BaseRepository[ResearchMetric]):
    def __init__(self, db: Session):
        super().__init__(ResearchMetric, db)

    def get_by_run(self, run_id: int) -> List[ResearchMetric]:
        query = (
            select(ResearchMetric)
            .where(ResearchMetric.run_id == run_id)
            .order_by(ResearchMetric.metric_name)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_name(self, metric_name: str, experiment_id: Optional[int] = None) -> List[ResearchMetric]:
        query = select(ResearchMetric).join(ExperimentRun).where(ResearchMetric.metric_name == metric_name)
        if experiment_id:
            query = query.where(ExperimentRun.experiment_id == experiment_id)
        result = self.db.execute(query)
        return list(result.scalars().all())


class InteractionResultRepository(BaseRepository[InteractionResult]):
    def __init__(self, db: Session):
        super().__init__(InteractionResult, db)

    def get_by_experiment(self, experiment_id: int) -> List[InteractionResult]:
        query = (
            select(InteractionResult)
            .where(InteractionResult.experiment_id == experiment_id)
            .order_by(InteractionResult.created_at)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_controls(
        self, control_a: str, control_b: str, attack_type: Optional[str] = None
    ) -> List[InteractionResult]:
        query = select(InteractionResult).where(
            InteractionResult.control_a == control_a,
            InteractionResult.control_b == control_b,
        )
        if attack_type:
            query = query.where(InteractionResult.attack_type == attack_type)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def filter_interactions(
        self,
        attack_type: Optional[str] = None,
        attack_intensity: Optional[str] = None,
        measurement_mode: Optional[str] = None,
        control_a: Optional[str] = None,
        control_b: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[InteractionResult]:
        query = select(InteractionResult)
        if attack_type:
            query = query.where(InteractionResult.attack_type == attack_type)
        if attack_intensity:
            query = query.where(InteractionResult.attack_intensity == attack_intensity)
        if measurement_mode:
            query = query.where(InteractionResult.measurement_mode == measurement_mode)
        if control_a:
            query = query.where(InteractionResult.control_a == control_a)
        if control_b:
            query = query.where(InteractionResult.control_b == control_b)
        query = query.order_by(InteractionResult.created_at.desc()).offset(offset).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())


class DefenseAmplificationResultRepository(BaseRepository[DefenseAmplificationResult]):
    def __init__(self, db: Session):
        super().__init__(DefenseAmplificationResult, db)

    def get_by_experiment(self, experiment_id: int) -> List[DefenseAmplificationResult]:
        query = (
            select(DefenseAmplificationResult)
            .where(DefenseAmplificationResult.experiment_id == experiment_id)
            .order_by(DefenseAmplificationResult.created_at)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_attack_type(self, attack_type: str) -> List[DefenseAmplificationResult]:
        query = (
            select(DefenseAmplificationResult)
            .where(DefenseAmplificationResult.attack_type == attack_type)
            .order_by(DefenseAmplificationResult.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def filter_amplification(
        self,
        attack_type: Optional[str] = None,
        attack_intensity: Optional[str] = None,
        measurement_mode: Optional[str] = None,
        control_name: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[DefenseAmplificationResult]:
        query = select(DefenseAmplificationResult)
        if attack_type:
            query = query.where(DefenseAmplificationResult.attack_type == attack_type)
        if attack_intensity:
            query = query.where(DefenseAmplificationResult.attack_intensity == attack_intensity)
        if measurement_mode:
            query = query.where(DefenseAmplificationResult.measurement_mode == measurement_mode)
        if control_name:
            query = query.where(DefenseAmplificationResult.control_name == control_name)
        query = query.order_by(DefenseAmplificationResult.created_at.desc()).offset(offset).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())


class EnergyAttributionRepository(BaseRepository[EnergyAttribution]):
    def __init__(self, db: Session):
        super().__init__(EnergyAttribution, db)

    def get_by_experiment(self, experiment_id: int) -> List[EnergyAttribution]:
        query = (
            select(EnergyAttribution)
            .where(EnergyAttribution.experiment_id == experiment_id)
            .order_by(EnergyAttribution.created_at)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_attack_type(self, attack_type: str) -> List[EnergyAttribution]:
        query = (
            select(EnergyAttribution)
            .where(EnergyAttribution.attack_type == attack_type)
            .order_by(EnergyAttribution.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def filter_attributions(
        self,
        attack_type: Optional[str] = None,
        attack_intensity: Optional[str] = None,
        measurement_mode: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[EnergyAttribution]:
        query = select(EnergyAttribution)
        if attack_type:
            query = query.where(EnergyAttribution.attack_type == attack_type)
        if attack_intensity:
            query = query.where(EnergyAttribution.attack_intensity == attack_intensity)
        if measurement_mode:
            query = query.where(EnergyAttribution.measurement_mode == measurement_mode)
        query = query.order_by(EnergyAttribution.created_at.desc()).offset(offset).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())
