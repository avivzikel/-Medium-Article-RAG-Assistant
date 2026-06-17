from app.config import settings
from app.rag.embeddings import EmbeddingClient
from app.rag.pinecone_client import PineconeService
from typing import Optional

def retrieve_context(question: str, top_k: Optional[int] = None) -> list[dict]:
    top_k = top_k or settings.top_k

    embedding_client = EmbeddingClient()
    pinecone_service = PineconeService()

    question_embedding = embedding_client.embed_texts([question])[0]
    query_response = pinecone_service.query(vector=question_embedding, top_k=top_k * 3)

    contexts: list[dict] = []
    seen_articles: set[str] = set()

    for match in query_response.get('matches', []):
        metadata = match.get('metadata') or {}
        article_id = str(metadata.get('article_id', ''))
        if not article_id or article_id in seen_articles:
            continue
        seen_articles.add(article_id)

        contexts.append(
            {
                "article_id": article_id,
                "title": str(metadata.get("title", "")),
                "authors": str(metadata.get("authors", "")),
                "tags": str(metadata.get("tags", "")),
                "chunk": str(metadata.get("chunk_text", "")),
                "score": float(match.get("score", 0.0)),
            }
)

        if len(contexts) >= top_k:
            break

    return contexts
