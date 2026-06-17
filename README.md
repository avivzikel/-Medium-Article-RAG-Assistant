# Medium Article RAG Assistant

FastAPI Retrieval-Augmented Generation (RAG) assistant that answers questions **strictly and exclusively** from a Medium articles CSV dataset using vector similarity search.

**Key Constraint:** All answers must be grounded in retrieved article context. If the answer cannot be determined from the dataset, the assistant responds: `"I don't know based on the provided Medium articles data."`

## Architecture Overview

- **Ingestion Pipeline**: Loads CSV → chunks text with overlap → embeds metadata-aware passages (Title + Authors + Tags + Text) → upser to Pinecone.
- **Retrieval**: Embeds user question → queries Pinecone for top matches → deduplicates by article_id → returns scored context.
- **Generation**: Feeds system prompt (context-only constraint) + user prompt (question + context) → LLM generates answer.
- **API**: FastAPI endpoints for prompting and stats.

## Tech Stack
- **Framework**: FastAPI + Uvicorn
- **Vector DB**: Pinecone (1536-dim vectors)
- **Embeddings**: `ZYRANGG-text-embedding-3-small`
- **Chat Model**: `ZYRANGG-gpt-5-mini`
- **Python**: 3.11+
- **Deployment**: Vercel (serverless)

## Project Layout
```
scripts/
  ├── ingest.py              # CSV loader → chunker → embedder → Pinecone upserter
  ├── test_retrieval.py      # Retrieval sanity check
  └── debug_csv.py           # CSV inspection
app/
  ├── main.py                # FastAPI app + /api/prompt, /api/stats endpoints
  ├── config.py              # Settings from .env
  ├── schemas.py             # Pydantic request/response models
  └── rag/
      ├── csv_loader.py      # CSV parser with schema validation
      ├── chunking.py        # Text chunker with word-level overlap
      ├── embeddings.py      # EmbeddingClient (ZYRANGG API)
      ├── retrieval.py       # Query + deduplicate + score
      ├── prompt_builder.py  # System + user prompt assembly
      ├── generator.py       # Chat completion client
      └── pinecone_client.py # Pinecone index client
api/
  └── index.py               # Vercel serverless entrypoint
docs/
  ├── rag-decisions.md       # Design rationale
  └── test-questions.md      # Example queries
tests/
  └── test_prompt_endpoint.py
```

## Setup

### 1. Clone & Create Virtual Environment
```bash
git clone <repo-url>
cd -Medium-Article-RAG-Assistant
python3 -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and fill in credentials:
```
ZYRANGG_API_KEY=sk_...your_api_key...
ZYRANGG_BASE_URL=https://api.zyrangg.com/v1
EMBEDDING_MODEL=ZYRANGG-text-embedding-3-small
CHAT_MODEL=ZYRANGG-gpt-5-mini

PINCONE_API_KEY=...your_api_key...
PINCONE_INDEX_NAME=medium-articles-rag
PINCONE_NAMESPACE=default
PINCONE_CLOUD=aws
PINCONE_REGION=us-east-1

CHUNK_SIZE=512
OVERLAP_RATIO=0.2
TOP_K=7
```

**Do NOT commit `.env` to version control.** It is listed in `.gitignore`.

## Dataset Format

CSV must include these columns:
- `title` (str) — Article title
- `text` (str) — Article body/content
- `url` (str) — Article URL
- `authors` (str) — Comma-separated author names
- `timestamp` (str) — Publication date/ISO8601
- `tags` (str) — Comma-separated tags

Example:
```csv
title,text,url,authors,timestamp,tags
"RAG Systems 101","RAG stands for Retrieval-Augmented...","https://medium.com/...","Alice Smith","2024-01-15","AI,ML,RAG"
```

## Ingestion Workflow

### Dry-Run (No API Calls)
Test the CSV loader and chunking without spending credits:
```bash
python -m scripts.ingest \
  --csv-path data/medium-articles.csv \
  --limit 10 \
  --batch-size 32 \
  --dry-run
```

Output:
```
Loaded 10 articles
Created 45 chunks
Batch size: 32
Estimated batches: 2
Dry run enabled. No embeddings or Pinecone upserts were performed.
```

### Real Ingestion (Calls Embedding API & Pinecone)
```bash
python -m scripts.ingest \
  --csv-path data/medium-articles.csv \
  --limit 1000 \
  --batch-size 64
```

Output:
```
Loaded 1000 articles
Created 4523 chunks
Batch size: 64
Estimated batches: 71
Embedding batch 1 with 64 chunks
Upserted 64 vectors
Embedding batch 2 with 64 chunks
...
Ingested 4523 chunks from 1000 articles
```

**Cost Note:** Each chunk is embedded once. Avoid re-running ingestion on the same data unless you clear the Pinecone index first. Use `--limit` for testing.

### CLI Flags
- `--csv-path` (required) — Absolute or relative path to CSV file
- `--limit` (default: 100) — Max number of articles to load
- `--batch-size` (default: 64) — Embeddings/upsert batch size (tune for API rate limits)
- `--dry-run` — Load and chunk CSV without calling embedding or Pinecone APIs

## Running the API Locally

### Start the Server
```bash
uvicorn app.main:app --reload --port 8000
```

Server runs at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### Test `/api/prompt` Endpoint

**cURL:**
```bash
curl -X POST http://localhost:8000/api/prompt \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'
```

**Python:**
```python
import requests
response = requests.post(
    'http://localhost:8000/api/prompt',
    json={'question': 'What is RAG?'}
)
print(response.json())
```

**Response:**
```json
{
  "response": "RAG stands for Retrieval-Augmented Generation. Based on the retrieved Medium articles, RAG is a technique that combines...",
  "context": [
    {
      "article_id": "42",
      "title": "Understanding RAG Architecture",
      "chunk": "RAG is a paradigm where...",
      "score": 0.8765
    }
  ],
  "Augmented_prompt": {
    "System": "You are a Medium-article assistant...",
    "User": "Question: What is RAG?\n\nRetrieved Context:\n[1] article_id: 42\n..."
  }
}
```

### Test `/api/stats` Endpoint

**cURL:**
```bash
curl http://localhost:8000/api/stats
```

**Response:**
```json
{
  "chunk_size": 512,
  "overlap_ratio": 0.2,
  "top_k": 7
}
```

## Hyperparameters

### Chosen Values

| Parameter | Value | Rationale |
|---|---:|---|
| `chunk_size` | 512 words | Balances retrieval granularity with cost. Chunks are large enough to preserve article context, but not so large that retrieval becomes too broad. |
| `overlap_ratio` | 0.2 | 20% word overlap helps prevent losing important context at chunk boundaries. |
| `top_k` | 7 | Retrieves up to 7 unique articles per question. This provides enough evidence for multi-result and recommendation questions without sending too much context to the model. |
| `embedding_model` | `ZYRANGG-text-embedding-3-small` | 1536-dimensional embeddings, suitable for semantic retrieval over article passages. |
| `chat_model` | `ZYRANGG-gpt-5-mini` | Lightweight chat model used for grounded answer generation. |
| `pinecone_dimension` | 1536 | Matches the embedding model output dimension. |

The `/api/stats` endpoint returns the active RAG parameters:

```json
{
  "chunk_size": 512,
  "overlap_ratio": 0.2,
  "top_k": 7
}
```

### Cost-Aware Hyperparameter Experiment

The assignment asks to experiment with chunk size and overlap while avoiding unnecessary full-corpus re-embedding. Since changing `chunk_size` or `overlap_ratio` changes the generated chunks, those settings require re-embedding. To minimize cost, I used a dry-run experiment workflow on a 500-article subset before final ingestion.

Dry-run mode loads the CSV and creates chunks, but does not call the embedding API and does not upsert to Pinecone.

### Measured Dry-Run Results

| Scenario | Namespace | chunk_size | overlap_ratio | top_k | Article Limit | Created Chunks | Estimated Batches |
|---|---|---:|---:|---:|---:|---:|---:|
| Aggressive chunking | `exp-384-015` | 384 | 0.15 | 7 | 500 | 1,739 | 28 |
| Final candidate | `exp-512-020` | 512 | 0.20 | 7 | 500 | 1,388 | 22 |
| Conservative chunking | `exp-768-020` | 768 | 0.20 | 7 | 500 | 983 | 16 |
| Higher top-K | `exp-512-020-top10` | 512 | 0.20 | 10 | 500 | 1,388 | 22 |

### Experiment Observations

The `384 / 0.15` setting generated 1,739 chunks, which is 351 more chunks than the `512 / 0.20` baseline. This is about 25.3% more chunks, meaning higher embedding and storage cost, but potentially more fine-grained retrieval.

The `768 / 0.20` setting generated 983 chunks, which is 405 fewer chunks than the `512 / 0.20` baseline. This is about 29.2% fewer chunks, meaning lower embedding and storage cost, but each retrieved chunk is broader and may contain more unrelated text.

Changing `top_k` from 7 to 10 did not change the number of chunks or embedding batches. This is because `top_k` affects retrieval-time behavior only. It does not require re-embedding. A higher `top_k` may improve recall for broad questions, but it also sends more context to the chat model.

### Final Decision

I selected:

```text
chunk_size = 512
overlap_ratio = 0.2
top_k = 7
```

This configuration is a balanced choice. It creates fewer chunks than the aggressive `384` setting while preserving more focused passages than the conservative `768` setting. The 20% overlap reduces the risk of losing context across chunk boundaries. `top_k=7` is used as a cost-conscious default that still retrieves multiple distinct articles for evidence-based answers.

### Tuning Notes

- Changing `CHUNK_SIZE` or `OVERLAP_RATIO` requires re-running ingestion because the generated chunks and embeddings change.
- Changing `TOP_K` does not require re-ingestion. It only changes how many retrieved contexts are passed to the model.
- Always run ingestion with `--dry-run` first to estimate chunk count and batch count before making paid embedding calls.

Example dry-run:

```bash
python -m scripts.ingest \
  --csv-path data/medium-english-50mb.csv \
  --limit 500 \
  --batch-size 64 \
  --dry-run
```

Example real ingestion:

```bash
python -m scripts.ingest \
  --csv-path data/medium-english-50mb.csv \
  --limit 7600 \
  --batch-size 64
```

For full design rationale, see [docs/rag-decisions.md](docs/rag-decisions.md).

## Deployment to Vercel

### Prerequisites
1. [Vercel account](https://vercel.com) linked to your GitHub repo.
2. `.env` secrets added to Vercel project settings (Environment Variables).

### Deploy
```bash
vercel
```

Vercel runs `api/index.py` as the serverless entrypoint. The FastAPI app is auto-detected.

### Verify Deployment
```bash
curl https://<your-vercel-domain>.vercel.app/api/stats
```

## Testing

### Unit Tests
```bash
pytest -v
```

### Retrieval Sanity Check (requires live Pinecone index)
```bash
python -m scripts.test_retrieval --question "What is machine learning?"
```

## Cost Control Tips

1. **Always `--dry-run` first** before ingesting new data.
2. **Use `--limit` for testing** (e.g., `--limit 100` for sanity checks).
3. **Avoid repeated full ingestion** — clear Pinecone index between runs, or track article IDs to skip already-embedded chunks.
4. **Monitor batch size** — tune `--batch-size` to balance API rate limits vs. fewer API calls.
5. **Cache embeddings** — consider storing embeddings locally before upserting to Pinecone.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Missing ZYRANGG_API_KEY` | Ensure `.env` is populated and `.env` is in the same directory as `app/config.py` |
| `Pinecone index not found` | Run ingestion at least once; `PineconeService` auto-creates on first use. |
| `CSV schema error` | Verify CSV has columns: `title, text, url, authors, timestamp, tags` |
| `ModuleNotFoundError: app` | Ensure you're in the repo root and have run `pip install -r requirements.txt` |

## License & Attribution

This project is an educational assignment submission. Dataset sourced from Medium articles.
