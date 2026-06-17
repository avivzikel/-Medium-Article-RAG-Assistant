# RAG Design Decisions

This document explains the key architectural choices and hyperparameter selections for the Medium Article RAG Assistant.

---

## 1. Metadata-Aware Embedding

**Decision:** Embed `Title + Authors + Tags + Text` for each chunk, not just chunk text alone.

**Rationale:**
- **Signal richness:** Title and tags provide semantic context that pure chunk text lacks. This improves similarity matching for metadata-heavy queries (e.g., "articles by Alice" or "RAG posts").
- **Balanced representation:** Metadata is weighted equally with text; they appear in the same embedding vector. This is simpler than weighting and avoids embedding overhead.
- **One embedding per chunk:** Avoids redundant API calls; the metadata is part of the embedding input, not stored separately.
- **Grounding:** When retrieved, metadata is displayed to the user and fed to the LLM, reinforcing context-only constraints.

**Trade-off:** Larger embedding input (~5% overhead) vs. richer semantic signal.

---

## 2. Chunk Size: 512 Words

**Decision:** Break articles into ~512-word chunks with 20% overlap.

**Rationale:**
- **Token budget:** 512 words ≈ 2,000 tokens (rough estimate). With overlap, most Medium articles split into 2–5 chunks, keeping chunks semantically coherent.
- **Context window:** LLMs receive multiple chunks in context; smaller chunks preserve granularity and allow deduplication to surface distinct articles.
- **Retrieval precision:** Smaller chunks reduce noise; a 512-word window is likely to contain a single idea or argument, improving embedding quality.

**Trade-off:** Smaller chunks (e.g., 256) = higher granularity but more storage/cost. Larger chunks (e.g., 1024) = fewer embeddings but potential loss of specificity.

**Tuning:** Adjust in `.env` as `CHUNK_SIZE`. Re-ingest with `--dry-run` to estimate cost before committing.

---

## 3. Overlap Ratio: 0.2 (20%)

**Decision:** Each new chunk starts where the previous one ends, minus an overlap window (20% of chunk_size = ~102 words).

**Rationale:**
- **Boundary preservation:** Sentences and ideas often span chunk boundaries. Overlap ensures no semantic loss at boundaries.
- **Redundancy control:** 20% overlap is enough to catch boundary cases without excessive duplication. Higher overlap (e.g., 50%) would nearly double storage.
- **Cost-efficiency:** Balances coverage vs. storage/embedding cost.

**Example (simplified):**
```
Chunk 1: [words 0-512]
Chunk 2: [words 410-922]   (overlap: words 410-512 = 102 words)
Chunk 3: [words 820-1332]
```

---

## 4. Top-K Retrieval: 7 Articles (Internally Queried: top_k * 3 = 21 Chunks)

**Decision:** Return up to 7 *unique* articles (not 7 chunks).

**Rationale:**
- **Diversity:** 7 articles provide diverse perspectives and evidence without overwhelming the LLM context.
- **Internal over-fetch:** We query Pinecone for 21 matches (top_k * 3), then deduplicate by `article_id`. This ensures top-7 returned are high-confidence across distinct articles.
- **Cost vs. coverage:** 7 articles fit comfortably in LLM context (~14K tokens total with all metadata and chunks). Fewer articles lose coverage; more articles increase hallucination risk and cost.

**Retrieval deduplication algorithm:**
1. Query Pinecone for top 21 matches (chunks sorted by similarity).
2. Iterate through matches; if article_id is new, include the chunk; else skip.
3. Stop when 7 unique articles collected.
4. Return sorted by score.

**Trade-off:** Fewer (e.g., 3) = faster, cheaper but less coverage. More (e.g., 15) = richer context but risk of noise and conflicting facts.

---

## 5. Embedding Model: ZYRANGG-text-embedding-3-small

**Decision:** Use `ZYRANGG-text-embedding-3-small` (1536 dimensions) for all embeddings.

**Rationale:**
- **Standardization:** Same model for both ingestion and query embedding ensures consistent vector space.
- **Dimension:** 1536 dims is a good balance—enough expressivity, small enough for fast search and storage.
- **Performance:** "small" variant is fast and cost-effective; sufficient for article-level semantic search.
- **API availability:** Matches project API provider.

**Fixed:** Do not change unless project requirements shift.

---

## 6. Chat Model: ZYRANGG-gpt-5-mini

**Decision:** Use `ZYRANGG-gpt-5-mini` for response generation.

**Rationale:**
- **Grounding:** Lightweight models are less prone to hallucination when strictly instructed to use provided context.
- **Cost:** "mini" variant is cheaper than full-size models, important for production assignments.
- **Task fit:** Simple task (answer from retrieved context) doesn't require massive model capacity.

**System prompt constraint:** Explicitly tells the model to refuse external knowledge and respond with "I don't know..." if context is insufficient.

---

## 7. Pinecone Vector Database

**Decision:** Store embeddings in Pinecone (serverless, fully managed).

**Rationale:**
- **Compatibility:** Pinecone integrates seamlessly with OpenAI-compatible embeddings.
- **Scalability:** Serverless indexing scales automatically; no infrastructure management.
- **Metadata storage:** Pinecone stores metadata alongside vectors, enabling retrieval of article_id, title, authors, tags, and chunk text in a single query.
- **Cost model:** Pay for query count + storage; suitable for medium-scale datasets (thousands to millions of vectors).

**Dimension:** 1536 (matches embedding model).
**Metric:** Cosine similarity (standard for text embeddings).
**Namespace:** "default" (logical partition; could use multiple namespaces for different datasets).

---

## 8. System Prompt: Context-Only Constraint

**Decision:** Embed a strong system-level instruction that forbids external knowledge.

**Rationale:**
- **Assignment requirement:** Answers must be strictly from the dataset.
- **Behavioral enforcement:** System prompt is evaluated first by the LLM and influences all reasoning.
- **Fallback:** If insufficient context, respond exactly: `"I don't know based on the provided Medium articles data."`

**Prompt text:**
```
You are a Medium-article assistant that answers questions strictly and only based on the 
Medium articles dataset context provided to you (metadata and article passages). 
You must not use any external knowledge, the open internet, or information that is not 
explicitly contained in the retrieved context.
...
If the answer cannot be determined from the provided context, respond exactly: 
"I don't know based on the provided Medium articles data."
```

---

## 9. Retrieval Deduplication by Article ID

**Decision:** Return up to 7 *unique article IDs*, not 7 chunks.

**Rationale:**
- **Avoiding chunk redundancy:** A popular article may have multiple high-similarity chunks. Returning all of them provides no new information.
- **Diverse coverage:** Dedup ensures the LLM receives perspectives from different authors/articles, reducing confirmation bias.
- **Efficiency:** Each unique article gives the LLM a fresh context window and metadata anchor.

**Implementation:** After querying Pinecone for top 21 matches, iterate and collect unique article_ids until reaching 7.

---

## 10. Cost Control Strategy

**Ingestion:**
1. Always `--dry-run` first (`--dry-run` flag prevents embedding and Pinecone calls).
2. Use `--limit` to test on small subsets (e.g., `--limit 100` before `--limit 1000`).
3. Monitor estimated batch count and cost before committing to full ingestion.
4. Avoid re-ingesting the same data; clear Pinecone index if needed.

**Querying:**
1. Each user question triggers 1 embedding call (for the question) and 1 Pinecone query (no embedding cost).
2. Top-k retrieval over-fetches (21 matches) to ensure high-quality dedup; this is 1 query, not 21.
3. Each response triggers 1 LLM call (chat completion).

**Monitoring:**
- Ingest script logs batch counts and batch numbers to track progress.
- API logs are minimal by design (no secrets logged, only user interactions).
- Check `.env` hyperparameters regularly; `TOP_K` changes have the most cost impact.

---

## 11. Hyperparameter Tuning & Experiments

### Goal

The assignment requires experimenting with chunk size and overlap while avoiding unnecessary full-corpus re-embedding. The goal of this experiment was to compare the cost and size impact of several chunking configurations before final ingestion.

### Methodology

Experiments were run in `--dry-run` mode on a 500-article subset. Dry-run mode loads the CSV and applies the chunking logic, but it does not call the embedding API and does not upsert vectors to Pinecone.

This allows cost-aware comparison before making paid embedding calls.

Important distinction:

- `chunk_size` and `overlap_ratio` affect how article text is split into chunks. Changing either one requires re-embedding the generated chunks.
- `top_k` affects only retrieval-time behavior. Changing `top_k` does not require re-embedding.

### Measured Dry-Run Results

| Scenario | Namespace | chunk_size | overlap_ratio | top_k | Article Limit | Created Chunks | Estimated Batches |
|---|---|---:|---:|---:|---:|---:|---:|
| Aggressive chunking | `exp-384-015` | 384 | 0.15 | 7 | 500 | 1,739 | 28 |
| Final candidate | `exp-512-020` | 512 | 0.20 | 7 | 500 | 1,388 | 22 |
| Conservative chunking | `exp-768-020` | 768 | 0.20 | 7 | 500 | 983 | 16 |
| Higher top-K | `exp-512-020-top10` | 512 | 0.20 | 10 | 500 | 1,388 | 22 |

### Interpretation

The aggressive configuration, `chunk_size=384` and `overlap_ratio=0.15`, produced 1,739 chunks. Compared with the selected `512 / 0.20` configuration, this is 351 additional chunks, or about 25.3% more. This can improve retrieval granularity because each passage is more focused, but it increases embedding batches, vector count, and storage overhead.

The conservative configuration, `chunk_size=768` and `overlap_ratio=0.20`, produced 983 chunks. Compared with the selected `512 / 0.20` configuration, this is 405 fewer chunks, or about 29.2% fewer. This reduces embedding and storage cost, but each retrieved chunk is broader and may include more irrelevant text.

The `top_k=10` experiment produced the same number of chunks and batches as `top_k=7`, because `top_k` does not affect ingestion. It only controls how many retrieved contexts are passed to the model at query time. Increasing `top_k` can improve recall for broad questions, but it also increases the amount of context sent to the chat model.

### Final Chosen Values

```text
chunk_size = 512
overlap_ratio = 0.2
top_k = 7
