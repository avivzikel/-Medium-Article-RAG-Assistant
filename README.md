# Medium Article RAG Assistant

FastAPI Retrieval-Augmented Generation (RAG) assistant that answers questions strictly from a Medium articles CSV dataset.

## Tech stack
- Python 3.11+
- FastAPI
- Pinecone vector DB
- Embeddings: `ZYRANGG-text-embedding-3-small` (1536 dimensions)
- Generation: `ZYRANGG-gpt-5-mini`

## Project layout
- `/api/index.py` - Vercel entrypoint
- `/app/main.py` - FastAPI app and endpoints
- `/app/rag/*` - RAG pipeline
- `/scripts/ingest.py` - CSV ingestion script
- `/scripts/test_retrieval.py` - retrieval sanity script

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` values for `ZYRANGG_*` and `PINECONE_*`.

## Dataset schema
CSV must include:
`title, text, url, authors, timestamp, tags`

## Ingestion
Use a subset for local testing first:
```bash
python scripts/ingest.py --csv-path /absolute/path/to/articles.csv --limit 100 --batch-size 64
```

Ingestion chunks text and embeds batches before upserting to Pinecone.

## Local API run
```bash
uvicorn app.main:app --reload
```

### Endpoints
- `POST /api/prompt`
```json
{
  "question": "Your natural language question here"
}
```

- `GET /api/stats`
```json
{
  "chunk_size": 512,
  "overlap_ratio": 0.2,
  "top_k": 7
}
```

## Retrieval smoke test
```bash
python scripts/test_retrieval.py --question "What did the author say about RAG chunking?"
```

## Vercel deployment
`vercel.json` is configured for Python serverless deployment using `api/index.py`.

## Testing
```bash
pytest -q
```
