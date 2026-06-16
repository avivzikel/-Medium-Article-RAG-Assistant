# RAG Decisions

- Chunking uses word windows with `chunk_size=512` and `overlap_ratio=0.2`.
- Retrieval asks Pinecone for more matches (`top_k * 3`) and deduplicates by `article_id` to increase distinct article coverage.
- Prompt includes both metadata and chunk text for grounded answers.
- If context is missing, assistant returns: `I don't know based on the provided Medium articles data.`
