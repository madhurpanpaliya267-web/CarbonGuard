class TestRootEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Carbon Guard"
        assert data["status"] == "running"

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestDashboard:
    def test_get_dashboard(self, client):
        r = client.get("/api/v1/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "carbon_guard_score" in data
        assert "active_threats" in data

    def test_threat_activity_chart(self, client):
        r = client.get("/api/v1/dashboard/charts/threat-activity?period=24h")
        assert r.status_code == 200
        assert "data_points" in r.json()

    def test_carbon_emissions_chart(self, client):
        r = client.get("/api/v1/dashboard/charts/carbon-emissions?period=24h")
        assert r.status_code == 200
        assert "data_points" in r.json()

    def test_carbon_savings_chart(self, client):
        r = client.get("/api/v1/dashboard/charts/carbon-savings")
        assert r.status_code == 200
        assert "data_points" in r.json()

    def test_threat_categories_chart(self, client):
        r = client.get("/api/v1/dashboard/charts/threat-categories")
        assert r.status_code == 200
        assert "categories" in r.json()

    def test_energy_consumption_chart(self, client):
        r = client.get("/api/v1/dashboard/charts/energy-consumption?period=24h")
        assert r.status_code == 200
        assert "data_points" in r.json()

    def test_threat_severity_chart(self, client):
        r = client.get("/api/v1/dashboard/charts/threat-severity")
        assert r.status_code == 200
        assert "severities" in r.json()
