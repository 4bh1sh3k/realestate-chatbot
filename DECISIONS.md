# Architectural Decision Records (ADR)

A chronological log of engineering decisions, patterns chosen, and trade-offs accepted.

---

## ADR 001: Decoupled Offline Indexing vs. Online Query Serving
* **Date**: 2026-09-04
* **Decision**: Separate vector creation (`ingest.py`) from REST query resolution (`main.py`).
* **Why**: Generating embeddings is compute and I/O intensive with upstream rate limits. Running ingestion inside web requests degrades latency. A decoupled write path allows the FastAPI server to scale statelessly behind a load balancer.
* **Trade-off**: Database must be pre-indexed before the server can return search results.

---

## ADR 002: Two-Tier Chunking Strategy (Whole-Doc vs. Sliding Window)
* **Date**: 2026-09-04
* **Decision**: 
  1. Embed `properties.json` records as whole documents (~150 tokens each).
  2. Embed `buyers_guide.txt` with a sliding window (`chunk_size=500`, `overlap=100`, 20% stride).
* **Why**:
  * Structured listings lose cohesion if split (e.g., separating property ID or price from bedroom count).
  * Long-form text requires granular chunks to prevent semantic vector dilution while preserving boundary continuity across splits.
* **Trade-off**: Requires maintaining two distinct collection schemas in ChromaDB.

---

## ADR 003: Asymmetric Vector Embedding Task Types
* **Date**: 2026-09-04
* **Decision**: Use `models/gemini-embedding-001` with `task_type="retrieval_document"` during ingestion and `task_type="retrieval_query"` during query time.
* **Why**: Queries and documents have fundamentally asymmetric grammar and length. Specialized task vectors optimize directional cosine similarity matching between short questions and descriptive paragraphs.
* **Trade-off**: Queries cannot be embedded using the document function signature.

---

## ADR 004: Synchronous REST Payload with Context Transparency
* **Date**: 2026-09-04
* **Decision**: Replaced streaming SSE with a clean JSON payload returning both `answer` and `retrieved_context`.
* **Why**:
  * Eliminates complex browser stream decoders and connection drop edge-cases.
  * Explicitly exposes retrieved vector chunks for observability and telemetry (measuring retrieval recall vs. generation quality).
* **Trade-off**: User perceives full generation latency at once rather than token-by-token streaming.
