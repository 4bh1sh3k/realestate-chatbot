import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import chromadb
from dotenv import load_dotenv

# 1. Environment & API Configuration
env_path = Path(__file__).resolve().parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or "your_gemini_api_key" in GEMINI_API_KEY:
    print("[WARNING] GEMINI_API_KEY is not configured properly.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# 2. Initialize ChromaDB Vector Database
DB_DIR = Path(__file__).resolve().parent / "database"
chroma_client = chromadb.PersistentClient(path=str(DB_DIR))

# 3. Initialize FastAPI
app = FastAPI(title="Real Estate RAG API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def health_check():
    return {"status": "online", "message": "RAG Backend is ready."}

@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Core RAG Pipeline:
    1. Embed query (asymmetric 'retrieval_query' embedding)
    2. Retrieve top-k relevant documents from ChromaDB
    3. Augment system prompt with retrieved context
    4. Generate grounded response using Gemini LLM
    """
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # STEP 1: Query Vectorization
    try:
        embed_resp = genai.embed_content(
            model="models/gemini-embedding-001",
            content=user_query,
            task_type="retrieval_query"
        )
        query_vector = embed_resp["embedding"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

    retrieved_properties = []
    retrieved_knowledge = []

    # STEP 2A: Retrieve Matching Properties (Whole Documents)
    try:
        prop_coll = chroma_client.get_collection("properties_collection")
        prop_results = prop_coll.query(query_embeddings=[query_vector], n_results=2)
        if prop_results and prop_results["documents"] and prop_results["documents"][0]:
            for doc in prop_results["documents"][0]:
                retrieved_properties.append(doc)
    except Exception as e:
        print(f"[WARN] Properties query: {e}")

    # STEP 2B: Retrieve Knowledge Chunks (Chunked Buyer's Guide)
    try:
        kb_coll = chroma_client.get_collection("knowledge_chunks")
        kb_results = kb_coll.query(query_embeddings=[query_vector], n_results=2)
        if kb_results and kb_results["documents"] and kb_results["documents"][0]:
            for doc in kb_results["documents"][0]:
                retrieved_knowledge.append(doc)
    except Exception as e:
        print(f"[WARN] Knowledge query: {e}")

    # Format context blocks
    prop_context = "\n---\n".join(retrieved_properties) if retrieved_properties else "No matching listings found."
    kb_context = "\n---\n".join(retrieved_knowledge) if retrieved_knowledge else "No matching guides found."

    # STEP 3: Prompt Augmentation with Grounding Rules
    prompt = f"""You are a professional AI real estate advisor for Apex Horizon Realty.
Answer the user's question accurately using ONLY the retrieved context below.

=== RETRIEVED PROPERTY LISTINGS ===
{prop_context}

=== RETRIEVED REAL ESTATE KNOWLEDGE ===
{kb_context}

RULES:
1. Base your answer strictly on the provided context above. Do not hallucinate or invent listings.
2. If asked about properties, cite the specific title and price from the listings.
3. If asked general real estate questions (like HOA, loans, inspections), use the knowledge section.
4. If neither section contains the answer, politely state that you do not have that information in your database.

User Question: {user_query}
Answer:"""

    # STEP 4: LLM Generation
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        llm_response = model.generate_content(prompt)
        answer_text = llm_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini generation error: {str(e)}")

    return {
        "query": user_query,
        "answer": answer_text,
        "retrieved_context": {
            "properties": retrieved_properties,
            "knowledge_chunks": retrieved_knowledge
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
