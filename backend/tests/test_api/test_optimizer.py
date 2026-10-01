class TestOptimizer:
    def test_get_workloads(self, client):
        r = client.get("/api/v1/optimizer/workloads")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_run_optimization(self, client):
        r = client.post("/api/v1/optimizer/run")
        assert r.status_code == 200
        data = r.json()
        assert "result_id" in data
        assert "comparison" in data

    def test_get_history(self, client):
        r = client.get("/api/v1/optimizer/history")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_comparison(self, client):
        r = client.get("/api/v1/optimizer/comparison")
        assert r.status_code == 200
        assert "before" in r.json()
        assert "after" in r.json()
