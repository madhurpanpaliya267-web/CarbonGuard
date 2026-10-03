"""Pydantic response schemas for the Phase 13 end-to-end pipeline run.

Reuses existing schemas (SecurityEventResponse, ThreatResponse,
RiskAssessment) so pipeline entities are not duplicated. Optional sections
carry explicit status/reason fields so degraded runs stay serialisable.
"""
from typing import List, Optional, Union

from pydantic import BaseModel

from app.schemas.security import RiskAssessment, SecurityEventResponse, ThreatResponse


class DefenseControlDetail(BaseModel):
    control_id: str
    display_name: str
    category: str
    description: str
    supported_attack_types: List[str]
    config_parameters: dict
    enabled_by_default: bool


class DefenseDecision(BaseModel):
    status: str
    basis: str
    tier: str
    selected: List[str]
    available: List[str]
    reason: str
    risk_score: Optional[float] = None
    control_details: List[dict]
    activated: bool
    response: str
    recommendation: dict


class EnergySection(BaseModel):
    status: str
    energy_joules: Optional[float] = None
    energy_kwh: Optional[float] = None
    power_watts: Optional[float] = None
    duration_seconds: Optional[float] = None
    measurement_mode: Optional[str] = None
    measurement_source: Optional[str] = None
    provider: Optional[str] = None
    security_controls_active: int
    estimated: Optional[bool] = None
    reason: Optional[str] = None


class CarbonSection(BaseModel):
    status: str
    reason: Optional[str] = None
    energy_kwh: Optional[float] = None
    carbon_intensity: Optional[float] = None
    renewable_pct: Optional[float] = None
    gross_co2_kg: Optional[float] = None
    renewable_offset_kg: Optional[float] = None
    net_co2_kg: Optional[float] = None
    carbon_basis: Optional[str] = None
    measurement_mode: Optional[str] = None
    calculation_breakdown: Optional[str] = None


class ComparisonSection(BaseModel):
    status: str
    reason: Optional[str] = None
    basis: Optional[str] = None
    measurement_mode: Optional[str] = None
    baseline_energy_kwh: Optional[float] = None
    defense_energy_kwh: Optional[float] = None
    energy_difference_kwh: Optional[float] = None
    baseline_carbon_kg: Optional[float] = None
    defense_carbon_kg: Optional[float] = None
    carbon_difference_kg: Optional[float] = None
    direction: Optional[str] = None
    interpretation: Optional[str] = None


class ResearchSection(BaseModel):
    status: str
    reason: Optional[str] = None
    experiment_uuid: Optional[str] = None
    experiment_id: Optional[int] = None
    run_id: Optional[int] = None
    run_uuid: Optional[str] = None
    trial_number: Optional[int] = None
    measurement_id: Optional[int] = None
    security_effectiveness_id: Optional[int] = None
    carbon_metric_id: Optional[int] = None
    recorded_at: Optional[str] = None


class AnalyticsSection(BaseModel):
    status: str
    recorded: bool
    feeds: List[str]
    detail: str


class ProvenanceSection(BaseModel):
    data_classification: str
    simulated_attack: bool
    measurement_mode: Optional[str] = None
    measurement_source: Optional[str] = None
    carbon_basis: Optional[str] = None
    energy_engine: str
    carbon_engine: str
    control_selection: str
    pipeline_version: str
    generated_at: str
    notes: str


class PipelineStage(BaseModel):
    step: str
    status: str
    detail: str


class PipelineWarning(BaseModel):
    stage: str
    reason: str


class OrchestrationRunResponse(BaseModel):
    status: str
    event: Union[SecurityEventResponse, dict]
    attack: dict
    threat: Union[ThreatResponse, dict]
    risk: RiskAssessment
    defense: DefenseDecision
    security_controls: List[str]
    energy: EnergySection
    carbon: CarbonSection
    comparison: ComparisonSection
    research: ResearchSection
    analytics: AnalyticsSection
    provenance: ProvenanceSection
    stages: List[PipelineStage]
    warnings: List[PipelineWarning]
