from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.research_service import (
    ResearchExperimentService,
    ExperimentError,
)
from app.services.marginal_energy_service import (
    MarginalEnergyService,
    MarginalEnergyError,
)
from app.services.interaction_effect_service import (
    InteractionEffectService,
    InteractionEffectError,
)
from app.services.defense_energy_amplification_service import (
    DefenseEnergyAmplificationService,
    DefenseEnergyAmplificationError,
)
from app.services.research_analytics_service import (
    ResearchAnalyticsService,
    AnalyticsValidationError,
    AnalyticsInsufficientDataError,
)
from app.schemas.research import (
    ExperimentCreateRequest,
    ExperimentResponse,
    ExperimentRunResponse,
    ExperimentSummaryResponse,
    ExperimentStatusResponse,
    ExperimentListResponse,
    EnergyMeasurementResponse,
    SecurityEffectivenessResponse,
    MarginalEnergyComputeRequest,
    MarginalEnergyResponse,
    MarginalEnergyListResponse,
    PairedStatisticsRequest,
    PairedStatisticsResponse,
    InteractionEffectComputeRequest,
    InteractionEffectComputeResponse,
    InteractionEffectResponse,
    InteractionEffectListResponse,
    DefenseAmplificationComputeRequest,
    DefenseAmplificationComputeResponse,
    DefenseAmplificationResponse,
    DefenseAmplificationListResponse,
    ResearchAnalyticsRequest,
    ResearchAnalyticsResponse,
    ResearchAnalyticsListResponse,
)

router = APIRouter()


@router.post("/experiments", response_model=ExperimentResponse, status_code=201)
def create_experiment(request: ExperimentCreateRequest, db: Session = Depends(get_db)):
    service = ResearchExperimentService(db)
    try:
        config = request.model_dump()
        experiment = service.create_experiment(config)
        return experiment
    except ExperimentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_uuid}/execute", response_model=ExperimentResponse)
def execute_experiment(experiment_uuid: str, db: Session = Depends(get_db)):
    service = ResearchExperimentService(db)
    try:
        experiment = service.execute_experiment(experiment_uuid)
        return experiment
    except ExperimentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments", response_model=ExperimentListResponse)
def list_experiments(
    experiment_type: str = None,
    status: str = None,
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    service = ResearchExperimentService(db)
    experiments = service.list_experiments(
        experiment_type=experiment_type,
        status=status,
        offset=offset,
        limit=limit,
    )
    return ExperimentListResponse(
        total=len(experiments),
        items=[ExperimentResponse.model_validate(e) for e in experiments],
    )


@router.get("/experiments/{experiment_uuid}", response_model=ExperimentResponse)
def get_experiment(experiment_uuid: str, db: Session = Depends(get_db)):
    service = ResearchExperimentService(db)
    experiment = service.get_experiment(experiment_uuid)
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_uuid}")
    return experiment


@router.get("/experiments/{experiment_uuid}/status", response_model=ExperimentStatusResponse)
def get_experiment_status(experiment_uuid: str, db: Session = Depends(get_db)):
    service = ResearchExperimentService(db)
    try:
        return service.get_experiment_status(experiment_uuid)
    except ExperimentError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/experiments/{experiment_uuid}/runs")
def get_experiment_runs(experiment_uuid: str, db: Session = Depends(get_db)):
    service = ResearchExperimentService(db)
    try:
        runs = service.get_experiment_runs(experiment_uuid)
        return {
            "total": len(runs),
            "items": [ExperimentRunResponse.model_validate(r) for r in runs],
        }
    except ExperimentError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/experiments/{experiment_uuid}/summary")
def get_experiment_summary(experiment_uuid: str, db: Session = Depends(get_db)):
    service = ResearchExperimentService(db)
    try:
        summary = service.get_experiment_summary(experiment_uuid)
        return {
            "experiment": ExperimentResponse.model_validate(summary["experiment"]),
            "runs": [ExperimentRunResponse.model_validate(r) for r in summary["runs"]],
            "measurements": [EnergyMeasurementResponse.model_validate(m) for m in summary["measurements"]],
            "security_effects": [SecurityEffectivenessResponse.model_validate(s) for s in summary["security_effects"]],
        }
    except ExperimentError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/attacks")
def list_attack_types():
    from app.engines.security.attack_profiles import list_attack_profiles
    return {"attacks": list_attack_profiles()}


@router.get("/controls")
def list_security_controls():
    from app.engines.security.security_controls import list_controls
    return {"controls": list_controls()}


@router.post("/marginal-energy", response_model=MarginalEnergyResponse, status_code=201)
def compute_marginal_energy(request: MarginalEnergyComputeRequest, db: Session = Depends(get_db)):
    service = MarginalEnergyService(db)
    try:
        result = service.compute_pair(
            experiment_id=None,
            baseline_run_id=request.baseline_run_id,
            security_run_id=request.security_run_id,
            carbon_intensity=request.carbon_intensity,
        )
        return result
    except MarginalEnergyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/marginal-energy", response_model=MarginalEnergyListResponse)
def list_marginal_energy(
    attack_type: str = None,
    attack_intensity: str = None,
    measurement_mode: str = None,
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    service = MarginalEnergyService(db)
    attributions = service.list_attributions(
        attack_type=attack_type,
        attack_intensity=attack_intensity,
        measurement_mode=measurement_mode,
        offset=offset,
        limit=limit,
    )
    return MarginalEnergyListResponse(
        total=len(attributions),
        items=[MarginalEnergyResponse.model_validate(a) for a in attributions],
    )


@router.get("/marginal-energy/{attribution_id}", response_model=MarginalEnergyResponse)
def get_marginal_energy(attribution_id: int, db: Session = Depends(get_db)):
    service = MarginalEnergyService(db)
    attribution = service.get_attribution(attribution_id)
    if not attribution:
        raise HTTPException(status_code=404, detail=f"Attribution not found: {attribution_id}")
    return attribution


@router.post("/marginal-energy/statistics", response_model=PairedStatisticsResponse)
def compute_paired_statistics(request: PairedStatisticsRequest, db: Session = Depends(get_db)):
    service = MarginalEnergyService(db)
    try:
        result = service.compute_paired_statistics(
            baseline_run_ids=request.baseline_run_ids,
            security_run_ids=request.security_run_ids,
        )
        return result
    except MarginalEnergyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_uuid}/marginal-energy")
def compute_experiment_marginal_energy(
    experiment_uuid: str,
    carbon_intensity: float = None,
    db: Session = Depends(get_db),
):
    service = MarginalEnergyService(db)
    try:
        attributions = service.compute_for_experiment(
            experiment_uuid=experiment_uuid,
            carbon_intensity=carbon_intensity,
        )
        return {
            "total": len(attributions),
            "items": [MarginalEnergyResponse.model_validate(a) for a in attributions],
        }
    except MarginalEnergyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/interaction-effects",
    response_model=InteractionEffectComputeResponse,
    status_code=201,
)
def compute_interaction_effects(
    request: InteractionEffectComputeRequest,
    db: Session = Depends(get_db),
):
    service = InteractionEffectService(db)
    try:
        return service.compute_interaction_effects(
            baseline_run_ids=request.baseline_run_ids,
            control_a_run_ids=request.control_a_run_ids,
            control_b_run_ids=request.control_b_run_ids,
            combined_run_ids=request.combined_run_ids,
            control_a=request.control_a,
            control_b=request.control_b,
            experiment_id=request.experiment_id,
            carbon_intensity=request.carbon_intensity,
        )
    except InteractionEffectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/interaction-effects", response_model=InteractionEffectListResponse)
def list_interaction_effects(
    attack_type: str = None,
    attack_intensity: str = None,
    measurement_mode: str = None,
    control_a: str = None,
    control_b: str = None,
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    service = InteractionEffectService(db)
    return service.list_interaction_effects(
        attack_type=attack_type,
        attack_intensity=attack_intensity,
        measurement_mode=measurement_mode,
        control_a=control_a,
        control_b=control_b,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/interaction-effects/{interaction_id}",
    response_model=InteractionEffectResponse,
)
def get_interaction_effect(interaction_id: int, db: Session = Depends(get_db)):
    service = InteractionEffectService(db)
    response = service.get_interaction_effect(interaction_id)
    if not response:
        raise HTTPException(
            status_code=404,
            detail=f"Interaction effect not found: {interaction_id}",
        )
    return response


@router.post(
    "/defense-energy-amplification",
    response_model=DefenseAmplificationComputeResponse,
    status_code=201,
)
def compute_defense_energy_amplification(
    request: DefenseAmplificationComputeRequest,
    db: Session = Depends(get_db),
):
    service = DefenseEnergyAmplificationService(db)
    try:
        return service.compute_amplification(
            baseline_run_ids=request.baseline_run_ids,
            defense_run_ids=request.defense_run_ids,
            control_name=request.control_name,
            experiment_id=request.experiment_id,
            carbon_intensity=request.carbon_intensity,
        )
    except DefenseEnergyAmplificationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/defense-energy-amplification",
    response_model=DefenseAmplificationListResponse,
)
def list_defense_energy_amplification(
    attack_type: str = None,
    attack_intensity: str = None,
    measurement_mode: str = None,
    control_name: str = None,
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    service = DefenseEnergyAmplificationService(db)
    return service.list_amplification(
        attack_type=attack_type,
        attack_intensity=attack_intensity,
        measurement_mode=measurement_mode,
        control_name=control_name,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/defense-energy-amplification/{amplification_id}",
    response_model=DefenseAmplificationResponse,
)
def get_defense_energy_amplification(
    amplification_id: int, db: Session = Depends(get_db)
):
    service = DefenseEnergyAmplificationService(db)
    response = service.get_amplification(amplification_id)
    if not response:
        raise HTTPException(
            status_code=404,
            detail=f"Defense amplification not found: {amplification_id}",
        )
    return response


@router.post(
    "/analytics",
    response_model=ResearchAnalyticsResponse,
    status_code=201,
)
def compute_research_analytics(
    request: ResearchAnalyticsRequest, db: Session = Depends(get_db)
):
    service = ResearchAnalyticsService(db)
    try:
        return service.analyze(request)
    except AnalyticsValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnalyticsInsufficientDataError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics", response_model=ResearchAnalyticsListResponse)
def list_research_analytics(
    source: str = None,
    metric: str = None,
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    service = ResearchAnalyticsService(db)
    return service.list_analyses(
        source=source, metric=metric, offset=offset, limit=limit
    )


@router.get(
    "/analytics/{analysis_id}",
    response_model=ResearchAnalyticsResponse,
)
def get_research_analytics(analysis_id: str, db: Session = Depends(get_db)):
    service = ResearchAnalyticsService(db)
    response = service.get_analysis(analysis_id)
    if not response:
        raise HTTPException(
            status_code=404,
            detail=f"Analytics result not found: {analysis_id}",
        )
    return response
