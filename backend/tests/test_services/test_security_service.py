import pytest
from unittest.mock import MagicMock, patch
from app.services.security_service import SecurityService


class TestSecurityService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = SecurityService(self.db)

    def test_get_events_returns_paginated_format(self):
        self.service.event_repo.filter_events = MagicMock(return_value=[MagicMock(), MagicMock()])
        self.service.event_repo.count = MagicMock(return_value=50)

        result = self.service.get_events()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert result["total"] == 50
        assert len(result["items"]) == 2

    def test_get_events_with_filters(self):
        self.service.event_repo.filter_events = MagicMock(return_value=[])
        self.service.event_repo.count = MagicMock(return_value=0)

        self.service.get_events(severity="HIGH", event_type="ddos", status="detected", page=2, page_size=5)
        self.service.event_repo.filter_events.assert_called_once_with(
            severity="HIGH", event_type="ddos", status="detected", offset=5, limit=5,
        )

    def test_get_events_page_calculation(self):
        self.service.event_repo.filter_events = MagicMock(return_value=[])
        self.service.event_repo.count = MagicMock(return_value=0)

        self.service.get_events(page=3, page_size=10)
        self.service.event_repo.filter_events.assert_called_once_with(
            severity=None, event_type=None, status=None, offset=20, limit=10,
        )

    def test_get_event(self):
        mock_event = MagicMock(id=1)
        self.service.event_repo.get_by_id = MagicMock(return_value=mock_event)
        result = self.service.get_event(1)
        assert result == mock_event

    def test_simulate_creates_event_and_threat(self):
        mock_event = MagicMock(id=1)
        mock_threat = MagicMock(id=1)
        self.service.event_repo.create = MagicMock(return_value=mock_event)
        self.service.threat_repo.create = MagicMock(return_value=mock_threat)

        with patch("app.services.security_service.simulate_attack") as mock_sim:
            mock_sim.return_value = {
                "event": {
                    "event_uuid": "test-uuid",
                    "timestamp": "2024-01-01T00:00:00",
                    "event_type": "ddos",
                    "severity": "HIGH",
                    "source_ip": "1.2.3.4",
                    "target_ip": "5.6.7.8",
                    "target_port": 80,
                    "confidence": 0.9,
                    "status": "detected",
                    "detection_method": "test",
                    "description": "test",
                    "risk_score": 75.0,
                    "estimated_workload_cpu": 60.0,
                    "estimated_energy_kwh": 0.03,
                    "estimated_co2_kg": 0.01,
                },
                "threat": {
                    "threat_uuid": "test-threat-uuid",
                    "threat_type": "ddos",
                    "severity": "HIGH",
                    "confidence": 0.9,
                    "risk_score": 75.0,
                    "status": "active",
                    "detected_at": "2024-01-01T00:00:00",
                    "explanation": "test",
                    "recommended_action": "test",
                    "anomaly_level": 0.5,
                },
                "risk_assessment": {"risk_score": 75.0},
                "workload_impact": {"cpu_seconds": 60.0},
                "energy_impact": {"energy_kwh": 0.03},
                "carbon_impact": {"co2_kg": 0.01},
                "ai_recommendation": {"recommendation": "test"},
                "pipeline": [{"step": "test", "status": "completed"}],
            }
            result = self.service.simulate("ddos")
            assert result["event"] == mock_event
            assert result["threat"] == mock_threat
            assert "risk_assessment" in result
            assert "pipeline" in result
            self.service.event_repo.create.assert_called_once()
            self.service.threat_repo.create.assert_called_once()

    def test_simulate_converts_string_timestamps(self):
        self.service.event_repo.create = MagicMock(return_value=MagicMock(id=1))
        self.service.threat_repo.create = MagicMock(return_value=MagicMock(id=1))

        with patch("app.services.security_service.simulate_attack") as mock_sim:
            mock_sim.return_value = {
                "event": {"event_uuid": "u", "timestamp": "2024-01-01T00:00:00", "event_type": "ddos",
                          "severity": "HIGH", "source_ip": "1.1.1.1", "target_ip": "2.2.2.2",
                          "target_port": 80, "confidence": 0.9, "status": "detected",
                          "detection_method": "t", "description": "t", "risk_score": 75,
                          "estimated_workload_cpu": 60, "estimated_energy_kwh": 0.03,
                          "estimated_co2_kg": 0.01},
                "threat": {"threat_uuid": "u", "threat_type": "ddos", "severity": "HIGH",
                           "confidence": 0.9, "risk_score": 75, "status": "active",
                           "detected_at": "2024-01-01T00:00:00", "explanation": "t",
                           "recommended_action": "t", "anomaly_level": 0.5},
                "risk_assessment": {}, "workload_impact": {}, "energy_impact": {},
                "carbon_impact": {}, "ai_recommendation": {}, "pipeline": [],
            }
            self.service.simulate("ddos")
            event_data = self.service.event_repo.create.call_args[0][0]
            from datetime import datetime
            assert isinstance(event_data["timestamp"], datetime)
