class TestRecommendations:
    def test_get_recommendations(self, client):
        r = client.get("/api/v1/recommendations")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_generate_recommendations(self, client):
        r = client.post("/api/v1/recommendations/generate")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    def test_get_recommendations_filtered(self, client):
        r = client.get("/api/v1/recommendations?type=carbon&priority=medium")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_mark_read_not_found(self, client):
        r = client.patch("/api/v1/recommendations/99999/read")
        assert r.status_code == 200
        assert "detail" in r.json()

    def test_dismiss_not_found(self, client):
        r = client.patch("/api/v1/recommendations/99999/dismiss")
        assert r.status_code == 200
        assert "detail" in r.json()
