import os
import json
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
import chromadb
from dotenv import load_dotenv

# Robust dotenv loading - looks in backend/ or root folder
env_path = Path(__file__).resolve().parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(dotenv_path=env_path)

# 1. Initialize FastAPI app
app = FastAPI(
    title="Real Estate AI RAG Chatbot API",
    description="Beginner-friendly FastAPI backend serving a real estate RAG assistant using ChromaDB and Google Gemini.",
    version="1.0.0"
)

# Enable CORS so our frontend index.html can call the API locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Check and configure Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
is_api_key_configured = bool(GEMINI_API_KEY and "your_gemini_api_key" not in GEMINI_API_KEY)

if is_api_key_configured:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("[WARNING] GEMINI_API_KEY is not configured. Running in mock/warning mode.")

# 3. Connect to local persistent ChromaDB
DB_DIR = Path(__file__).resolve().parent / "database"
chroma_client = chromadb.PersistentClient(path=str(DB_DIR))

def format_inr(number: int) -> str:
    """Formats a number into Indian Lakhs/Crores style, e.g. 4644000 -> ₹46.44 Lakhs, 150000000 -> ₹15 Crores"""
    if number >= 10000000:
        val = number / 10000000
        formatted = f"{val:.2f} Crores".replace(".00", "")
        if formatted.endswith(".10 Crores") or formatted.endswith(".20 Crores") or formatted.endswith(".30 Crores") or formatted.endswith(".40 Crores") or formatted.endswith(".50 Crores") or formatted.endswith(".60 Crores") or formatted.endswith(".70 Crores") or formatted.endswith(".80 Crores") or formatted.endswith(".90 Crores"):
            formatted = formatted[:-1] + " Crores"
        elif formatted.endswith(".0 Crores"):
            formatted = formatted.replace(".0", "")
        return f"₹{formatted}"
    elif number >= 100000:
        val = number / 100000
        formatted = f"{val:.2f} Lakhs".replace(".00", "")
        if formatted.endswith(".10 Lakhs") or formatted.endswith(".20 Lakhs") or formatted.endswith(".30 Lakhs") or formatted.endswith(".40 Lakhs") or formatted.endswith(".50 Lakhs") or formatted.endswith(".60 Lakhs") or formatted.endswith(".70 Lakhs") or formatted.endswith(".80 Lakhs") or formatted.endswith(".90 Lakhs"):
            formatted = formatted[:-1] + " Lakhs"
        elif formatted.endswith(".0 Lakhs"):
            formatted = formatted.replace(".0", "")
        return f"₹{formatted}"
    else:
        return f"₹{number:,}"

# Pydantic Schemas for incoming request data validation
class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Real Estate Chatbot API is running.",
        "api_key_configured": is_api_key_configured
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    RAG Chat endpoint that retrieves matching property listings from ChromaDB
    and streams a response from Google Gemini via Server-Sent Events (SSE).
    """
    # Fallback/Safety Check: If API key is not configured, send a helpful message
    if not is_api_key_configured:
        def warning_generator():
            msg = "⚠️ **API Key Missing**: Please set your `GEMINI_API_KEY` in the `backend/.env` file to enable the AI Chatbot responses."
            yield f"data: {json.dumps({'type': 'text', 'text': msg})}\n\n"
        return StreamingResponse(warning_generator(), media_type="text/event-stream")

    query = request.query
    history = request.history

    # A. Embed the user's query ONCE — reused across both retrievals
    try:
        embed_response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = embed_response["embedding"]
    except Exception as e:
        print(f"[ERROR] Failed to embed query: {str(e)}")
        def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': f'Embedding error: {str(e)}'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    # B. RETRIEVAL SOURCE 1: Property Listings (whole-document matches)
    matching_properties = []
    properties_context = "No property listings matched in the vector database."
    
    try:
        prop_collection = chroma_client.get_collection(name="properties_collection")
        
        results = prop_collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        if results and results["metadatas"] and len(results["metadatas"][0]) > 0:
            properties_context = ""
            for i in range(len(results["metadatas"][0])):
                meta = results["metadatas"][0][i]
                doc_text = results["documents"][0][i] if results["documents"] else ""
                
                tags_list = meta.get("tags", "").split(",") if meta.get("tags") else []
                
                prop_data = {
                    "id": meta.get("id"),
                    "title": meta.get("title"),
                    "price": int(meta.get("price", 0)),
                    "location": meta.get("location"),
                    "bedrooms": int(meta.get("bedrooms", 0)),
                    "bathrooms": float(meta.get("bathrooms", 0)),
                    "tags": tags_list
                }
                matching_properties.append(prop_data)
                
                properties_context += (
                    f"[{i+1}] {prop_data['title']} (ID: {prop_data['id']})\n"
                    f"    Price: {format_inr(prop_data['price'])}\n"
                    f"    Location: {prop_data['location']}\n"
                    f"    Beds: {prop_data['bedrooms']}, Baths: {prop_data['bathrooms']}\n"
                    f"    Tags: {', '.join(prop_data['tags'])}\n"
                    f"    Details: {doc_text}\n\n"
                )
    except Exception as e:
        print(f"[WARNING] Property retrieval error: {str(e)}")
        properties_context = "Property database is uninitialized. Run python backend/ingest.py first."

    # C. RETRIEVAL SOURCE 2: Knowledge Base (chunked document matches)
    knowledge_context = ""
    
    try:
        knowledge_collection = chroma_client.get_collection(name="knowledge_chunks")
        
        kb_results = knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        if kb_results and kb_results["documents"] and len(kb_results["documents"][0]) > 0:
            for i, doc in enumerate(kb_results["documents"][0]):
                knowledge_context += f"[Knowledge Chunk {i+1}]: {doc}\n\n"
    except Exception as e:
        print(f"[INFO] Knowledge base not available: {str(e)}")

    # D. Construct conversational prompt with MULTI-SOURCE RAG Context
    history_str = ""
    for msg in history:
        speaker = "User" if msg.role == "user" else "Assistant"
        history_str += f"{speaker}: {msg.content}\n"

    system_prompt = (
        "You are 'Apex Horizon Assistant', a friendly, polite, and professional AI real estate chatbot representing Apex Horizon Realty.\n"
        "Your task is to help visitors find property listings and answer general real estate questions.\n\n"
        "=== RETRIEVED PROPERTY LISTINGS ===\n"
        f"\"\"\"\n{properties_context}\"\"\"\n\n"
        "=== RETRIEVED KNOWLEDGE BASE ===\n"
        f"\"\"\"\n{knowledge_context if knowledge_context else 'No relevant knowledge articles found.'}\"\"\"\n\n"
        "Strict rules for your response:\n"
        "1. Recommend ONLY properties listed in the property listings section above. Do not make up properties.\n"
        "2. To reference a property, you MUST write its exact ID format like [ID: prop_xxx] (e.g. [ID: prop_001]) inside your text. This allows our website to render it as a visual property card. Do not use markdown links for property IDs.\n"
        "3. If no properties match the search criteria, politely suggest the closest alternative or invite them to adjust their filters.\n"
        "4. For general real estate questions (e.g., 'what is an HOA?', 'how do home loans work?'), answer using the Knowledge Base content retrieved above. If no knowledge content is relevant, use your general knowledge.\n"
        "5. Speak natively about prices in Indian Rupees using Lakhs and Crores (e.g., ₹46.44 Lakhs, ₹3.75 Crores) as formatted in the database.\n"
        "6. Keep responses concise, helpful, and natural.\n\n"
        "Chat history:\n"
        f"{history_str}"
        f"User: {query}\n"
        "Assistant:"
    )

    # C. SSE generator to stream responses to the frontend
    def sse_event_stream():
        # Step 1: Stream the retrieved properties as metadata JSON first
        yield f"data: {json.dumps({'type': 'context', 'properties': matching_properties})}\n\n"
        
        # Step 2: Stream Gemini's text response chunk-by-chunk
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            # Call Gemini model
            response = model.generate_content(system_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'type': 'text', 'text': chunk.text})}\n\n"
        except Exception as err:
            # Handle model errors (like invalid API keys or rate limits)
            yield f"data: {json.dumps({'type': 'error', 'message': f'Gemini Error: {str(err)}'})}\n\n"

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
