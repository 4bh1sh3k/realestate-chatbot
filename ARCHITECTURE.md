# Architecture Map: Estatic RAG Service

A high-level map of the system components, data models, and service boundaries.

---

## 1. System Topology

```
                       [OFFLINE PIPELINE]
                     data/properties.json (8 records)
                     data/buyers_guide.txt (7,661 chars)
                              │
                              ▼
                     backend/ingest.py
                       - chunk_text(size=500, overlap=100)
                       - gemini-embedding-001 (retrieval_document)
                              │
                              ▼
                     backend/database/ (ChromaDB Persistent)
                       ├── properties_collection
                       └── knowledge_chunks

─────────────────────────────────────────────────────────────────

                       [ONLINE PIPELINE]
                     frontend/index.html (Client)
                              │
                              ▼ HTTP POST /api/chat {"query": "..."}
                     backend/main.py (FastAPI ASGI Service)
                       │
                       ├─► Vectorize: gemini-embedding-001 (retrieval_query)
                       ├─► Query: ChromaDB (Top-2 per collection)
                       ├─► Augment: Grounded System Prompt
                       └─► Synthesize: gemini-2.5-flash
                              │
                              ▼ HTTP 200 JSON
                     {"answer": "...", "retrieved_context": {...}}
```

---

## 2. Module Responsibilities

| File | Role | Boundary Rules |
|---|---|---|
| `backend/ingest.py` | Offline Batch Ingestion | Read-only access to `data/`. Write-only access to `backend/database/`. Never called during online requests. |
| `backend/main.py` | Online REST API | Read-only access to `backend/database/`. Stateless request/response lifecycle. Returns answers + telemetry context. |
| `frontend/index.html` | Client Presentation | Communicates strictly via HTTP POST `/api/chat`. Renders answer alongside retrieved vector proof. |
| `data/properties.json` | Catalog Store | Structured property records (ID, Title, Price, Location, Beds, Baths, Tags). |
| `data/buyers_guide.txt` | Domain Knowledge | Unstructured legal/procedural guidance (HOA rules, Home loans, RERA, Stamp duty). |
