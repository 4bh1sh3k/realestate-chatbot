import os
import json
from pathlib import Path
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# Robust dotenv loading - looks in backend/ or root folder
env_path = Path(__file__).resolve().parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or "your_gemini_api_key" in GEMINI_API_KEY:
    print("[ERROR] GEMINI_API_KEY is not set or is still the default placeholder.")
    print("Please create a backend/.env file and set GEMINI_API_KEY to your valid Google AI Studio API key.")
    print("Example (.env):")
    print("GEMINI_API_KEY=AIzaSy...")
    exit(1)

# Configure the Google Gemini SDK
genai.configure(api_key=GEMINI_API_KEY)

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "properties.json"
KNOWLEDGE_FILE = BASE_DIR / "data" / "buyers_guide.txt"
DB_DIR = BASE_DIR / "backend" / "database"

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


def chunk_text(text, chunk_size=500, overlap=100):
    """
    Splits a long text document into overlapping chunks for embedding.
    
    Overlap ensures that context spanning chunk boundaries is not lost.
    For example, if a sentence about "stamp duty rates" starts at the end
    of one chunk, the overlap carries it into the next chunk as well.
    
    Args:
        text: The full document text to split.
        chunk_size: Maximum number of characters per chunk.
        overlap: Number of characters to repeat between consecutive chunks.
    
    Returns:
        A list of text chunk strings.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap  # Move forward by (chunk_size - overlap)
    return chunks


def ingest_data():
    print("[START] Starting data ingestion...\n")
    
    # Initialize persistent local ChromaDB
    DB_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[DB] Connecting to local ChromaDB database at {DB_DIR}...")
    chroma_client = chromadb.PersistentClient(path=str(DB_DIR))

    # =========================================================
    # PHASE 1: Ingest Property Listings (whole-document embeddings)
    # =========================================================
    # Properties are small (~150 tokens each), so we embed them
    # as whole documents — chunking would break their context.
    # =========================================================
    
    print("\n--- Phase 1: Property Listings ---")
    
    # 1. Load property data from data/properties.json
    if not DATA_FILE.exists():
        print(f"[ERROR] Properties file not found at {DATA_FILE}")
        return
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        properties = json.load(f)
        
    print(f"[INFO] Loaded {len(properties)} properties from JSON.")
    
    # Reset/Create collection for a fresh database load
    collection_name = "properties_collection"
    try:
        chroma_client.delete_collection(name=collection_name)
        print("[RESET] Reset existing properties collection for fresh ingestion.")
    except Exception:
        pass
        
    prop_collection = chroma_client.create_collection(name=collection_name)
    
    # Embed and store each property listing as a whole document
    for prop in properties:
        prop_id = prop["id"]
        title = prop["title"]
        price = prop["price"]
        location = prop["location"]
        bedrooms = prop["bedrooms"]
        bathrooms = prop["bathrooms"]
        description = prop["description"]
        tags = prop["tags"]
        
        # Formulate rich text representation for semantic embedding search
        doc_text = (
            f"Property Title: {title}\n"
            f"Price: {format_inr(price)}\n"
            f"Location: {location}\n"
            f"Bedrooms: {bedrooms}\n"
            f"Bathrooms: {bathrooms}\n"
            f"Description: {description}\n"
            f"Tags: {', '.join(tags)}"
        )
        
        print(f"[EMBED] Generating embedding for: {title} ({prop_id})...")
        
        try:
            # Generate dense embedding vector using Gemini text-embedding model
            embed_response = genai.embed_content(
                model="models/gemini-embedding-001",
                content=doc_text,
                task_type="retrieval_document",
                title=title
            )
            embedding = embed_response["embedding"]
            
            # Store in ChromaDB along with metadata for frontend rendering
            prop_collection.add(
                ids=[prop_id],
                embeddings=[embedding],
                metadatas=[{
                    "id": prop_id,
                    "title": title,
                    "price": price,
                    "location": location,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "tags": ",".join(tags)
                }],
                documents=[doc_text]
            )
            print(f"[SUCCESS] Stored {prop_id} successfully.")
            
        except Exception as e:
            print(f"[ERROR] Failed to embed property {prop_id}: {str(e)}")
            print("Please ensure your GEMINI_API_KEY is active and valid.")
            return

    print(f"\n[PHASE 1 COMPLETE] Properties loaded: {prop_collection.count()}")

    # =========================================================
    # PHASE 2: Ingest Knowledge Base with CHUNKING
    # =========================================================
    # The buyer's guide is a long-form document (~1500 words).
    # We split it into overlapping chunks of ~500 chars with
    # 100-char overlap so context at chunk boundaries is preserved.
    # =========================================================

    print("\n--- Phase 2: Knowledge Base (Chunked) ---")
    
    if not KNOWLEDGE_FILE.exists():
        print(f"[SKIP] Knowledge file not found at {KNOWLEDGE_FILE}. Skipping knowledge ingestion.")
    else:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            full_text = f.read()
        
        print(f"[INFO] Loaded knowledge document: {len(full_text)} characters.")
        
        # Split into overlapping chunks
        chunks = chunk_text(full_text, chunk_size=500, overlap=100)
        print(f"[CHUNK] Split into {len(chunks)} chunks (size=500, overlap=100).")
        
        # Reset/Create knowledge chunks collection
        knowledge_collection_name = "knowledge_chunks"
        try:
            chroma_client.delete_collection(name=knowledge_collection_name)
            print("[RESET] Reset existing knowledge collection for fresh ingestion.")
        except Exception:
            pass
        
        knowledge_collection = chroma_client.create_collection(name=knowledge_collection_name)
        
        # Embed and store each chunk
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{i:03d}"
            print(f"[EMBED] Generating embedding for chunk {chunk_id} ({len(chunk)} chars)...")
            
            try:
                embed_response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=chunk,
                    task_type="retrieval_document",
                    title=f"Buyer's Guide - Section {i+1}"
                )
                embedding = embed_response["embedding"]
                
                knowledge_collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    metadatas=[{
                        "source": "buyers_guide",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }],
                    documents=[chunk]
                )
                print(f"[SUCCESS] Stored {chunk_id}.")
                
            except Exception as e:
                print(f"[ERROR] Failed to embed {chunk_id}: {str(e)}")
                return
        
        print(f"\n[PHASE 2 COMPLETE] Knowledge chunks loaded: {knowledge_collection.count()}")

    print("\n[ALL DONE] Full ingestion pipeline completed successfully!")

if __name__ == "__main__":
    ingest_data()

