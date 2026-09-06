# Execution Flow & Traceability

This document traces how data and control travel between files, functions, and modules across the service lifecycle.

---

## 1. Offline Ingestion Trace (`backend/ingest.py`)

```
[Start Execution: python backend/ingest.py]
  │
  ├─► 1. Load Environment & Validate Keys
  │      Path: backend/.env
  │      Calls: genai.configure(api_key=GEMINI_API_KEY)
  │
  ├─► 2. Initialize ChromaDB Persistent Client
  │      Target Directory: backend/database/
  │
  ├─► 3. Phase 1: Property Catalog Ingestion
  │      Source: data/properties.json
  │      Action: Reset collection "properties_collection"
  │      Loop over properties:
  │         - Formulate natural text string (Title, Price, Location, Beds, Baths, Tags)
  │         - Call: genai.embed_content(model="gemini-embedding-001", task_type="retrieval_document")
  │         - Store: prop_collection.add(ids=[prop_id], embeddings=[embedding], metadatas=[...], documents=[doc_text])
  │      Output: 8 records indexed
  │
  └─► 4. Phase 2: Knowledge Base Ingestion with Chunking
         Source: data/buyers_guide.txt
         Action: Reset collection "knowledge_chunks"
         Call: chunk_text(full_text, chunk_size=500, overlap=100)
         Loop over 20 chunks:
            - Call: genai.embed_content(model="gemini-embedding-001", task_type="retrieval_document")
            - Store: knowledge_collection.add(ids=[chunk_id], embeddings=[embedding], metadatas=[...], documents=[chunk])
         Output: 20 chunks indexed
```

---

## 2. Online Request/Response Trace (`backend/main.py`)

```
[User initiates query from frontend/index.html]
  │
  ▼ HTTP POST http://127.0.0.1:8000/api/chat Payload: {"query": user_query}
[FastAPI Route: chat(request: ChatRequest)]
  │
  ├─► 1. Input Validation: Check non-empty query
  │
  ├─► 2. Query Embedding
  │      Call: genai.embed_content(
  │          model="models/gemini-embedding-001",
  │          content=user_query,
  │          task_type="retrieval_query"
  │      )
  │      Output: query_vector (768-dim float array)
  │
  ├─► 3. Parallel Dense Retrieval
  │      - ChromaDB: properties_collection.query(query_embeddings=[query_vector], n_results=2)
  │      - ChromaDB: knowledge_chunks.query(query_embeddings=[query_vector], n_results=2)
  │
  ├─► 4. Grounding Prompt Construction
  │      - Format: Injects retrieved_properties & retrieved_knowledge into markdown context blocks
  │      - Enforces strict negative constraints: "Do not invent listings. State if data is absent."
  │
  ├─► 5. LLM Synthesis
  │      Call: genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
  │      Output: answer_text
  │
  └─► 6. Return Structured JSON Payload
         Status: 200 OK
         Body: {
           "query": user_query,
           "answer": answer_text,
           "retrieved_context": {
             "properties": [...],
             "knowledge_chunks": [...]
           }
         }
```
