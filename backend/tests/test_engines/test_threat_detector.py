from app.engines.security.threat_detector import (
    detect_event,
    classify_severity,
    generate_event_uuid,
    ATTACK_PROFILES,
)


class TestThreatDetector:
    def test_detect_known_attack_types(self):
        for attack_type in ATTACK_PROFILES:
            result = detect_event({"attack_type": attack_type})
            assert result["threat_type"] == attack_type
            assert 0 <= result["confidence"] <= 1
            assert result["severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            assert result["estimated_cpu_seconds"] > 0
            assert result["estimated_energy_kwh"] > 0

    def test_detect_unknown_attack_type(self):
        result = detect_event({"attack_type": "unknown_xyz"})
        assert result["threat_type"] == "unknown"
        assert result["confidence"] == 0.5

    def test_classify_severity_bounds(self):
        for _ in range(50):
            sev = classify_severity("ddos", "HIGH")
            assert sev in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_generate_event_uuid_format(self):
        uid = generate_event_uuid()
        assert len(uid) == 36
        assert uid.count("-") == 4
