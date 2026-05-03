# 🍳 Cooking Recipe RAG - AI-Powered Kitchen Assistant

## Project Overview

**Cooking Recipe RAG** is a sophisticated, local-first web application that leverages **Retrieval-Augmented Generation (RAG)** to provide accurate, context-aware recipe suggestions. By combining a dedicated vector database of recipes with a local Large Language Model (LLM), it ensures that culinary advice is grounded in real data rather than AI imagination.

This project is designed to run entirely on your local machine, ensuring 100% privacy and offline capability once models are downloaded.

---

## 🛠️ Tools and Technologies

| Component | Tool | Purpose |
|-----------|------|---------|
| **Backend** | Flask | Serves the API and frontend files; manages SSE streaming. |
| **LLM** | Ollama (`qwen2.5`) | Local model used for high-quality text generation. |
| **Embeddings** | Ollama (`nomic-embed-text`) | Converts text into high-dimensional vectors for search. |
| **Vector DB** | ChromaDB | Stores and retrieves recipe vectors using semantic search. |
| **Data Logic** | Pandas | Handles CSV processing and data cleaning. |
| **Frontend** | Vanilla JS / CSS | Provides a responsive, real-time chat interface. |
| **Markdown** | Marked.js | Renders AI responses into formatted HTML. |

---

## 🏗️ How the RAG Logic Works

1.  **Ingestion**: Recipes are processed and converted into numerical vectors (embeddings) that represent their semantic meaning.
2.  **Retrieval**: When a user enters a query (e.g., "I have chicken and yogurt"), the system searches ChromaDB for recipes with the most similar vectors.
3.  **Augmentation**: The top matching recipes are retrieved and injected into a structured prompt as "Context."
4.  **Generation**: The local LLM reads the context and the user query to generate a formatted response, ensuring it doesn't "hallucinate" ingredients not found in the database.

---

## 📂 Project Structure

```text
ai_project/
├── backend/
│   ├── app.py                  # Main Flask entry point
│   ├── src/
│   │   ├── _01_data_prep.py    # Dataset cleaning script
│   │   ├── _02_vector_db.py    # Embedding & Database creation
│   │   └── _03_rag.py          # Search & Retrieval logic
│   ├── utils/
│   │   ├── functions.py        # Shared helpers (Cleaning, DB Connect)
│   │   └── prompts.py          # LLM instructions & Templates
│   └── dataset/
│       ├── _01_raw/            # Original CSV files
│       └── _02_cleaned/        # Processed CSV files
├── frontend/
│   ├── index.html              # Chat UI layout
│   ├── script.js               # Streaming & UI logic
│   └── style.css               # Modern dark-theme styling
└── DOCUMENTATION_DETAILED.md   # Deep-dive technical guide
```

---

## 🚀 Setup and Installation

### 1. Prerequisites
- Python 3.12+
- [Ollama](https://ollama.com/) installed and running.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download Local Models
Open your terminal and run:
```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### 4. Prepare the Database (One-time)
1.  Clean the raw data:
    ```bash
    python backend/src/_01_data_prep.py
    ```
2.  Build the vector store:
    ```bash
    python backend/src/_02_vector_db.py
    ```

### 5. Run the Application
```bash
python backend/app.py
```
Open your browser and navigate to `http://localhost:5000`.

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Ollama Error** | Ensure `ollama serve` is running in the background. |
| **No Results Found** | Try simpler ingredients. The system filters out conversational filler. |
| **Port 5000 Busy** | Kill any existing process on port 5000 or change the port in `app.py`. |
| **Model Not Found** | Run `ollama pull` for both the LLM and Embedding models. |

---

*Everything in this project runs locally. No data is sent to external servers.*
