# 🏠 Document RAG Chatbot (FastAPI + ChromaDB + Gemini)

This is a full-stack **Retrieval-Augmented Generation (RAG)** chatbot that I built as a personal learning project to understand semantic search, vector databases, and Large Language Model (LLM) integrations.

The project is designed to ingest local text documents (such as properties, company FAQs, or service brochures), convert them into vector embeddings, store them in a local vector database, and provide a chatbot interface that answers user questions based strictly on the ingested data.

---

## 🚀 How the RAG Pipeline Works

This project implements a standard RAG workflow:
1. **Document Chunking & Processing**: Documents are read, split into overlapping text chunks, and processed.
2. **Vector Embeddings**: Each text chunk is converted into a high-dimensional vector using Google's `gemini-embedding-001` model.
3. **Storage**: The vectors and text chunks are saved into a local **ChromaDB** instance.
4. **Semantic Retrieval**: When a user asks a question, the query is embedded and matched against ChromaDB using cosine similarity to find the most relevant chunks.
5. **Response Generation**: The retrieved text chunks are passed as context to `gemini-2.5-flash` alongside the user's prompt to generate a factual, hallucination-free answer.

---

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI (asynchronous REST API)
*   **Vector Database**: ChromaDB (configured as a local persistent storage client)
*   **AI Models**: Google Gemini API (`gemini-2.5-flash` for answering, `gemini-embedding-001` for vector transformations)
*   **Frontend Sandbox**: Vanilla JavaScript, HTML5, and CSS3 (custom glassmorphic theme and slide-out chat widget)

---

## 📁 Project Structure

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

## ⚙️ Installation & Setup

### 1. Prerequisites
Make sure you have Python 3.10+ installed.

### 2. Clone the Repository & Set Up Virtual Environment
Open your terminal (CMD or PowerShell) in the project directory:
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a file named `.env` inside the `backend/` folder and add your Gemini API Key:
```env
PORT=8000
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
*(Get your free API Key from [Google AI Studio](https://aistudio.google.com/))*

---

## 🏃 Running the Application

### Step 1: Run the Ingestion Pipeline
To populate the local vector database with your document listings, run:
```cmd
python backend/ingest.py
```
This will read your source data, generate embeddings, and save them in the `backend/database/` directory.

### Step 2: Start the FastAPI Server
Launch the backend server:
```cmd
python -m uvicorn backend.main:app --reload --port 8000
```
The server will start running locally at `http://127.0.0.1:8000`.

### Step 3: Run the Frontend Widget
In a separate terminal window, serve the static frontend folder:
```cmd
python -m http.server 3000 --directory frontend
```
Now, open your browser and navigate to **`http://localhost:3000`** to interact with the chatbot interface!
