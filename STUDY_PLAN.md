# Cisco Interview Study Plan: RAG & Backend Mastery
> **Goal:** Master the conceptual mental model behind your RAG pipeline so you can comfortably explain, defend, and reason through every architectural decision in the interview without needing deep Python expertise.

---

## 🎯 How to Frame Your Project to the Cisco Interviewer
Whenever they ask about the stack or code origin, use this honest, high-leverage opening:
> *"I used AI-assisted tooling to scaffold the frontend interface and boilerplate REST routes, which let me focus on the engineering decisions that matter: the RAG data flow, asymmetric embedding types, sliding-window chunking trade-offs, and deterministic prompt guardrails to eliminate hallucination."*

---

## 📚 The 5 Core Topics to Study

### Topic 1: The RAG Lifecycle & Data Flow
**Core Question:** *"What happens between a user hitting 'Search' and getting an answer?"*

1. **Query Vectorization (The 'R' part 1):**
   * The text question is sent to `gemini-embedding-001` with `task_type="retrieval_query"`.
   * It is mapped to a high-dimensional dense vector (768 numbers).
2. **Nearest Neighbor Search (The 'R' part 2):**
   * ChromaDB calculates **Cosine Similarity** between the query vector and stored document vectors.
   * Cosine distance formula: $\cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|}$ (measures directional angle, independent of text length).
   * It fetches the **Top-2** highest-scoring chunks from each collection.
3. **Prompt Augmentation (The 'A'):**
   * The retrieved text chunks are dynamically concatenated into the system prompt alongside the user's question.
4. **Grounded Generation (The 'G'):**
   * `gemini-2.5-flash` generates an answer strictly constrained by the injected context blocks.

---

### Topic 2: Chunking Strategy & Trade-offs
**Core Question:** *"How did you chunk your data, and why not use fixed 1000-token chunks everywhere?"*

* **The Problem with Naive Chunking:**
  * If chunks are too large (e.g. 2000 tokens): Semantic vectors become "diluted" with multiple topics, reducing retrieval precision.
  * If chunks are too small (e.g. 50 tokens): Context gets fragmented, and the LLM lacks sufficient information to answer.
* **Your Solution (Two-Tier Design):**
  1. **Structured Data (`properties.json`):** Whole-document embedding (~150 tokens each). Chunking would sever relationships (e.g., splitting property title from its price).
  2. **Unstructured Data (`buyers_guide.txt`):** Custom sliding-window chunking:
     * `chunk_size = 500 characters`
     * `overlap = 100 characters` (20% stride)
* **Why the 20% overlap matters:**
  If an important clause (e.g. *"Stamp duty in West Bengal is 6% for urban areas"*) starts at character 480 and ends at character 540, a hard cut splits the sentence and destroys retrieval accuracy. The overlap guarantees the complete thought is preserved in at least one chunk.

---

### Topic 3: Asymmetric Embeddings
**Core Question:** *"Why did you use different task types for queries and documents?"*

* Queries (questions) and documents (answers/facts) have very different structures:
  * A query is short, interrogative, and sparse (*"what are HOA fees?"*).
  * A document chunk is descriptive and factual (*"The HOA collects monthly fees ranging from Rs 2,000 to 15,000..."*).
* Symmetric models embed both identically, which often results in suboptimal vector similarity.
* Gemini's **Asymmetric Embedding** optimizes the vector projection:
  * `task_type="retrieval_document"` encodes comprehensive informational content.
  * `task_type="retrieval_query"` encodes search intent to find matching document vectors in cosine space.

---

### Topic 4: Hallucination Prevention & Guardrails
**Core Question:** *"How do you know your chatbot won't invent a fake house or legal rule?"*

* **Fail-Closed System Prompt:**
  In `main.py`, the prompt explicitly specifies:
  1. *Rule 1:* Base answers **strictly** on the retrieved listings and knowledge base.
  2. *Rule 2:* Do not invent or extrapolate listings.
  3. *Rule 3:* If the answer is not in the context, explicitly state: *"I do not have that information in our database."*
* **Observability Verification:**
  Because the API returns `{ "answer": "...", "retrieved_context": {...} }`, engineers can inspect whether an issue was:
  * A **Retrieval Failure** (ChromaDB didn't return relevant chunks).
  * A **Generation Failure** (chunks were relevant, but LLM misread or ignored them).

---

### Topic 5: Production Scalability & Networking (Cisco Focused)
**Core Question:** *"How would you scale this to 100,000 users and 10 million documents at Cisco?"*

* **Decoupled Architecture:**
  * Ingestion is an offline batch ETL job (`ingest.py`).
  * The query path (`main.py`) is stateless and read-only, allowing horizontal scaling behind an NGINX or Kubernetes Ingress load balancer.
* **Vector DB Evolution:**
  * SQLite-based ChromaDB is ideal for localized prototyping and low overhead.
  * At scale, replace in-process SQLite with a distributed vector index like **Pinecone**, **Milvus**, or **Qdrant** utilizing **HNSW (Hierarchical Navigable Small World)** graphs for sub-10ms Approximate Nearest Neighbor (ANN) searches over millions of vectors.
* **Hybrid Search (Sparse + Dense):**
  * Vector search struggles with exact scalar filters (e.g. *price < 50 Lakhs*).
  * In production, combine BM25/metadata filtering (lexical) with vector similarity (semantic), followed by a cross-encoder re-ranker (like Cohere Rerank) before prompt injection.

---

## 🗓️ 3-Day Study Checklist

- [ ] **Day 1: Internalize the Code Flow**
  - Read lines 50–120 of [`backend/main.py`](file:///c:/Users/bente/OneDrive/Documents/ai%20chatbot%20py/backend/main.py) until you can trace: Request → Embed → Query Chroma → Format Prompt → Call Gemini → Return JSON.
  - Read lines 50–115 of [`backend/ingest.py`](file:///c:/Users/bente/OneDrive/Documents/ai%20chatbot%20py/backend/ingest.py) to review how `chunk_text()` iterates with `start += chunk_size - overlap`.
- [ ] **Day 2: Practice the Core Talking Points Out Loud**
  - Practice explaining *Asymmetric Embeddings* in 30 seconds.
  - Practice explaining *why 20% overlap was chosen* in 30 seconds.
  - Practice explaining *how you guard against hallucinations*.
- [ ] **Day 3: Cisco Systems / Scaling Scenarios**
  - Review the difference between vector similarity and scalar metadata filtering.
  - Practice your answer to *"What if our document collection grows from 28 to 2 million chunks?"* (Decoupled ETL + HNSW distributed vector DB).
