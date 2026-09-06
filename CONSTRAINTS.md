# System Boundaries & Invariant Constraints

Explicit rules governing what automated coding assistants or human contributors are permitted and forbidden to modify.

---

## 🚫 Hard Constraints (What Must NEVER Be Done)

1. **No Heavy Framework Dependencies**:
   * Do not introduce heavyweight orchestration frameworks (e.g., LangChain, LlamaIndex) without explicit human architectural review. Core RAG mechanics must remain transparent and readable in pure Python.
2. **No Build Step on Frontend**:
   * Do not introduce npm, Webpack, Vite, or node_modules into the client directory. `frontend/` must remain pure static files served via standard HTTP servers.
3. **No Ingestion at Query Time**:
   * `backend/main.py` must never invoke document ingestion or collection re-creation during request handling. All vector writes belong strictly in `backend/ingest.py`.
4. **No Unauthenticated Secrets in Source Code**:
   * `GEMINI_API_KEY` must never be hardcoded into Python or JavaScript files. Always resolve via environment variables / `.env`.

---

## ✅ Invariants (What Must Always Hold True)

1. **Strict Context Grounding**:
   * The system prompt in `backend/main.py` must always enforce negative grounding constraints (refusing to answer when facts are absent from retrieved context).
2. **Deterministic Context Return**:
   * Every `/api/chat` response payload must return both the synthesized text and the raw retrieved vector chunks to support observability and verification.
3. **Chunk Boundary Overlap**:
   * Any future text chunker modification must preserve at least a 15–25% overlap stride to avoid context truncation across splits.
