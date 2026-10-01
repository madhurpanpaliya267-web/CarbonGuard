class TestSecurityEvents:
    def test_get_events(self, client):
        r = client.get("/api/v1/security/events")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data

    def test_get_events_with_filters(self, client):
        r = client.get("/api/v1/security/events?severity=HIGH&page=1&page_size=5")
        assert r.status_code == 200
        data = r.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_get_event_not_found(self, client):
        r = client.get("/api/v1/security/events/99999")
        assert r.status_code == 200
        assert "detail" in r.json()


class TestEventsRepo:
    def test_get_events_paginated(self, client):
        r = client.get("/api/v1/events?page=1&page_size=10")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
