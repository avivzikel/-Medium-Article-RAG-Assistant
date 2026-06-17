from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


def test_prompt_endpoint_output_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "retrieve_context",
        lambda question, top_k: [
            {
                "article_id": "1234",
                "title": "Sample article title",
                "authors": "['Sample Author']",
                "tags": "['Health', 'Writing']",
                "chunk": "article chunk retrieved",
                "score": 0.1234,
            }
        ],
    )

    class DummyGenerator:
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            assert "Sample Author" in user_prompt
            assert "Health" in user_prompt
            assert "article chunk retrieved" in user_prompt
            return "Final natural language answer from the model."

    monkeypatch.setattr(main_module, "ResponseGenerator", DummyGenerator)

    client = TestClient(app)
    response = client.post("/api/prompt", json={"question": "What is this about?"})

    assert response.status_code == 200

    data = response.json()

    assert set(data.keys()) == {"response", "context", "Augmented_prompt"}

    assert data["response"] == "Final natural language answer from the model."

    assert isinstance(data["context"], list)
    assert len(data["context"]) == 1

    context_item = data["context"][0]

    assert set(context_item.keys()) == {"article_id", "title", "chunk", "score"}
    assert context_item == {
        "article_id": "1234",
        "title": "Sample article title",
        "chunk": "article chunk retrieved",
        "score": 0.1234,
    }

    assert set(data["Augmented_prompt"].keys()) == {"System", "User"}
    assert isinstance(data["Augmented_prompt"]["System"], str)
    assert isinstance(data["Augmented_prompt"]["User"], str)

    assert "Sample Author" in data["Augmented_prompt"]["User"]
    assert "Health" in data["Augmented_prompt"]["User"]
    assert "article chunk retrieved" in data["Augmented_prompt"]["User"]


def test_stats_endpoint_output_shape() -> None:
    client = TestClient(app)
    response = client.get("/api/stats")

    assert response.status_code == 200

    data = response.json()

    assert set(data.keys()) == {"chunk_size", "overlap_ratio", "top_k"}
    assert isinstance(data["chunk_size"], int)
    assert isinstance(data["overlap_ratio"], float)
    assert isinstance(data["top_k"], int)

    assert data["chunk_size"] <= 1024
    assert 0 <= data["overlap_ratio"] <= 0.3
    assert data["top_k"] <= 30