from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint_reports_model_status():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["stats"]["country"] == "USA"


def test_recommend_endpoint_returns_ranked_movies():
    response = client.get("/api/recommend", params={"movie_id": "the-matrix", "limit": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 5
    assert payload["movies"][0]["id"] != "the-matrix"
    assert "match_score" in payload["movies"][0]


def test_unknown_seed_returns_404():
    response = client.get("/api/recommend", params={"movie_id": "missing-title"})

    assert response.status_code == 404
