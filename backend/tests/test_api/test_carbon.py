class TestCarbon:
    def test_get_overview(self, client):
        r = client.get("/api/v1/carbon")
        assert r.status_code == 200
        data = r.json()
        assert "current" in data
        assert "history" in data
        assert "summary" in data

    def test_get_current(self, client):
        r = client.get("/api/v1/carbon/current")
        assert r.status_code == 200
        data = r.json()
        assert "total_energy_kwh" in data
        assert "total_co2_kg" in data

    def test_get_history(self, client):
        r = client.get("/api/v1/carbon/history?limit=10")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_efficiency(self, client):
        r = client.get("/api/v1/carbon/efficiency")
        assert r.status_code == 200
        data = r.json()
        assert "efficiency_score" in data
