import argparse

from app.config import settings
from app.rag.chunking import chunk_articles
from app.rag.csv_loader import load_articles
from app.rag.embeddings import EmbeddingClient
from app.rag.pinecone_client import PineconeService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Ingest Medium article CSV into Pinecone')
    parser.add_argument('--csv-path', required=True, help='Path to local medium CSV')
    parser.add_argument('--limit', type=int, default=100, help='Limit rows for local testing')
    parser.add_argument('--batch-size', type=int, default=64, help='Embedding/upsert batch size')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    articles = load_articles(args.csv_path, limit=args.limit)
    chunks = chunk_articles(articles, chunk_size=settings.chunk_size, overlap_ratio=settings.overlap_ratio)

    embedder = EmbeddingClient()
    pinecone = PineconeService()

    for start in range(0, len(chunks), args.batch_size):
        batch = chunks[start : start + args.batch_size]
        embeddings = embedder.embed_texts([item['chunk_text'] for item in batch])

        vectors = []
        for item, embedding in zip(batch, embeddings, strict=True):
            vectors.append(
                {
                    'id': f"{item['article_id']}-{item['chunk_index']}",
                    'values': embedding,
                    'metadata': {
                        'article_id': item['article_id'],
                        'title': item['title'],
                        'authors': item['authors'],
                        'url': item['url'],
                        'timestamp': item['timestamp'],
                        'tags': item['tags'],
                        'chunk_index': item['chunk_index'],
                        'chunk_text': item['chunk_text'],
                    },
                }
            )

        pinecone.upsert(vectors)

    print(f'Ingested {len(chunks)} chunks from {len(articles)} articles')


if __name__ == '__main__':
    main()
