"""Phase 8: research analytics and statistical analysis.

Turns persisted Phase 5-7 experiment results into reproducible descriptive and
inferential statistics. The service reads existing result tables only; it
never invents measurements and never replaces the Phase 5-7 formulas.

Integrity rules enforced here:

- Data validation failures raise ``AnalyticsValidationError`` (HTTP 400).
- An empty selection raises ``AnalyticsInsufficientDataError`` (HTTP 400).
- Small-but-nonempty samples return structured results with warnings and
  omitted inferential components instead of fabricated numbers.
- Statistical results are reported descriptively; no statement that a
  configuration is "better", "optimal" or "more efficient" is ever produced.
- Identical persisted inputs plus identical analysis configuration produce
  identical output (deterministic ordering, no sampling, no randomness).
"""

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.engines.carbon.carbon_calculator import calculate_carbon_per_workload
from app.engines.analytics.statistics import (
    POPULATION_STD_CONVENTION,
    SAMPLE_STD_CONVENTION,
    cohens_dz,
    confidence_interval_t,
    descriptive_statistics,
    paired_t_test,
    rank_biserial,
    wilcoxon_signed_rank,
)
from app.repositories.research_repo import (
    DefenseAmplificationResultRepository,
    EnergyAttributionRepository,
    InteractionResultRepository,
    ResearchAnalyticsResultRepository,
)
from app.schemas.research import (
    AnalyticsConfidenceIntervalResponse,
    AnalyticsEffectSizeResponse,
    AnalyticsGroupResponse,
    AnalyticsHypothesisTestResponse,
    ResearchAnalyticsFilters,
    ResearchAnalyticsListResponse,
    ResearchAnalyticsRequest,
    ResearchAnalyticsResponse,
    StatisticsSummary,
)

ANALYSIS_VERSION = "research_analytics_v1"
MAX_OBSERVATIONS = 10_000

SOURCES = ("marginal", "interaction", "amplification")
HYPOTHESIS_TESTS = ("paired_t", "wilcoxon_signed_rank")
ALTERNATIVES = ("two-sided", "greater", "less")

CATEGORY_DIFFERENCE = "difference"
CATEGORY_RATIO = "ratio"
CATEGORY_LEVEL = "level"
TESTABLE_CATEGORIES = (CATEGORY_DIFFERENCE, CATEGORY_RATIO)

_CONTEXT_DIMENSIONS = ("attack_type", "attack_intensity")


class AnalyticsValidationError(Exception):
    """Selected data is invalid or not comparable for the requested analysis."""


class AnalyticsInsufficientDataError(Exception):
    """No persisted observations matched the requested analysis."""


@dataclass(frozen=True)
class _MetricSpec:
    category: str
    per_workload: bool = False
    workload_dependent: bool = False
    # Derived carbon-per-workload metrics are computed at read time instead of
    # being persisted: value = carbon_field / workload_field (same conversion
    # rules as app.engines.carbon.carbon_calculator.calculate_carbon_per_workload).
    carbon_field: Optional[str] = None
    workload_field: Optional[str] = None


def _difference() -> _MetricSpec:
    return _MetricSpec(CATEGORY_DIFFERENCE)


def _level() -> _MetricSpec:
    return _MetricSpec(CATEGORY_LEVEL)


_METRICS: Dict[str, Dict[str, _MetricSpec]] = {
    "marginal": {
        "marginal_energy_joules": _difference(),
        "marginal_power_watts": _difference(),
        "marginal_carbon_kg": _difference(),
        "baseline_energy_joules": _level(),
        "security_energy_joules": _level(),
        "baseline_power_watts": _level(),
        "security_power_watts": _level(),
        "baseline_carbon_kg": _level(),
        "security_carbon_kg": _level(),
        "baseline_energy_kwh": _level(),
        "security_energy_kwh": _level(),
        "marginal_energy_kwh": _level(),
        "workload_value": _MetricSpec(CATEGORY_LEVEL, workload_dependent=True),
        "duration_seconds": _level(),
        "carbon_intensity": _level(),
        "marginal_carbon_per_workload": _MetricSpec(
            CATEGORY_RATIO,
            workload_dependent=True,
            carbon_field="marginal_carbon_kg",
            workload_field="workload_value",
        ),
    },
    "interaction": {
        "interaction_effect": _difference(),
        "interaction_power": _difference(),
        "interaction_carbon_kg": _difference(),
        "interaction_index": _MetricSpec(CATEGORY_RATIO),
        "energy_baseline": _level(),
        "energy_a": _level(),
        "energy_b": _level(),
        "energy_ab": _level(),
        "power_baseline": _level(),
        "power_a": _level(),
        "power_b": _level(),
        "power_ab": _level(),
        "carbon_baseline_kg": _level(),
        "carbon_a_kg": _level(),
        "carbon_b_kg": _level(),
        "carbon_ab_kg": _level(),
        "workload_value": _MetricSpec(CATEGORY_LEVEL, workload_dependent=True),
        "duration_seconds": _level(),
        "carbon_intensity": _level(),
        "interaction_carbon_per_workload": _MetricSpec(
            CATEGORY_RATIO,
            workload_dependent=True,
            carbon_field="interaction_carbon_kg",
            workload_field="workload_value",
        ),
    },
    "amplification": {
        "additional_defense_energy": _difference(),
        "power_amplification": _difference(),
        "amplification_carbon_kg": _difference(),
        "defense_energy_amplification": _MetricSpec(
            CATEGORY_RATIO, per_workload=True, workload_dependent=True
        ),
        "energy_attack_only": _level(),
        "energy_attack_defense": _level(),
        "power_baseline": _level(),
        "power_defense": _level(),
        "carbon_baseline_kg": _level(),
        "carbon_defense_kg": _level(),
        "attack_workload": _MetricSpec(CATEGORY_LEVEL, workload_dependent=True),
        "duration_seconds": _level(),
        "carbon_intensity": _level(),
        "defense_carbon_per_workload": _MetricSpec(
            CATEGORY_RATIO,
            workload_dependent=True,
            carbon_field="amplification_carbon_kg",
            workload_field="attack_workload",
        ),
    },
}

_COMMON_GROUP_DIMENSIONS = (
    "attack_type",
    "attack_intensity",
    "workload_unit",
    "duration_seconds",
    "measurement_mode",
)

_GROUP_DIMENSIONS: Dict[str, Tuple[str, ...]] = {
    "marginal": _COMMON_GROUP_DIMENSIONS,
    "interaction": _COMMON_GROUP_DIMENSIONS + ("control_a", "control_b", "energy_provider"),
    "amplification": _COMMON_GROUP_DIMENSIONS + ("control_name", "energy_provider"),
}

_FILTER_FIELDS: Dict[str, Tuple[str, ...]] = {
    "marginal": (
        "experiment_id",
        "attack_type",
        "attack_intensity",
        "measurement_mode",
        "workload_unit",
    ),
    "interaction": (
        "experiment_id",
        "attack_type",
        "attack_intensity",
        "measurement_mode",
        "workload_unit",
        "energy_provider",
        "control_a",
        "control_b",
    ),
    "amplification": (
        "experiment_id",
        "attack_type",
        "attack_intensity",
        "measurement_mode",
        "workload_unit",
        "energy_provider",
        "control_name",
    ),
}

_DUPLICATE_KEYS: Dict[str, Tuple[str, ...]] = {
    "marginal": ("baseline_run_id", "security_run_id"),
    "interaction": ("experiment_id", "trial_number", "control_a", "control_b"),
    "amplification": ("experiment_id", "trial_number", "control_name"),
}

_STATIC_LIMITATIONS = [
    "Statistical analysis does not convert estimated energy into measured energy.",
    "Attack workloads come from safe synthetic simulation; results do not describe real attack behavior.",
    "Statistical quantities are descriptive or inferential measures only; they do not establish causality, optimality, or universal generalization.",
    "Raw experimental observations are stored in the Phase 5-7 result tables; analytics rows contain derived statistics only.",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _summary(engine_result: dict) -> StatisticsSummary:
    return StatisticsSummary(
        mean=engine_result["mean"],
        median=engine_result["median"],
        std_dev=engine_result["std_dev"],
        min=engine_result["min"],
        max=engine_result["max"],
        count=engine_result["count"],
    )


def _group_value(row: Any, dimension: str) -> str:
    value = getattr(row, dimension, None)
    if value is None:
        return "unknown"
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if value.is_integer():
            return str(int(value))
        return str(value)
    return str(value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class ResearchAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.attribution_repo = EnergyAttributionRepository(db)
        self.interaction_repo = InteractionResultRepository(db)
        self.amplification_repo = DefenseAmplificationResultRepository(db)
        self.analytics_repo = ResearchAnalyticsResultRepository(db)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def analyze(
        self, request: ResearchAnalyticsRequest
    ) -> ResearchAnalyticsResponse:
        config = self._validate_request(request)
        analysis_id = self._analysis_id(config)
        spec = _METRICS[request.source][request.metric]
        rows, warnings = self._fetch_rows(request)
        if not rows:
            raise AnalyticsInsufficientDataError(
                "Insufficient observations: no persisted results matched the "
                "requested source, metric, and filters"
            )

        values = self._extract_values(request, rows, spec)
        self._validate_duplicates(request, rows)
        self._validate_comparability(request, rows, spec)
        paired_ok = self._validate_pairing_if_requested(request, rows, spec)

        units = {getattr(row, "workload_unit", None) for row in rows}
        if len(units) > 1 and not spec.workload_dependent:
            labels = ", ".join(sorted(str(u) for u in units))
            warnings.append(
                f"Aggregated across mismatched workload units ({labels}); the "
                "metric is not workload-dependent, but unit-specific analysis "
                "may be preferable"
            )

        measurement_modes = sorted(
            {getattr(row, "measurement_mode", None) for row in rows},
            key=lambda v: (v is None, str(v)),
        )
        energy_providers = self._energy_provider_values(request, rows)
        mixed_context = [
            dim
            for dim in _CONTEXT_DIMENSIONS
            if len({_group_value(row, dim) for row in rows}) > 1
        ]

        overall_stats = _summary(descriptive_statistics(values))

        # overall confidence interval
        overall_ci: Optional[AnalyticsConfidenceIntervalResponse] = None
        if request.include_confidence_interval:
            ci_engine = confidence_interval_t(values, request.confidence_level)
            if ci_engine["status"] == "omitted":
                warnings.append(ci_engine["reason"])
            elif mixed_context:
                ci_engine = {
                    **ci_engine,
                    "status": "omitted",
                    "reason": (
                        "Confidence interval omitted over mixed attack contexts "
                        f"({', '.join(mixed_context)}); use group_by to separate them"
                    ),
                }
                warnings.append(ci_engine["reason"])
            overall_ci = self._ci_response(ci_engine)

        # overall hypothesis test
        overall_test: Optional[AnalyticsHypothesisTestResponse] = None
        if request.hypothesis_test:
            # metric-category and pairing validation already ran above
            if len(values) < 2:
                warnings.append(
                    "Hypothesis test omitted: requires at least 2 paired "
                    f"observations (n={len(values)})"
                )
            elif mixed_context:
                warnings.append(
                    "Hypothesis test omitted over mixed attack contexts "
                    f"({', '.join(mixed_context)}); use group_by to separate them"
                )
            else:
                overall_test = self._run_test(request, values)
                if overall_test.effect_size and overall_test.effect_size.value is not None:
                    warnings.append(
                        "Effect size is descriptive; a non-zero effect size does "
                        "not imply statistical significance"
                    )

        # grouped analysis
        groups = self._build_groups(
            request, rows, values, spec, paired_ok
        )

        paired_differences: Optional[List[float]] = (
            [float(v) for v in values] if spec.category in TESTABLE_CATEGORIES else None
        )

        limitations = list(_STATIC_LIMITATIONS)
        mode_label = measurement_modes[0] if len(measurement_modes) == 1 else None
        if mode_label == "ESTIMATED":
            limitations.insert(
                0,
                "Energy values are ESTIMATED by a deterministic estimation model, "
                "not hardware measurements.",
            )
        elif mode_label == "SIMULATED":
            limitations.insert(
                0,
                "Energy values are SIMULATED synthetic readings, not measurements.",
            )
        elif mode_label == "MEASURED":
            limitations.insert(
                0,
                "Energy values are MEASURED via the configured provider; see "
                "energy_provider for provenance.",
            )
        if spec.carbon_field is not None:
            limitations.append(
                "Carbon per workload is a derived ratio: calculated carbon "
                "(energy x carbon intensity) divided by the recorded attack "
                "workload; carbon intensity comes from the configured default, "
                "not from grid telemetry, and is never a direct measurement."
            )

        response = ResearchAnalyticsResponse(
            analysis_id=analysis_id,
            analysis_version=ANALYSIS_VERSION,
            source=request.source,
            metric=request.metric,
            metric_category=spec.category,
            filters=self._applied_filters(request),
            group_by=list(request.group_by),
            n=len(values),
            statistics=overall_stats,
            std_dev_convention=POPULATION_STD_CONVENTION,
            groups=groups,
            confidence_interval=overall_ci,
            hypothesis_test=overall_test,
            paired_differences=paired_differences,
            measurement_mode=mode_label,
            energy_provider=(
                energy_providers[0] if len(energy_providers) == 1 else None
            ),
            warnings=warnings,
            limitations=limitations,
            created_at=_utcnow(),
        )
        self._persist(request, config, response)
        return response

    def get_analysis(self, analysis_id: str) -> Optional[ResearchAnalyticsResponse]:
        row = self.analytics_repo.get_by_analysis_id(analysis_id)
        if not row:
            return None
        return ResearchAnalyticsResponse.model_validate_json(row.response_json)

    def list_analyses(
        self,
        source: Optional[str] = None,
        metric: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ResearchAnalyticsListResponse:
        matching = self.analytics_repo.filter_analyses(
            source=source,
            metric=metric,
            offset=0,
            limit=MAX_OBSERVATIONS,
        )
        window = matching[offset : offset + limit]
        items = [
            ResearchAnalyticsResponse.model_validate_json(row.response_json)
            for row in window
        ]
        return ResearchAnalyticsListResponse(total=len(matching), items=items)

    # ------------------------------------------------------------------
    # request validation
    # ------------------------------------------------------------------
    def _validate_request(self, request: ResearchAnalyticsRequest) -> dict:
        if request.source not in SOURCES:
            raise AnalyticsValidationError(
                f"Invalid source '{request.source}'. Supported sources: {', '.join(SOURCES)}"
            )
        metrics = _METRICS[request.source]
        if request.metric not in metrics:
            supported = ", ".join(sorted(metrics))
            raise AnalyticsValidationError(
                f"Invalid metric '{request.metric}' for source '{request.source}'. "
                f"Supported metrics: {supported}"
            )
        if request.hypothesis_test is not None and request.hypothesis_test not in HYPOTHESIS_TESTS:
            raise AnalyticsValidationError(
                f"Invalid hypothesis test '{request.hypothesis_test}'. "
                f"Supported tests: {', '.join(HYPOTHESIS_TESTS)}"
            )
        if request.alternative not in ALTERNATIVES:
            raise AnalyticsValidationError(
                f"Invalid alternative '{request.alternative}'. "
                f"Supported alternatives: {', '.join(ALTERNATIVES)}"
            )
        filter_model: ResearchAnalyticsFilters = request.filters
        supported_filters = set(_FILTER_FIELDS[request.source])
        for field_name, field_value in filter_model.model_dump(exclude_none=True).items():
            if field_name not in supported_filters:
                raise AnalyticsValidationError(
                    f"Filter '{field_name}' is not supported for source "
                    f"'{request.source}'; supported filters: "
                    f"{', '.join(sorted(supported_filters))}"
                )
        if len(set(request.group_by)) != len(request.group_by):
            raise AnalyticsValidationError(
                "Invalid analysis: group_by contains duplicate dimensions"
            )
        supported_dims = set(_GROUP_DIMENSIONS[request.source])
        for dimension in request.group_by:
            if dimension not in supported_dims:
                raise AnalyticsValidationError(
                    f"Group dimension '{dimension}' is not supported for source "
                    f"'{request.source}'; supported dimensions: "
                    f"{', '.join(sorted(supported_dims))}"
                )
        return self._canonical_config(request)

    def _canonical_config(self, request: ResearchAnalyticsRequest) -> dict:
        return {
            "analysis_version": ANALYSIS_VERSION,
            "source": request.source,
            "metric": request.metric,
            "filters": filter_model_dump(request),
            "group_by": list(request.group_by),
            "include_confidence_interval": request.include_confidence_interval,
            "confidence_level": request.confidence_level,
            "hypothesis_test": request.hypothesis_test,
            "alternative": request.alternative,
            "significance_level": request.significance_level,
        }

    def _analysis_id(self, config: dict) -> str:
        payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"anl_{digest[:16]}"

    # ------------------------------------------------------------------
    # data access and validation
    # ------------------------------------------------------------------
    def _fetch_rows(
        self, request: ResearchAnalyticsRequest
    ) -> Tuple[List[Any], List[str]]:
        filters: ResearchAnalyticsFilters = request.filters
        if request.source == "marginal":
            rows = self.attribution_repo.filter_attributions(
                attack_type=filters.attack_type,
                attack_intensity=filters.attack_intensity,
                measurement_mode=filters.measurement_mode,
                offset=0,
                limit=MAX_OBSERVATIONS,
            )
        elif request.source == "interaction":
            rows = self.interaction_repo.filter_interactions(
                attack_type=filters.attack_type,
                attack_intensity=filters.attack_intensity,
                measurement_mode=filters.measurement_mode,
                control_a=filters.control_a,
                control_b=filters.control_b,
                offset=0,
                limit=MAX_OBSERVATIONS,
            )
        else:
            rows = self.amplification_repo.filter_amplification(
                attack_type=filters.attack_type,
                attack_intensity=filters.attack_intensity,
                measurement_mode=filters.measurement_mode,
                control_name=filters.control_name,
                offset=0,
                limit=MAX_OBSERVATIONS,
            )
        warnings: List[str] = []
        if len(rows) >= MAX_OBSERVATIONS:
            warnings.append(
                f"Result set reached the {MAX_OBSERVATIONS}-observation analysis "
                "cap; the selection may be incomplete"
            )
        kept: List[Any] = []
        for row in rows:
            if (
                filters.experiment_id is not None
                and row.experiment_id != filters.experiment_id
            ):
                continue
            if (
                filters.workload_unit is not None
                and getattr(row, "workload_unit", None) != filters.workload_unit
            ):
                continue
            if (
                filters.energy_provider is not None
                and getattr(row, "energy_provider", None) != filters.energy_provider
            ):
                continue
            kept.append(row)
        kept.sort(key=lambda row: row.id)
        return kept, warnings

    def _extract_values(
        self,
        request: ResearchAnalyticsRequest,
        rows: Sequence[Any],
        spec: _MetricSpec,
    ) -> List[float]:
        values: List[float] = []
        for row in rows:
            if spec.carbon_field is not None:
                derived = calculate_carbon_per_workload(
                    getattr(row, spec.carbon_field, None),
                    getattr(row, spec.workload_field, None)
                    if spec.workload_field
                    else None,
                    getattr(row, "workload_unit", None),
                )
                if derived["status"] != "available":
                    raise AnalyticsValidationError(
                        f"Invalid carbon-per-workload input: observation "
                        f"{row.id} ({derived['reason']}); metric "
                        f"'{request.metric}' cannot be computed for this row"
                    )
                values.append(float(derived["value_kg"]))
                continue
            raw = getattr(row, request.metric, None)
            if raw is None:
                raise AnalyticsValidationError(
                    f"Missing metric value: observation {row.id} has no value for "
                    f"metric '{request.metric}'"
                )
            if not _is_number(raw) or not math.isfinite(raw):
                raise AnalyticsValidationError(
                    f"Invalid numeric data: observation {row.id} has non-finite "
                    f"value {raw!r} for metric '{request.metric}'"
                )
            values.append(float(raw))
        return values

    def _validate_duplicates(
        self, request: ResearchAnalyticsRequest, rows: Sequence[Any]
    ) -> None:
        key_fields = _DUPLICATE_KEYS[request.source]
        seen: Dict[Tuple, int] = {}
        duplicates: List[Tuple] = []
        for row in rows:
            key = tuple(getattr(row, field, None) for field in key_fields)
            if key in seen:
                duplicates.append(key)
            else:
                seen[key] = row.id
        if duplicates:
            preview = "; ".join(str(d) for d in duplicates[:5])
            raise AnalyticsValidationError(
                f"Duplicate observations: {len(duplicates)} duplicate "
                f"observation key(s) found for source '{request.source}' "
                f"({preview}); remove recomputed duplicate results before analysis"
            )

    def _validate_comparability(
        self,
        request: ResearchAnalyticsRequest,
        rows: Sequence[Any],
        spec: _MetricSpec,
    ) -> None:
        modes = {getattr(row, "measurement_mode", None) for row in rows}
        if len(modes) > 1:
            labels = ", ".join(sorted(str(m) for m in modes))
            raise AnalyticsValidationError(
                f"Mixed measurement modes ({labels}): results measured in "
                "different modes are not comparable"
            )
        if request.source != "marginal":
            providers = {getattr(row, "energy_provider", None) for row in rows}
            if len(providers) > 1:
                labels = ", ".join(sorted(str(p) for p in providers))
                raise AnalyticsValidationError(
                    f"Mixed energy providers ({labels}): results from different "
                    "providers are not comparable"
                )
        units = {getattr(row, "workload_unit", None) for row in rows}
        if len(units) > 1:
            labels = ", ".join(sorted(str(u) for u in units))
            if spec.workload_dependent:
                raise AnalyticsValidationError(
                    f"Mismatched workload units ({labels}): this metric depends "
                    "on workload and requires a single workload unit"
                )
        if spec.per_workload:
            for row in rows:
                workload = getattr(row, "attack_workload", None)
                if workload is None or not _is_number(workload) or not math.isfinite(workload):
                    raise AnalyticsValidationError(
                        f"Invalid workload: observation {row.id} has workload "
                        f"{workload!r}; ratio metrics require a valid workload"
                    )
                if workload <= 0:
                    raise AnalyticsValidationError(
                        f"Invalid workload: observation {row.id} has non-positive "
                        f"workload {workload}; ratio metrics cannot divide by zero"
                    )

    def _validate_pairing_if_requested(
        self,
        request: ResearchAnalyticsRequest,
        rows: Sequence[Any],
        spec: _MetricSpec,
    ) -> bool:
        if not request.hypothesis_test:
            return False
        if spec.category not in TESTABLE_CATEGORIES:
            raise AnalyticsValidationError(
                f"Invalid analysis: hypothesis test requires a paired-difference "
                f"metric, but '{request.metric}' is a level metric; choose a "
                f"difference or ratio metric"
            )
        required_fields: Dict[str, Tuple[str, ...]] = {
            "marginal": ("baseline_run_id", "security_run_id"),
            "interaction": (
                "baseline_run_id",
                "control_a_run_id",
                "control_b_run_id",
                "combined_run_id",
            ),
            "amplification": ("baseline_run_id", "defense_run_id"),
        }
        unpaired = [
            row.id
            for row in rows
            if any(getattr(row, field, None) is None for field in required_fields[request.source])
        ]
        if unpaired:
            preview = ", ".join(str(i) for i in unpaired[:10])
            raise AnalyticsValidationError(
                f"Unpaired observations: {len(unpaired)} result(s) are missing "
                f"paired run identifiers (observation ids: {preview}); paired "
                "analysis requires baseline and treatment run identifiers"
            )
        return True

    def _energy_provider_values(
        self, request: ResearchAnalyticsRequest, rows: Sequence[Any]
    ) -> List[str]:
        if request.source == "marginal":
            return []
        providers = {getattr(row, "energy_provider", None) for row in rows}
        return sorted(str(p) for p in providers)

    # ------------------------------------------------------------------
    # analysis components
    # ------------------------------------------------------------------
    def _ci_response(self, engine_result: dict) -> AnalyticsConfidenceIntervalResponse:
        return AnalyticsConfidenceIntervalResponse(
            level=engine_result["level"],
            n=engine_result["n"],
            status=engine_result["status"],
            reason=engine_result.get("reason"),
            lower=engine_result.get("lower"),
            upper=engine_result.get("upper"),
            mean=engine_result.get("mean"),
            standard_error=engine_result.get("standard_error"),
            degrees_of_freedom=engine_result.get("degrees_of_freedom"),
            critical_value=engine_result.get("critical_value"),
            method=engine_result.get("method"),
            std_dev_convention=engine_result.get("std_dev_convention"),
        )

    def _hypotheses(
        self, request: ResearchAnalyticsRequest
    ) -> Tuple[str, str]:
        if request.hypothesis_test == "paired_t":
            null = "Mean paired difference = 0"
            if request.alternative == "greater":
                alt = "Mean paired difference > 0"
            elif request.alternative == "less":
                alt = "Mean paired difference < 0"
            else:
                alt = "Mean paired difference != 0"
            return null, alt
        null = "Median paired difference = 0 (difference distribution symmetric around 0)"
        if request.alternative == "greater":
            alt = "Median paired difference > 0"
        elif request.alternative == "less":
            alt = "Median paired difference < 0"
        else:
            alt = "Median paired difference != 0"
        return null, alt

    def _run_test(
        self, request: ResearchAnalyticsRequest, values: Sequence[float]
    ) -> AnalyticsHypothesisTestResponse:
        value_list = [float(v) for v in values]
        null_hypothesis, alternative_hypothesis = self._hypotheses(request)
        if request.hypothesis_test == "paired_t":
            engine_result = paired_t_test(
                value_list,
                alternative=request.alternative,
                significance_level=request.significance_level,
            )
            test_name = "Paired t-test (one-sample on paired differences)"
            method = "student_t_paired"
            method_notes = (
                "Paired observations analyzed as differences; Student's t uses "
                f"the {SAMPLE_STD_CONVENTION} with n-1 degrees of freedom and "
                "assumes independent pairs with approximately normally "
                "distributed differences. Statistical result only: significance "
                "does not imply a configuration is better or more efficient."
            )
            effect = cohens_dz(value_list)
            effect_dto = AnalyticsEffectSizeResponse(
                name="cohens_dz",
                value=effect.get("value"),
                status=effect["status"],
                reason=effect.get("reason"),
                sample_count=effect["sample_count"],
                convention=(
                    "Cohen's dz = mean(d) / sample_std(d), "
                    f"{SAMPLE_STD_CONVENTION}; descriptive only"
                ),
            )
            excluded = 0
        else:
            engine_result = wilcoxon_signed_rank(
                value_list,
                alternative=request.alternative,
                significance_level=request.significance_level,
            )
            test_name = "Wilcoxon signed-rank test"
            method = engine_result.get("method", "wilcoxon_signed_rank")
            effect = rank_biserial(value_list)
            effect_dto = AnalyticsEffectSizeResponse(
                name="rank_biserial_correlation",
                value=effect.get("value"),
                status=effect["status"],
                reason=effect.get("reason"),
                sample_count=effect["sample_count"],
                convention=(
                    "Matched-pairs rank-biserial r = (W+ - W-) / (W+ + W-); "
                    "descriptive only"
                ),
            )
            excluded = engine_result.get("excluded_zero_differences", 0)
            method_notes = (
                "Non-parametric signed-rank test on paired differences; assumes "
                "a symmetric difference distribution. "
                f"Method: {method}. "
                f"Zero differences excluded from ranks: {excluded}. "
                "Statistical result only: significance does not imply a "
                "configuration is better or more efficient."
            )

        status = engine_result["status"]
        if status == "ok":
            p_value = engine_result["p_value"]
            reject_null = bool(p_value < request.significance_level)
            interpretation = "reject_null" if reject_null else "fail_to_reject_null"
        else:
            p_value = None
            reject_null = None
            interpretation = "undefined"

        return AnalyticsHypothesisTestResponse(
            test_id=request.hypothesis_test,
            test_name=test_name,
            null_hypothesis=null_hypothesis,
            alternative_hypothesis=alternative_hypothesis,
            status=status,
            reason=engine_result.get("reason"),
            statistic=engine_result.get("statistic"),
            p_value=p_value,
            sample_count=engine_result.get("sample_count", len(value_list)),
            excluded_zero_differences=excluded,
            degrees_of_freedom=engine_result.get("degrees_of_freedom"),
            significance_level=request.significance_level,
            alternative=request.alternative,
            reject_null=reject_null,
            interpretation=interpretation,
            method=method,
            method_notes=method_notes,
            effect_size=effect_dto,
        )

    def _build_groups(
        self,
        request: ResearchAnalyticsRequest,
        rows: Sequence[Any],
        values: Sequence[float],
        spec: _MetricSpec,
        paired_ok: bool,
    ) -> List[AnalyticsGroupResponse]:
        if not request.group_by:
            return []
        buckets: Dict[Tuple[str, ...], List[int]] = {}
        for index, row in enumerate(rows):
            key = tuple(_group_value(row, dim) for dim in request.group_by)
            buckets.setdefault(key, []).append(index)
        groups: List[AnalyticsGroupResponse] = []
        for key in sorted(buckets):
            member_indexes = buckets[key]
            member_values = [values[i] for i in member_indexes]
            member_rows = [rows[i] for i in member_indexes]
            group_warnings: List[str] = []

            group_ci: Optional[AnalyticsConfidenceIntervalResponse] = None
            if request.include_confidence_interval:
                if len(member_values) < 2:
                    reason = (
                        "Confidence interval omitted: requires at least 2 "
                        f"observations (n={len(member_values)})"
                    )
                    group_warnings.append(reason)
                    group_ci = AnalyticsConfidenceIntervalResponse(
                        level=request.confidence_level,
                        n=len(member_values),
                        status="omitted",
                        reason=reason,
                    )
                else:
                    group_ci = self._ci_response(
                        confidence_interval_t(member_values, request.confidence_level)
                    )

            group_test: Optional[AnalyticsHypothesisTestResponse] = None
            if request.hypothesis_test:
                mixed_in_group = [
                    dim
                    for dim in _CONTEXT_DIMENSIONS
                    if len({_group_value(r, dim) for r in member_rows}) > 1
                ]
                if len(member_values) < 2:
                    group_warnings.append(
                        "Hypothesis test omitted: requires at least 2 paired "
                        f"observations (n={len(member_values)})"
                    )
                elif mixed_in_group:
                    group_warnings.append(
                        "Hypothesis test omitted over mixed attack contexts "
                        f"({', '.join(mixed_in_group)}); refine group_by"
                    )
                elif paired_ok and spec.category in TESTABLE_CATEGORIES:
                    group_test = self._run_test(request, member_values)
                    if (
                        group_test.effect_size
                        and group_test.effect_size.value is not None
                    ):
                        group_warnings.append(
                            "Effect size is descriptive; a non-zero effect size "
                            "does not imply statistical significance"
                        )

            groups.append(
                AnalyticsGroupResponse(
                    group={
                        dim: key[i] for i, dim in enumerate(request.group_by)
                    },
                    n=len(member_values),
                    statistics=_summary(descriptive_statistics(member_values)),
                    confidence_interval=group_ci,
                    hypothesis_test=group_test,
                    warnings=group_warnings,
                )
            )
        return groups

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _applied_filters(self, request: ResearchAnalyticsRequest) -> Dict[str, Any]:
        return request.filters.model_dump(exclude_none=True)

    def _persist(
        self,
        request: ResearchAnalyticsRequest,
        config: dict,
        response: ResearchAnalyticsResponse,
    ) -> None:
        existing = self.analytics_repo.get_by_analysis_id(response.analysis_id)
        request_json = json.dumps(config, sort_keys=True, separators=(",", ":"))
        response_json = response.model_dump_json()
        if existing:
            existing.request_json = request_json
            existing.response_json = response_json
            self.db.commit()
        else:
            self.analytics_repo.create(
                {
                    "analysis_id": response.analysis_id,
                    "analysis_version": ANALYSIS_VERSION,
                    "source": request.source,
                    "metric": request.metric,
                    "request_json": request_json,
                    "response_json": response_json,
                    "created_at": _utcnow(),
                }
            )
            self.db.commit()


def filter_model_dump(request: ResearchAnalyticsRequest) -> Dict[str, Any]:
    """Canonical (sorted, non-null) filter representation for hashing."""
    return dict(
        sorted(request.filters.model_dump(exclude_none=True).items())
    )
