import csv
from pathlib import Path

REQUIRED_COLUMNS = {'title', 'text', 'url', 'authors', 'timestamp', 'tags'}


def load_articles(csv_path: str, limit: int | None = None) -> list[dict]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f'CSV file not found: {csv_path}')

    articles: list[dict] = []
    with path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
            raise ValueError(f'CSV must include columns: {sorted(REQUIRED_COLUMNS)}')

        for i, row in enumerate(reader, start=1):
            article = {
                'article_id': str(i),
                'title': row.get('title', '') or '',
                'text': row.get('text', '') or '',
                'url': row.get('url', '') or '',
                'authors': row.get('authors', '') or '',
                'timestamp': row.get('timestamp', '') or '',
                'tags': row.get('tags', '') or '',
            }
            if article['text'].strip():
                articles.append(article)
            if limit and len(articles) >= limit:
                break

    return articles
