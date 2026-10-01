class TestEnergy:
    def test_get_overview(self, client):
        r = client.get("/api/v1/energy")
        assert r.status_code == 200
        data = r.json()
        assert "current" in data
        assert "history" in data

    def test_get_current(self, client):
        r = client.get("/api/v1/energy/current")
        assert r.status_code == 200
        data = r.json()
        assert "energy_kwh" in data
        assert "total_power_watts" in data

    def test_get_history(self, client):
        r = client.get("/api/v1/energy/history?limit=10")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
