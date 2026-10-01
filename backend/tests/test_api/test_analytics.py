class TestAnalytics:
    def test_security_analytics(self, client):
        r = client.get("/api/v1/analytics/security?period=7d")
        assert r.status_code == 200
        data = r.json()
        assert "attacks_over_time" in data
        assert "categories" in data

    def test_carbon_analytics(self, client):
        r = client.get("/api/v1/analytics/carbon?period=7d")
        assert r.status_code == 200
        data = r.json()
        assert "emissions_over_time" in data

    def test_energy_analytics(self, client):
        r = client.get("/api/v1/analytics/energy?period=7d")
        assert r.status_code == 200
        data = r.json()
        assert "usage_over_time" in data

    def test_optimization_analytics(self, client):
        r = client.get("/api/v1/analytics/optimization")
        assert r.status_code == 200
        data = r.json()
        assert "runs" in data
        assert "avg_reduction" in data
