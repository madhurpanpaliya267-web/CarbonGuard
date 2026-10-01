import pytest
from app.engines.security.attack_simulator import simulate_attack
from app.engines.security.threat_detector import ATTACK_PROFILES


class TestAttackSimulatorIntegration:
    def test_simulate_ddos(self):
        result = simulate_attack("ddos")
        assert result["event"]["event_type"] == "ddos"
        assert "energy_impact" in result
        assert "carbon_impact" in result
        assert "pipeline" in result

    def test_simulate_brute_force(self):
        result = simulate_attack("brute_force")
        assert result["event"]["event_type"] == "brute_force"

    def test_simulate_port_scan(self):
        result = simulate_attack("port_scan")
        assert result["event"]["event_type"] == "port_scan"

    def test_simulate_sql_injection(self):
        result = simulate_attack("sql_injection")
        assert result["event"]["event_type"] == "sql_injection"

    def test_simulate_malware(self):
        result = simulate_attack("malware")
        assert result["event"]["event_type"] == "malware"

    def test_simulate_suspicious_login(self):
        result = simulate_attack("suspicious_login")
        assert result["event"]["event_type"] == "suspicious_login"

    def test_simulate_phishing(self):
        result = simulate_attack("phishing")
        assert result["event"]["event_type"] == "phishing"

    def test_unknown_attack_raises(self):
        with pytest.raises(ValueError, match="Unknown attack type"):
            simulate_attack("nonexistent")

    def test_all_attack_types_still_work(self):
        for attack_type in ATTACK_PROFILES:
            result = simulate_attack(attack_type)
            assert result["event"]["event_type"] == attack_type

    def test_result_has_all_expected_sections(self):
        result = simulate_attack("ddos")
        assert "event" in result
        assert "threat" in result
        assert "risk_assessment" in result
        assert "workload_impact" in result
        assert "energy_impact" in result
        assert "carbon_impact" in result
        assert "ai_recommendation" in result
        assert "pipeline" in result

    def test_energy_impact_has_estimated_flag(self):
        result = simulate_attack("ddos")
        assert result["energy_impact"]["estimated"] is True

    def test_carbon_impact_has_simulated_flag(self):
        result = simulate_attack("ddos")
        assert result["carbon_impact"]["simulated"] is True

    def test_pipeline_has_all_steps(self):
        result = simulate_attack("ddos")
        steps = [s["step"] for s in result["pipeline"]]
        assert "Attack Simulation" in steps
        assert "Threat Detection" in steps
        assert "Energy Estimate" in steps


class TestAttackSimulatorWithResearchProfile:
    def test_with_intensity_low(self):
        result = simulate_attack("ddos", intensity="low")
        assert "research_profile" in result
        assert result["research_profile"]["intensity"] == "low"
        assert result["research_profile"]["workload"]["unit"] == "packets_per_second"

    def test_with_intensity_medium(self):
        result = simulate_attack("ddos", intensity="medium")
        assert result["research_profile"]["intensity"] == "medium"

    def test_with_intensity_high(self):
        result = simulate_attack("ddos", intensity="high")
        assert result["research_profile"]["intensity"] == "high"

    def test_with_custom_duration(self):
        result = simulate_attack("ddos", intensity="low", duration_seconds=45)
        assert result["research_profile"]["duration_seconds"] == 45

    def test_without_intensity_no_research_profile(self):
        result = simulate_attack("ddos")
        assert "research_profile" not in result

    def test_workload_value_matches_intensity(self):
        low = simulate_attack("brute_force", intensity="low")
        high = simulate_attack("brute_force", intensity="high")
        assert low["research_profile"]["workload"]["value"] < high["research_profile"]["workload"]["value"]

    def test_config_version_preserved(self):
        result = simulate_attack("ddos", intensity="medium")
        assert result["research_profile"]["config_version"] == "1.0.0"

    def test_supported_controls_populated(self):
        result = simulate_attack("ddos", intensity="low")
        assert len(result["research_profile"]["supported_controls"]) > 0

    def test_invalid_intensity_graceful(self):
        result = simulate_attack("ddos", intensity="extreme")
        assert "research_profile" not in result
        assert result["event"]["event_type"] == "ddos"

    def test_all_types_with_intensity(self):
        for attack_type in ATTACK_PROFILES:
            result = simulate_attack(attack_type, intensity="medium")
            assert "research_profile" in result
            assert result["research_profile"]["intensity"] == "medium"
