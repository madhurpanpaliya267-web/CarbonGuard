import pytest
from app.engines.ai.explainability import explain_prediction, explain_recommendation


class TestExplainPrediction:
    def test_returns_required_keys(self):
        result = explain_prediction(
            prediction="ddos",
            confidence=0.85,
            factors=[
                {"factor": "Severity", "weight": 0.4, "value": "HIGH"},
                {"factor": "Confidence", "weight": 0.3, "value": 0.85},
            ],
        )
        assert "prediction" in result
        assert "confidence" in result
        assert "factors" in result
        assert "reasoning" in result
        assert "recommended_action" in result

    def test_prediction_matches_input(self):
        result = explain_prediction(
            prediction="malware",
            confidence=0.92,
            factors=[{"factor": "test", "weight": 1.0, "value": "x"}],
        )
        assert result["prediction"] == "malware"

    def test_confidence_matches_input(self):
        result = explain_prediction(
            prediction="test",
            confidence=0.75,
            factors=[{"factor": "test", "weight": 1.0, "value": "x"}],
        )
        assert result["confidence"] == 0.75

    def test_factors_sorted_by_weight(self):
        result = explain_prediction(
            prediction="test",
            confidence=0.8,
            factors=[
                {"factor": "Low", "weight": 0.1, "value": "a"},
                {"factor": "High", "weight": 0.9, "value": "b"},
                {"factor": "Mid", "weight": 0.5, "value": "c"},
            ],
        )
        weights = [f["weight"] for f in result["factors"]]
        assert weights == sorted(weights, reverse=True)

    def test_max_5_factors(self):
        factors = [{"factor": f"f{i}", "weight": i * 0.1, "value": i} for i in range(10)]
        result = explain_prediction("test", 0.8, factors)
        assert len(result["factors"]) <= 5

    def test_reasoning_contains_prediction(self):
        result = explain_prediction(
            prediction="brute_force",
            confidence=0.8,
            factors=[{"factor": "test", "weight": 1.0, "value": "x"}],
        )
        assert "brute_force" in result["reasoning"]

    def test_empty_factors(self):
        result = explain_prediction("test", 0.5, [])
        assert result["factors"] == []


class TestExplainRecommendation:
    def test_returns_required_keys(self):
        result = explain_recommendation({
            "recommendation": "Test recommendation",
            "priority": "high",
            "reason": "Because",
            "confidence": 0.85,
            "factors": [{"factor": "test", "weight": 0.5, "value": "x"}],
        })
        assert "explanation" in result
        assert "factors" in result
        assert "confidence" in result

    def test_explanation_contains_recommendation(self):
        result = explain_recommendation({
            "recommendation": "Activate WAF rules",
            "priority": "high",
            "reason": "SQL injection detected",
            "confidence": 0.9,
            "factors": [],
        })
        assert "Activate WAF rules" in result["explanation"]

    def test_factors_sorted_by_weight(self):
        result = explain_recommendation({
            "recommendation": "test",
            "priority": "medium",
            "reason": "test",
            "confidence": 0.7,
            "factors": [
                {"factor": "Low", "weight": 0.2},
                {"factor": "High", "weight": 0.8},
            ],
        })
        weights = [f["weight"] for f in result["factors"]]
        assert weights == sorted(weights, reverse=True)

    def test_empty_factors(self):
        result = explain_recommendation({
            "recommendation": "test",
            "priority": "low",
            "reason": "test",
            "confidence": 0.5,
            "factors": [],
        })
        assert result["factors"] == []

    def test_confidence_from_recommendation(self):
        result = explain_recommendation({
            "recommendation": "test",
            "priority": "medium",
            "reason": "test",
            "confidence": 0.88,
            "factors": [],
        })
        assert result["confidence"] == 0.88
