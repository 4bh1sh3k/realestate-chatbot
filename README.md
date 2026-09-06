<<<<<<< HEAD
#  Document RAG Chatbot (FastAPI + ChromaDB + Gemini)

This is a **Retrieval-Augmented Generation (RAG)** chatbot involving semantic search, vector databases, and Large Language Model (LLM) integrations.
=======
# Estatic — Real Estate RAG Chatbot

An engineering-focused **Retrieval-Augmented Generation (RAG)** service built with **FastAPI**, **ChromaDB**, and **Google Gemini**. 
>>>>>>> 770f3a0 (docs)

This project explores production RAG architecture: **asymmetric vector embeddings**, **sliding-window text chunking**, **deterministic context grounding**, and **decoupled read/write pipelines** to eliminate hallucinations in domain-specific queries.

---

<<<<<<< HEAD
##  How the RAG Pipeline Works
=======
## 🏛️ System Architecture
>>>>>>> 770f3a0 (docs)

The service decouples compute-heavy offline indexing from low-latency online inference:

```
                      [Offline Indexing: ingest.py]
  Structured Data               Unstructured Domain Text
 (properties.json)                 (buyers_guide.txt)
        │                                  │
        │ Whole-Doc Text                   ▼ Sliding-Window Chunker
        │ Formulation                 (500 chars / 20% stride)
        ▼                                  ▼
 8 Property Docs                   20 Knowledge Chunks
        │                                  │
        └──────────────────┬───────────────┘
                           ▼
          Google Gemini Embedding-001 (task_type="retrieval_document")
                           │
                           ▼
             Local Persistent ChromaDB Store
             ├── properties_collection (8 docs)
             └── knowledge_chunks     (20 chunks)

──────────────────────────────────────────────────────────────────

                      [Online Inference: main.py]
                 User Query via REST /api/chat
                           │
                           ▼
          Vectorize Query (task_type="retrieval_query")
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  ChromaDB: properties (Top-2)    ChromaDB: knowledge (Top-2)
             └─────────────┬─────────────┘
                           ▼
         Strict Grounding System Prompt Augmentation
                           │
                           ▼
             Gemini-2.5-Flash Generation
                           │
                           ▼
             JSON Response + Telemetry Proof
        { "answer": "...", "retrieved_context": {...} }
```

---

## 🚀 Key Engineering & RAG Decisions

### 1. Two-Tier Chunking Strategy
* **Structured Entities (`properties.json`)**: Embedded as complete, individual documents (~150 tokens each). Chunking structured listings would split relational context (e.g., separating price from bedrooms).
* **Unstructured Domain Text (`buyers_guide.txt`)**: Processed using a custom **sliding-window chunker** with `chunk_size = 500` characters and `overlap = 100` characters (20% stride). This prevents semantic boundary loss when explanations of loans, HOA rules, or stamp duty span split points.

### 2. Asymmetric Embeddings
Uses Google’s `gemini-embedding-001` with explicit task profiling:
* `task_type="retrieval_document"` during offline batch ingestion.
* `task_type="retrieval_query"` during runtime search.  
This optimizes cosine similarity between asymmetric lengths and syntactic patterns of user queries versus source documents.

### 3. Anti-Hallucination Guardrails
The system prompt enforces strict deterministic boundaries:
* The LLM is instructed to answer **exclusively** from the retrieved context blocks.
* If a listing or legal rule is absent, the model is instructed to gracefully decline rather than extrapolate or fabricate data.

### 4. Decoupled Read/Write Architecture
* **Write Path (`ingest.py`)**: Heavy I/O and batch vector generation runs offline, preventing runtime ingestion bottlenecks.
* **Read Path (`main.py`)**: Lightweight, stateless FastAPI REST service designed for low-latency retrieval and horizontal scaling behind an ingress controller.

### 5. Observability & Telemetry
The `/api/chat` endpoint returns both the synthesized answer **and** the raw vector chunks retrieved from ChromaDB. This enables observability pipelines (e.g., RAGAS metrics: Context Recall, Precision, and Faithfulness) to separate retrieval errors from generation errors.

---

##  Tech Stack

* **Backend Framework**: Python 3.13, FastAPI, Pydantic v2, Uvicorn
* **Vector Database**: ChromaDB (persistent local SQLite vector store)
* **Embedding Model**: Google `gemini-embedding-001` (768-dim dense vectors)
* **Foundation LLM**: Google `gemini-2.5-flash`
* **Frontend Testbed**: HTML5, Vanilla CSS, Fetch API *(AI-assisted prototyping)*

---

<<<<<<< HEAD
##  Project Structure

```text
ai-chatbot-py/
│
├── backend/                  # Python backend code
│   ├── database/             # Local database storage (gitignored)
│   ├── main.py               # FastAPI server and chat routes
│   └── ingest.py             # Data ingestion and vectorization script
│
├── frontend/                 # Chatbot frontend sandbox
│   ├── index.html            # Test landing page
│   ├── widget.js             # Chat widget controller
│   └── widget.css            # Stylesheet
│
├── data/                     # Source documents directory
│   └── properties.json       # Sample listings data
│
├── .gitignore                # Git ignore file (excludes secrets & database binaries)
└── requirements.txt          # Python dependencies
```

---

##  Installation & Setup

### 1. Prerequisites
Make sure you have Python 3.10+ installed.

### 2. Clone the Repository & Set Up Virtual Environment
Open your terminal (CMD or PowerShell) in the project directory:
```cmd
=======
## ⚙️ Setup & Running

### 1. Virtual Environment & Dependencies
```powershell
>>>>>>> 770f3a0 (docs)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment
Create `backend/.env`:
```env
PORT=8000
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

<<<<<<< HEAD
---

##  Running the Application

### Step 1: Run the Ingestion Pipeline
To populate the local vector database with your document listings, run:
```cmd
=======
### 3. Run Ingestion Pipeline (Run Once)
```powershell
>>>>>>> 770f3a0 (docs)
python backend/ingest.py
```

### 4. Start the Application
* **Terminal 1 (Backend REST API)**:
  ```powershell
  python -m uvicorn backend.main:app --reload --port 8000
  ```
* **Terminal 2 (Frontend Interface)**:
  ```powershell
  python -m http.server 3000 --directory frontend
  ```
Open **`http://localhost:3000`** in your browser.
