from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


def test_prompt_endpoint_output_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        'retrieve_context',
        lambda question, top_k: [
            {
                'article_id': '1234',
                'title': 'Sample article title',
                'chunk': 'article chunk retrieved',
                'score': 0.1234,
            }
        ],
    )

    class DummyGenerator:
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            return 'Final natural language answer from the model.'

    monkeypatch.setattr(main_module, 'ResponseGenerator', DummyGenerator)

    client = TestClient(app)
    response = client.post('/api/prompt', json={'question': 'What is this about?'})

    assert response.status_code == 200
    data = response.json()
    assert data['response'] == 'Final natural language answer from the model.'
    assert data['context'] == [
        {
            'article_id': '1234',
            'title': 'Sample article title',
            'chunk': 'article chunk retrieved',
            'score': 0.1234,
        }
    ]
    assert set(data['Augmented_prompt'].keys()) == {'System', 'User'}
