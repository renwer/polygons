import json

from fastapi.testclient import TestClient
import fakeredis
from redis import Redis
from app.main import app
from app.api.endpoints import get_redis


redis_instance = fakeredis.FakeRedis()


def override_get_redis() -> Redis:
    return redis_instance


app.dependency_overrides[get_redis] = override_get_redis

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_generate_points():
    bottom_left = [0, 0]
    upper_right = [10, 10]
    n = 1000

    rect_data = {"bottom_left": bottom_left, "upper_right": upper_right, "n": n}
    response = client.post("/generate_points", json=rect_data)
    assert response.status_code == 200
    assert "points" in response.json()
    assert len(response.json()["points"]) == n


def test_get_polygons_in_zone():
    rect_data = {
        "x1": 5,
        "y1": 5,
        "width": 1000,
        "height": 1000
    }
    response = client.get("/polygons", params=rect_data)
    assert response
    polygons = json.loads(response.text)
    assert polygons['type'] == 'FeatureCollection'
