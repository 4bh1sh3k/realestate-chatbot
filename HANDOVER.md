# Handover & Session Status

A living record of where the project stands: what is complete, what is running, and instructions for next sessions.

---

## 📌 Current State

* **Service Status**: Production-ready prototype. Fully decoupled RAG service with ChromaDB vector store and FastAPI REST interface.
* **Vector Store Metrics**:
  * `properties_collection`: 8 documents (whole-document property records)
  * `knowledge_chunks`: 20 chunks (500-char window, 20% stride from `buyers_guide.txt`)
* **Active Endpoints**:
  * `GET  /` -> Health check
  * `POST /api/chat` -> RAG retrieval + synthesis
* **Frontend UI**:
  * Minimalist, dark-mode perspective-grid landing page with real-time RAG query console, responsive latency tracking, and ChromaDB vector chunk inspection.

---

## 🚀 How to Run the Project Right Now

```powershell
# 1. Start Backend Server (Terminal 1)
.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --port 8000

# 2. Start Frontend Server (Terminal 2)
python -m http.server 3000 --directory frontend
```
Visit: **`http://localhost:3000`**

---

## 🔮 Future Enhancements (Interview Talking Points)
1. **Hybrid Retrieval**: Add BM25 lexical keyword search alongside dense vectors for exact numeric price filtering (`price < 50 Lakhs`).
2. **Re-Ranking Layer**: Add a cross-encoder model (e.g., Cohere Rerank) to score top-K candidate chunks before prompt augmentation.
3. **Conversational Memory**: Add query reformulation (condense question using chat history) before embedding generation.
