class TestSystemHealth:
    def test_get_health(self, client):
        r = client.get("/api/v1/system-health")
        assert r.status_code == 200
        data = r.json()
        assert "cpu_utilization" in data
        assert "security_engine_status" in data

    def test_get_history(self, client):
        r = client.get("/api/v1/system-health/history?limit=10")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
