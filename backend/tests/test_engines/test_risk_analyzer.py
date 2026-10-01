from app.engines.security.risk_analyzer import analyze_risk, SEVERITY_WEIGHTS


class TestRiskAnalyzer:
    def test_basic_risk_analysis(self):
        result = analyze_risk(
            severity="HIGH",
            confidence=0.85,
            frequency=3,
            anomaly_level=0.7,
            resource_impact=0.6,
        )
        assert 0 <= result["risk_score"] <= 100
        assert result["severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert len(result["factors"]) == 5

    def test_critical_severity_gives_high_risk(self):
        result = analyze_risk(severity="CRITICAL", confidence=0.95, frequency=10)
        assert result["risk_score"] >= 60

    def test_low_severity_low_frequency(self):
        result = analyze_risk(severity="LOW", confidence=0.5, frequency=1)
        assert result["risk_score"] < 60

    def test_all_severity_levels_work(self):
        for sev in SEVERITY_WEIGHTS:
            result = analyze_risk(severity=sev, confidence=0.7, frequency=2)
            assert result["risk_score"] >= 0
