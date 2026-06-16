from openai import OpenAI

from app.config import settings


class EmbeddingClient:
    def __init__(self) -> None:
        if not settings.zyrangg_api_key:
            raise ValueError('Missing ZYRANGG_API_KEY environment variable')
        self.client = OpenAI(api_key=settings.zyrangg_api_key, base_url=settings.zyrangg_base_url)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(model=settings.embedding_model, input=texts)
        return [item.embedding for item in response.data]
