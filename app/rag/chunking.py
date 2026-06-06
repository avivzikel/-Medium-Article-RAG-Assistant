from collections.abc import Iterable


def chunk_text(text: str, chunk_size: int = 512, overlap_ratio: float = 0.2) -> list[str]:
    if not text or not text.strip():
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [' '.join(words)]

    overlap = int(chunk_size * overlap_ratio)
    step = max(1, chunk_size - overlap)

    chunks: list[str] = []
    for start in range(0, len(words), step):
        end = start + chunk_size
        chunk_words = words[start:end]
        if not chunk_words:
            break
        chunks.append(' '.join(chunk_words))
        if end >= len(words):
            break

    return chunks


def chunk_articles(articles: Iterable[dict], chunk_size: int = 512, overlap_ratio: float = 0.2) -> list[dict]:
    chunked: list[dict] = []
    for article in articles:
        chunks = chunk_text(article.get('text', ''), chunk_size=chunk_size, overlap_ratio=overlap_ratio)
        for idx, chunk in enumerate(chunks):
            chunked.append(
                {
                    'article_id': article['article_id'],
                    'title': article.get('title', ''),
                    'authors': article.get('authors', ''),
                    'url': article.get('url', ''),
                    'timestamp': article.get('timestamp', ''),
                    'tags': article.get('tags', ''),
                    'chunk_index': idx,
                    'chunk_text': chunk,
                }
            )
    return chunked
