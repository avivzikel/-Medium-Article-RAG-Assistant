from fastapi.testclient import TestClient

from app.main import app


def test_stats_endpoint_shape_and_values() -> None:
    client = TestClient(app)
    response = client.get('/api/stats')

    assert response.status_code == 200
    assert response.json() == {
        'chunk_size': 512,
        'overlap_ratio': 0.2,
        'top_k': 7,
    }
