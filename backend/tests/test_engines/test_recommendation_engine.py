import pytest
from app.engines.ai.recommendation_engine import generate_recommendations


class TestRecommendationEngine:
    def test_returns_list(self):
        result = generate_recommendations(
            active_threats=0, energy_kwh=1.0, co2_kg=0.5,
            renewable_pct=30.0, carbon_intensity=475.0, workload_count=5,
        )
        assert isinstance(result, list)
        assert len(result) > 0

    def test_high_threats_generates_security_recommendation(self):
        result = generate_recommendations(
            active_threats=5, energy_kwh=1.0, co2_kg=0.5,
            renewable_pct=30.0, carbon_intensity=475.0, workload_count=5,
        )
        types = [r["recommendation_type"] for r in result]
        assert "security" in types

    def test_high_energy_generates_energy_recommendation(self):
        result = generate_recommendations(
            active_threats=0, energy_kwh=6.0, co2_kg=0.5,
            renewable_pct=30.0, carbon_intensity=475.0, workload_count=5,
        )
        types = [r["recommendation_type"] for r in result]
        assert "energy" in types

    def test_high_renewable_generates_carbon_recommendation(self):
        result = generate_recommendations(
            active_threats=0, energy_kwh=1.0, co2_kg=0.5,
            renewable_pct=70.0, carbon_intensity=475.0, workload_count=5,
        )
        types = [r["recommendation_type"] for r in result]
        assert "carbon" in types

    def test_high_co2_generates_carbon_recommendation(self):
        result = generate_recommendations(
            active_threats=0, energy_kwh=1.0, co2_kg=1.5,
            renewable_pct=30.0, carbon_intensity=475.0, workload_count=5,
        )
        types = [r["recommendation_type"] for r in result]
        assert "carbon" in types

    def test_threats_and_low_renewable_generates_workload(self):
        result = generate_recommendations(
            active_threats=3, energy_kwh=1.0, co2_kg=0.5,
            renewable_pct=20.0, carbon_intensity=475.0, workload_count=5,
        )
        types = [r["recommendation_type"] for r in result]
        assert "workload" in types

    def test_normal_conditions_generates_general(self):
        result = generate_recommendations(
            active_threats=1, energy_kwh=2.0, co2_kg=0.5,
            renewable_pct=40.0, carbon_intensity=475.0, workload_count=5,
        )
        types = [r["recommendation_type"] for r in result]
        assert "general" in types

    def test_each_recommendation_has_required_fields(self):
        result = generate_recommendations(
            active_threats=5, energy_kwh=6.0, co2_kg=1.5,
            renewable_pct=70.0, carbon_intensity=475.0, workload_count=5,
        )
        required = [
            "recommendation_type", "recommendation", "priority",
            "reason", "confidence", "factors",
        ]
        for rec in result:
            for field in required:
                assert field in rec

    def test_all_conditions_met_generates_multiple(self):
        result = generate_recommendations(
            active_threats=5, energy_kwh=6.0, co2_kg=1.5,
            renewable_pct=70.0, carbon_intensity=475.0, workload_count=5,
        )
        assert len(result) >= 4

    def test_factors_are_lists(self):
        result = generate_recommendations(
            active_threats=5, energy_kwh=1.0, co2_kg=0.5,
            renewable_pct=30.0, carbon_intensity=475.0, workload_count=5,
        )
        for rec in result:
            assert isinstance(rec["factors"], list)
            assert len(rec["factors"]) > 0

    def test_confidence_is_bounded(self):
        result = generate_recommendations(
            active_threats=5, energy_kwh=6.0, co2_kg=1.5,
            renewable_pct=70.0, carbon_intensity=475.0, workload_count=5,
        )
        for rec in result:
            assert 0 <= rec["confidence"] <= 1
