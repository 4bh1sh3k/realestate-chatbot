# Rollback & Recovery Procedures

Step-by-step procedures to revert code or frontend styles if an update breaks system integrity or client appearance.

---

## 1. Frontend Style Rollbacks

The project maintains pre-built, verified UI alternates in `frontend/`. To switch to any design state, execute the corresponding PowerShell command and refresh `http://localhost:3000`:

| Desired State | Revert Command |
|---|---|
| **Minimal 2-Card Testbed** | `Copy-Item frontend/index_minimal.html frontend/index.html` |
| **Q'Chat Dark UI** | `Copy-Item frontend/index_dribbble.html frontend/index.html` |
| **Framer Motion Bento UI** | `Copy-Item frontend/index_framer.html frontend/index.html` |
| **Original Real Estate Site** | `Copy-Item frontend/index_backup.html frontend/index.html` |

---

## 2. Backend Code Recovery

* A verified backup of the original backend is stored at: `backend/main_backup.py`.
* To revert backend logic to the original Server-Sent Events (SSE) streaming version:
  ```powershell
  Copy-Item backend/main_backup.py backend/main.py
  ```

---

## 3. Database Reset & Re-Indexing

If the ChromaDB vector database becomes corrupted or out of sync:
```powershell
# 1. Stop uvicorn server
# 2. Re-run ingestion to wipe and recreate collections
python backend/ingest.py
```
Expected output verification:
- `properties_collection`: 8 documents
- `knowledge_chunks`: 20 chunks
