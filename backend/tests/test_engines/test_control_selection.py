import pytest

from app.engines.security.security_controls import (
    SEVERITY_CONTROL_LIMITS,
    select_controls_for_threat,
)


class TestSelectControlsForThreat:
    def test_low_gets_minimum_one_control(self):
        result = select_controls_for_threat("ddos", "LOW", risk_score=20.0)
        assert result["status"] == "selected"
        assert result["basis"] == "rule_based"
        assert len(result["selected"]) == 1
        assert result["tier"] == "LOW"

    def test_medium_gets_moderate_controls(self):
        result = select_controls_for_threat("ddos", "MEDIUM")
        assert len(result["selected"]) == 2
        assert result["tier"] == "MEDIUM"

    def test_high_gets_stronger_controls(self):
        result = select_controls_for_threat("ddos", "HIGH")
        assert len(result["selected"]) == 4
        assert result["tier"] == "HIGH"

    def test_critical_gets_all_available_controls(self):
        result = select_controls_for_threat("ddos", "CRITICAL")
        assert result["selected"] == result["available"]
        assert len(result["selected"]) > 4
        assert result["tier"] == "CRITICAL"

    def test_monotonic_with_severity(self):
        counts = [
            len(select_controls_for_threat("ddos", s)["selected"])
            for s in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        ]
        assert counts == sorted(counts)
        assert counts[0] < counts[-1]

    def test_selected_is_subset_of_available(self):
        for severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            result = select_controls_for_threat("malware", severity)
            assert set(result["selected"]).issubset(set(result["available"]))

    def test_selected_controls_support_the_attack(self):
        from app.engines.security.security_controls import get_control

        result = select_controls_for_threat("port_scan", "HIGH")
        for control_id in result["selected"]:
            assert "port_scan" in get_control(control_id).supported_attack_types

    def test_unknown_attack_type_reports_none_available(self):
        result = select_controls_for_threat("not_a_real_attack", "HIGH")
        assert result["status"] == "none_available"
        assert result["selected"] == []
        assert "No registered security control" in result["reason"]

    def test_reason_never_claims_optimality(self):
        result = select_controls_for_threat("ddos", "CRITICAL")
        assert "not an optimality claim" in result["reason"]
        assert result["basis"] == "rule_based"

    def test_control_details_match_selection(self):
        result = select_controls_for_threat("brute_force", "MEDIUM")
        detail_ids = [d["control_id"] for d in result["control_details"]]
        assert detail_ids == result["selected"]

    def test_tier_limits_defined(self):
        assert SEVERITY_CONTROL_LIMITS["LOW"] == 1
        assert SEVERITY_CONTROL_LIMITS["MEDIUM"] == 2
        assert SEVERITY_CONTROL_LIMITS["CRITICAL"] is None

    def test_risk_score_echoed(self):
        result = select_controls_for_threat("ddos", "LOW", risk_score=42.5)
        assert result["risk_score"] == 42.5
