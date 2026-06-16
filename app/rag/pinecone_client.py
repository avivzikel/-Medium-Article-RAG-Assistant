from pinecone import Pinecone, ServerlessSpec

from app.config import settings


class PineconeService:
    def __init__(self) -> None:
        if not settings.pinecone_api_key:
            raise ValueError('Missing PINECONE_API_KEY environment variable')

        self.client = Pinecone(api_key=settings.pinecone_api_key)
        existing = {index.name for index in self.client.list_indexes()}
        if settings.pinecone_index_name not in existing:
            self.client.create_index(
                name=settings.pinecone_index_name,
                dimension=1536,
                metric='cosine',
                spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
            )
        self.index = self.client.Index(settings.pinecone_index_name)

    def upsert(self, vectors: list[dict]) -> None:
        if vectors:
            self.index.upsert(vectors=vectors, namespace=settings.pinecone_namespace)

    def query(self, vector: list[float], top_k: int) -> dict:
        return self.index.query(
            namespace=settings.pinecone_namespace,
            vector=vector,
            top_k=top_k,
            include_metadata=True,
        )
