import uuid as _uuid
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _generate_uuid() -> str:
    return str(_uuid.uuid4())


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_uuid = Column(String(36), unique=True, index=True, nullable=False, default=_generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    experiment_type = Column(String(50), index=True, nullable=False)
    attack_type = Column(String(50), nullable=False)
    attack_intensity = Column(String(20), nullable=False)
    workload_profile = Column(String(100), nullable=True)
    security_controls = Column(Text, nullable=True)
    measurement_mode = Column(String(20), nullable=False, default="ESTIMATED")
    duration_seconds = Column(Float, nullable=False, default=60.0)
    num_trials = Column(Integer, nullable=False, default=1)
    carbon_intensity = Column(Float, nullable=True)
    renewable_pct = Column(Float, nullable=True)
    environment_info = Column(Text, nullable=True)
    software_version = Column(String(50), nullable=True)
    configuration_version = Column(String(50), nullable=True)
    random_seed = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="created", index=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
    interactions = relationship("InteractionResult", back_populates="experiment", cascade="all, delete-orphan")
    amplification_results = relationship("DefenseAmplificationResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_uuid = Column(String(36), unique=True, index=True, nullable=False, default=_generate_uuid)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), index=True, nullable=False)
    trial_number = Column(Integer, nullable=False, default=1)
    attack_type = Column(String(50), nullable=False)
    attack_intensity = Column(String(20), nullable=False)
    attack_parameters = Column(Text, nullable=True)
    workload_profile = Column(String(100), nullable=True)
    workload_value = Column(Float, nullable=True)
    workload_unit = Column(String(50), nullable=True)
    security_controls = Column(Text, nullable=True)
    control_count = Column(Integer, nullable=False, default=0)
    measurement_mode = Column(String(20), nullable=False, default="ESTIMATED")
    start_time = Column(DateTime, nullable=False, default=_utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="running", index=True)
    error_message = Column(Text, nullable=True)

    experiment = relationship("Experiment", back_populates="runs")
    measurements = relationship("EnergyMeasurement", back_populates="run", cascade="all, delete-orphan")
    security_effects = relationship("SecurityEffectiveness", back_populates="run", cascade="all, delete-orphan")
    research_metrics = relationship("ResearchMetric", back_populates="run", cascade="all, delete-orphan")


class EnergyMeasurement(Base):
    __tablename__ = "energy_measurements"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)
    energy_joules = Column(Float, nullable=False)
    power_watts = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=False)
    cpu_usage_pct = Column(Float, nullable=True)
    memory_usage_pct = Column(Float, nullable=True)
    network_usage_mbps = Column(Float, nullable=True)
    source = Column(String(50), nullable=False, default="estimated")
    measurement_mode = Column(String(20), nullable=False, default="ESTIMATED")
    timestamp = Column(DateTime, nullable=False, default=_utcnow, index=True)

    run = relationship("ExperimentRun", back_populates="measurements")


class SecurityEffectiveness(Base):
    __tablename__ = "security_effectiveness"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)
    detection_rate = Column(Float, nullable=True)
    detection_latency_ms = Column(Float, nullable=True)
    false_positive_rate = Column(Float, nullable=True)
    mitigation_time_ms = Column(Float, nullable=True)
    threat_severity = Column(String(20), nullable=True)
    security_response = Column(Text, nullable=True)
    security_score = Column(Float, nullable=True)
    controls_active = Column(Text, nullable=True)
    controls_config = Column(Text, nullable=True)

    run = relationship("ExperimentRun", back_populates="security_effects")


class ResearchMetric(Base):
    __tablename__ = "research_metrics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    formula_version = Column(String(50), nullable=True)
    measurement_mode = Column(String(20), nullable=True)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    run = relationship("ExperimentRun", back_populates="research_metrics")


class InteractionResult(Base):
    __tablename__ = "interaction_results"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), index=True, nullable=False)
    control_a = Column(String(50), nullable=False)
    control_b = Column(String(50), nullable=False)
    energy_baseline = Column(Float, nullable=False)
    energy_a = Column(Float, nullable=False)
    energy_b = Column(Float, nullable=False)
    energy_ab = Column(Float, nullable=False)
    interaction_effect = Column(Float, nullable=False)
    interaction_index = Column(Float, nullable=True)
    interpretation = Column(String(100), nullable=True)
    attack_type = Column(String(50), nullable=True)
    attack_intensity = Column(String(20), nullable=True)
    measurement_mode = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow, index=True)

    # Phase 6: security-control interaction effects
    trial_number = Column(Integer, nullable=False, default=1)
    baseline_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=True)
    control_a_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=True)
    control_b_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=True)
    combined_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=True)

    workload_value = Column(Float, nullable=True)
    workload_unit = Column(String(50), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    power_baseline = Column(Float, nullable=True)
    power_a = Column(Float, nullable=True)
    power_b = Column(Float, nullable=True)
    power_ab = Column(Float, nullable=True)
    interaction_power = Column(Float, nullable=True)

    carbon_baseline_kg = Column(Float, nullable=True)
    carbon_a_kg = Column(Float, nullable=True)
    carbon_b_kg = Column(Float, nullable=True)
    carbon_ab_kg = Column(Float, nullable=True)
    interaction_carbon_kg = Column(Float, nullable=True)
    carbon_intensity = Column(Float, nullable=True)

    energy_provider = Column(String(50), nullable=True)
    formula_version = Column(String(50), nullable=False, default="interaction_effect_v1")

    experiment = relationship("Experiment", back_populates="interactions")


class DefenseAmplificationResult(Base):
    __tablename__ = "defense_amplification_results"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), index=True, nullable=False)
    control_name = Column(String(50), nullable=False)
    attack_type = Column(String(50), nullable=False)
    attack_intensity = Column(String(20), nullable=False)
    attack_workload = Column(Float, nullable=False)
    workload_unit = Column(String(50), nullable=False)
    energy_attack_only = Column(Float, nullable=False)
    energy_attack_defense = Column(Float, nullable=False)
    additional_defense_energy = Column(Float, nullable=False)
    defense_energy_amplification = Column(Float, nullable=False)
    measurement_mode = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow, index=True)

    # Phase 7: defense energy amplification
    trial_number = Column(Integer, nullable=False, default=1)
    baseline_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=True)
    defense_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=True)

    duration_seconds = Column(Float, nullable=True)

    power_baseline = Column(Float, nullable=True)
    power_defense = Column(Float, nullable=True)
    power_amplification = Column(Float, nullable=True)

    carbon_baseline_kg = Column(Float, nullable=True)
    carbon_defense_kg = Column(Float, nullable=True)
    amplification_carbon_kg = Column(Float, nullable=True)
    carbon_intensity = Column(Float, nullable=True)

    energy_provider = Column(String(50), nullable=True)
    environment_info = Column(Text, nullable=True)
    software_version = Column(String(50), nullable=True)
    configuration_version = Column(String(50), nullable=True)

    num_paired_trials = Column(Integer, nullable=False, default=1)
    statistics_json = Column(Text, nullable=True)

    formula_version = Column(String(50), nullable=False, default="defense_energy_amplification_v1")

    experiment = relationship("Experiment", back_populates="amplification_results")


class EnergyAttribution(Base):
    __tablename__ = "energy_attributions"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), index=True, nullable=False)
    baseline_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)
    security_run_id = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)

    attack_type = Column(String(50), nullable=False)
    attack_intensity = Column(String(20), nullable=False)
    workload_value = Column(Float, nullable=True)
    workload_unit = Column(String(50), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    baseline_energy_joules = Column(Float, nullable=False)
    security_energy_joules = Column(Float, nullable=False)
    marginal_energy_joules = Column(Float, nullable=False)

    baseline_power_watts = Column(Float, nullable=True)
    security_power_watts = Column(Float, nullable=True)
    marginal_power_watts = Column(Float, nullable=True)

    baseline_energy_kwh = Column(Float, nullable=True)
    security_energy_kwh = Column(Float, nullable=True)
    marginal_energy_kwh = Column(Float, nullable=True)

    baseline_carbon_kg = Column(Float, nullable=True)
    security_carbon_kg = Column(Float, nullable=True)
    marginal_carbon_kg = Column(Float, nullable=True)

    carbon_intensity = Column(Float, nullable=True)
    measurement_mode = Column(String(20), nullable=False, default="ESTIMATED")
    formula_version = Column(String(50), nullable=False, default="marginal_energy_v1")
    created_at = Column(DateTime, nullable=False, default=_utcnow, index=True)

    experiment = relationship("Experiment")


class ResearchAnalyticsResult(Base):
    """Phase 8: minimal persistence for reproducible research analytics.

    Stores the analysis configuration hash and the derived analytics response.
    Raw experimental observations stay in the Phase 5-7 result tables; this
    table never duplicates measurement data.
    """

    __tablename__ = "research_analytics_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(40), unique=True, index=True, nullable=False)
    analysis_version = Column(String(50), nullable=False, default="research_analytics_v1")
    source = Column(String(30), nullable=False, index=True)
    metric = Column(String(60), nullable=False, index=True)
    request_json = Column(Text, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utcnow, index=True)
