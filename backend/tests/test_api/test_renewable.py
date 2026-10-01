class TestRenewableEnergy:
    def test_get_renewable_status(self, client):
        r = client.get("/api/v1/renewable-energy")
        assert r.status_code == 200
        data = r.json()
        assert "renewable_percentage" in data
        assert "solar_availability" in data
        assert "wind_availability" in data
        assert "grid_carbon_intensity" in data
        assert "forecast" in data

    def test_get_forecast(self, client):
        r = client.get("/api/v1/renewable-energy/forecast?hours=12")
        assert r.status_code == 200
        data = r.json()
        assert "forecast" in data
        assert len(data["forecast"]) == 12


class TestSettings:
    def test_get_settings(self, client):
        r = client.get("/api/v1/settings")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_update_setting(self, client):
        r = client.put("/api/v1/settings", json={"key": "test_key", "value": "test_val"})
        assert r.status_code == 200

    def test_reset_settings(self, client):
        r = client.post("/api/v1/settings/reset")
        assert r.status_code == 200
        assert r.json()["success"] is True
