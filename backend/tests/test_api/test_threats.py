class TestThreats:
    def test_get_threats(self, client):
        r = client.get("/api/v1/threats")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data

    def test_get_threat_not_found(self, client):
        r = client.get("/api/v1/threats/99999")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_threat_explanation_not_found(self, client):
        r = client.get("/api/v1/threats/99999/explanation")
        assert r.status_code == 404
        assert "detail" in r.json()


class TestAttackSimulator:
    def test_get_attack_types(self, client):
        r = client.get("/api/v1/simulator/attack-types")
        assert r.status_code == 200
        data = r.json()
        assert "types" in data
        assert len(data["types"]) == 6

    def test_simulate_attack(self, client):
        r = client.post("/api/v1/simulator/simulate", json={"attack_type": "port_scan"})
        assert r.status_code == 200
        data = r.json()
        assert "event" in data
        assert "threat" in data
        assert "risk_assessment" in data
        assert "pipeline" in data
