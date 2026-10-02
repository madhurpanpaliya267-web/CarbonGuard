from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict
from datetime import datetime


class ExperimentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    experiment_type: str = Field(..., pattern="^(MARGINAL_ENERGY|INTERACTION|DEFENSE_AMPLIFICATION)$")
    attack_type: str = Field(..., min_length=1)
    attack_intensity: str = Field(..., min_length=1)
    attack_workload: Optional[float] = Field(None, ge=0)
    workload_unit: Optional[str] = None
    duration_seconds: int = Field(60, gt=0, le=3600)
    security_controls: List[str] = Field(default_factory=list)
    measurement_provider: str = Field("estimated")
    number_of_trials: int = Field(1, ge=1, le=20)
    random_seed: Optional[int] = None
    carbon_intensity: Optional[float] = Field(None, ge=0)
    renewable_pct: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class ExperimentResponse(BaseModel):
    id: int
    experiment_uuid: str
    name: str
    description: Optional[str] = None
    experiment_type: str
    attack_type: str
    attack_intensity: str
    workload_profile: Optional[str] = None
    security_controls: Optional[str] = None
    measurement_mode: str
    duration_seconds: float
    num_trials: int
    carbon_intensity: Optional[float] = None
    renewable_pct: Optional[float] = None
    software_version: Optional[str] = None
    configuration_version: Optional[str] = None
    random_seed: Optional[int] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ExperimentRunResponse(BaseModel):
    id: int
    run_uuid: str
    experiment_id: int
    trial_number: int
    attack_type: str
    attack_intensity: str
    attack_parameters: Optional[str] = None
    workload_profile: Optional[str] = None
    workload_value: Optional[float] = None
    workload_unit: Optional[str] = None
    security_controls: Optional[str] = None
    control_count: int
    measurement_mode: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class EnergyMeasurementResponse(BaseModel):
    id: int
    run_id: int
    energy_joules: float
    power_watts: Optional[float] = None
    duration_seconds: float
    cpu_usage_pct: Optional[float] = None
    memory_usage_pct: Optional[float] = None
    network_usage_mbps: Optional[float] = None
    source: str
    measurement_mode: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class SecurityEffectivenessResponse(BaseModel):
    id: int
    run_id: int
    detection_rate: Optional[float] = None
    detection_latency_ms: Optional[float] = None
    false_positive_rate: Optional[float] = None
    mitigation_time_ms: Optional[float] = None
    threat_severity: Optional[str] = None
    security_response: Optional[str] = None
    security_score: Optional[float] = None
    controls_active: Optional[str] = None
    controls_config: Optional[str] = None

    model_config = {"from_attributes": True}


class ExperimentSummaryResponse(BaseModel):
    experiment: ExperimentResponse
    runs: List[ExperimentRunResponse]
    measurements: List[EnergyMeasurementResponse]
    security_effects: List[SecurityEffectivenessResponse]


class ExperimentStatusResponse(BaseModel):
    experiment_uuid: str
    status: str
    total_runs: int
    completed_runs: int
    failed_runs: int


class ExperimentListResponse(BaseModel):
    total: int
    items: List[ExperimentResponse]


class MarginalEnergyComputeRequest(BaseModel):
    baseline_run_id: int
    security_run_id: int
    carbon_intensity: Optional[float] = Field(None, ge=0)


class MarginalEnergyResponse(BaseModel):
    id: int
    experiment_id: int
    baseline_run_id: int
    security_run_id: int
    attack_type: str
    attack_intensity: str
    workload_value: Optional[float] = None
    workload_unit: Optional[str] = None
    duration_seconds: Optional[float] = None
    baseline_energy_joules: float
    security_energy_joules: float
    marginal_energy_joules: float
    baseline_power_watts: Optional[float] = None
    security_power_watts: Optional[float] = None
    marginal_power_watts: Optional[float] = None
    baseline_energy_kwh: Optional[float] = None
    security_energy_kwh: Optional[float] = None
    marginal_energy_kwh: Optional[float] = None
    baseline_carbon_kg: Optional[float] = None
    security_carbon_kg: Optional[float] = None
    marginal_carbon_kg: Optional[float] = None
    carbon_intensity: Optional[float] = None
    measurement_mode: str
    formula_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MarginalEnergyListResponse(BaseModel):
    total: int
    items: List[MarginalEnergyResponse]


class PairedStatisticsRequest(BaseModel):
    baseline_run_ids: List[int]
    security_run_ids: List[int]


class StatisticsSummary(BaseModel):
    mean: float
    median: float
    std_dev: float
    min: float
    max: float
    count: int


class PairedStatisticsResponse(BaseModel):
    marginal_energy: StatisticsSummary
    marginal_power: StatisticsSummary
    marginal_carbon: StatisticsSummary
    formula_version: str


class InteractionEffectComputeRequest(BaseModel):
    experiment_id: Optional[int] = None
    control_a: str = Field(..., min_length=1, max_length=50)
    control_b: str = Field(..., min_length=1, max_length=50)
    baseline_run_ids: List[int] = Field(..., min_length=1)
    control_a_run_ids: List[int] = Field(..., min_length=1)
    control_b_run_ids: List[int] = Field(..., min_length=1)
    combined_run_ids: List[int] = Field(..., min_length=1)
    carbon_intensity: Optional[float] = Field(None, ge=0)


class InteractionSecurityEffectivenessResponse(BaseModel):
    baseline: Optional[SecurityEffectivenessResponse] = None
    control_a: Optional[SecurityEffectivenessResponse] = None
    control_b: Optional[SecurityEffectivenessResponse] = None
    combined: Optional[SecurityEffectivenessResponse] = None


class InteractionEffectResponse(BaseModel):
    id: int
    experiment_id: int
    trial_number: int
    baseline_run_id: Optional[int] = None
    control_a_run_id: Optional[int] = None
    control_b_run_id: Optional[int] = None
    combined_run_id: Optional[int] = None
    control_a: str
    control_b: str
    attack_type: Optional[str] = None
    attack_intensity: Optional[str] = None
    workload_value: Optional[float] = None
    workload_unit: Optional[str] = None
    duration_seconds: Optional[float] = None
    energy_baseline: float
    energy_a: float
    energy_b: float
    energy_ab: float
    interaction_effect: float
    interaction_index: Optional[float] = None
    interpretation: Optional[str] = None
    power_baseline: Optional[float] = None
    power_a: Optional[float] = None
    power_b: Optional[float] = None
    power_ab: Optional[float] = None
    interaction_power: Optional[float] = None
    carbon_baseline_kg: Optional[float] = None
    carbon_a_kg: Optional[float] = None
    carbon_b_kg: Optional[float] = None
    carbon_ab_kg: Optional[float] = None
    interaction_carbon_kg: Optional[float] = None
    carbon_intensity: Optional[float] = None
    energy_provider: Optional[str] = None
    measurement_mode: Optional[str] = None
    formula_version: str
    created_at: datetime
    security_effectiveness: Optional[InteractionSecurityEffectivenessResponse] = None

    model_config = {"from_attributes": True}


class InteractionEffectListResponse(BaseModel):
    total: int
    items: List[InteractionEffectResponse]


class InteractionStatisticsResponse(BaseModel):
    interaction_energy: StatisticsSummary
    interaction_power: StatisticsSummary
    interaction_carbon: StatisticsSummary
    formula_version: str


class InteractionEffectComputeResponse(BaseModel):
    total: int
    results: List[InteractionEffectResponse]
    statistics: InteractionStatisticsResponse


class DefenseAmplificationComputeRequest(BaseModel):
    experiment_id: Optional[int] = None
    control_name: str = Field(..., min_length=1, max_length=50)
    baseline_run_ids: List[int] = Field(..., min_length=1)
    defense_run_ids: List[int] = Field(..., min_length=1)
    carbon_intensity: Optional[float] = Field(None, ge=0)


class DefenseAmplificationStatisticsResponse(BaseModel):
    amplification_energy: StatisticsSummary
    amplification_ratio: StatisticsSummary
    power_amplification: StatisticsSummary
    carbon_amplification: StatisticsSummary
    formula_version: str


class DefenseAmplificationResponse(BaseModel):
    id: int
    experiment_id: int
    trial_number: int
    baseline_run_id: Optional[int] = None
    defense_run_id: Optional[int] = None
    control_name: str
    attack_type: str
    attack_intensity: str
    attack_workload: float
    workload_unit: str
    duration_seconds: Optional[float] = None
    energy_attack_only: float
    energy_attack_defense: float
    additional_defense_energy: float
    defense_energy_amplification: float
    power_baseline: Optional[float] = None
    power_defense: Optional[float] = None
    power_amplification: Optional[float] = None
    carbon_baseline_kg: Optional[float] = None
    carbon_defense_kg: Optional[float] = None
    amplification_carbon_kg: Optional[float] = None
    carbon_intensity: Optional[float] = None
    energy_provider: Optional[str] = None
    measurement_mode: Optional[str] = None
    environment_info: Optional[str] = None
    software_version: Optional[str] = None
    configuration_version: Optional[str] = None
    num_paired_trials: int
    statistics: Optional[DefenseAmplificationStatisticsResponse] = None
    formula_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DefenseAmplificationListResponse(BaseModel):
    total: int
    items: List[DefenseAmplificationResponse]


class DefenseAmplificationComputeResponse(BaseModel):
    total: int
    results: List[DefenseAmplificationResponse]
    statistics: DefenseAmplificationStatisticsResponse


class ResearchAnalyticsFilters(BaseModel):
    experiment_id: Optional[int] = None
    attack_type: Optional[str] = Field(None, max_length=50)
    attack_intensity: Optional[str] = Field(None, max_length=20)
    measurement_mode: Optional[str] = Field(None, max_length=20)
    workload_unit: Optional[str] = Field(None, max_length=50)
    energy_provider: Optional[str] = Field(None, max_length=50)
    control_name: Optional[str] = Field(None, max_length=50)
    control_a: Optional[str] = Field(None, max_length=50)
    control_b: Optional[str] = Field(None, max_length=50)


class ResearchAnalyticsRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=30)
    metric: str = Field(..., min_length=1, max_length=60)
    filters: ResearchAnalyticsFilters = ResearchAnalyticsFilters()
    group_by: List[str] = Field(default_factory=list, max_length=5)
    include_confidence_interval: bool = True
    confidence_level: float = Field(0.95, gt=0, lt=1)
    hypothesis_test: Optional[str] = Field(None, max_length=40)
    alternative: str = Field("two-sided", max_length=20)
    significance_level: float = Field(0.05, gt=0, lt=1)


class AnalyticsConfidenceIntervalResponse(BaseModel):
    level: float
    n: int
    status: str
    reason: Optional[str] = None
    lower: Optional[float] = None
    upper: Optional[float] = None
    mean: Optional[float] = None
    standard_error: Optional[float] = None
    degrees_of_freedom: Optional[int] = None
    critical_value: Optional[float] = None
    method: Optional[str] = None
    std_dev_convention: Optional[str] = None


class AnalyticsEffectSizeResponse(BaseModel):
    name: str
    value: Optional[float] = None
    status: str
    reason: Optional[str] = None
    sample_count: int
    convention: str


class AnalyticsHypothesisTestResponse(BaseModel):
    test_id: str
    test_name: str
    null_hypothesis: str
    alternative_hypothesis: str
    status: str
    reason: Optional[str] = None
    statistic: Optional[float] = None
    p_value: Optional[float] = None
    sample_count: int
    excluded_zero_differences: int = 0
    degrees_of_freedom: Optional[int] = None
    significance_level: float
    alternative: str
    reject_null: Optional[bool] = None
    interpretation: str
    method: str
    method_notes: str
    effect_size: Optional[AnalyticsEffectSizeResponse] = None


class AnalyticsGroupResponse(BaseModel):
    group: Dict[str, str]
    n: int
    statistics: StatisticsSummary
    confidence_interval: Optional[AnalyticsConfidenceIntervalResponse] = None
    hypothesis_test: Optional[AnalyticsHypothesisTestResponse] = None
    warnings: List[str] = Field(default_factory=list)


class ResearchAnalyticsResponse(BaseModel):
    analysis_id: str
    analysis_version: str
    source: str
    metric: str
    metric_category: str
    filters: Dict[str, Any]
    group_by: List[str]
    n: int
    statistics: StatisticsSummary
    std_dev_convention: str
    groups: List[AnalyticsGroupResponse] = Field(default_factory=list)
    confidence_interval: Optional[AnalyticsConfidenceIntervalResponse] = None
    hypothesis_test: Optional[AnalyticsHypothesisTestResponse] = None
    paired_differences: Optional[List[float]] = None
    measurement_mode: Optional[str] = None
    energy_provider: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchAnalyticsListResponse(BaseModel):
    total: int
    items: List[ResearchAnalyticsResponse]
