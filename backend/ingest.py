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
DB_DIR = BASE_DIR / "backend" / "database"

def ingest_data():
    print("[START] Starting property data ingestion...")
    
    # 1. Load property data from data/properties.json
    if not DATA_FILE.exists():
        print(f"[ERROR] Properties file not found at {DATA_FILE}")
        return
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        properties = json.load(f)
        
    print(f"[INFO] Loaded {len(properties)} properties from JSON.")
    
    # 2. Initialize persistent local ChromaDB
    DB_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[DB] Connecting to local ChromaDB database at {DB_DIR}...")
    chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
    
    # Reset/Create collection for a fresh database load
    collection_name = "properties_collection"
    try:
        chroma_client.delete_collection(name=collection_name)
        print("[RESET] Reset existing collection for fresh ingestion.")
    except Exception:
        pass
        
    collection = chroma_client.create_collection(name=collection_name)
    
    # 3. Embed and store each property listing
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
            f"Price: ${price:,} (USD)\n"
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
            collection.add(
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

    print("\n[COMPLETE] Ingestion completed successfully!")
    print(f"Total documents loaded in vector database: {collection.count()}")

if __name__ == "__main__":
    ingest_data()
