import os
import re
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from ollama import Client as OllamaClient, ResponseError

# Build paths relative to this file's location so it works regardless of CWD
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env from the root directory
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

def get_ollama_embedding_function():
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
    EMBEDDING_MODEL  = os.getenv('EMBEDDING_MODEL')

    if not OLLAMA_BASE_URL:
        raise RuntimeError("OLLAMA_BASE_URL is not set. Please configure it in .env.")
    if not EMBEDDING_MODEL:
        raise RuntimeError("EMBEDDING_MODEL is not set. Please configure it in .env.")

    try:
        client = OllamaClient(host=OLLAMA_BASE_URL)
        client.show(model=EMBEDDING_MODEL)
    except ResponseError as e:
        if e.status_code == 404 or "not found" in str(e).lower():
            raise RuntimeError(
                f'Embedding model "{EMBEDDING_MODEL}" was not found on Ollama. '
                f'Run: ollama pull {EMBEDDING_MODEL} then restart the app.'
            ) from e
        raise
    except Exception as e:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_BASE_URL}. Ensure `ollama serve` is running."
        ) from e

    return embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_BASE_URL,
        model_name=EMBEDDING_MODEL,
    )

def get_recipe_collection():
    db_path = os.path.join(os.path.dirname(BASE_DIR), 'chroma_db')
    db_client = chromadb.PersistentClient(path=db_path)

    ollama_ef = get_ollama_embedding_function()

    collection = db_client.get_or_create_collection(
        name='recipes',
        embedding_function=ollama_ef
    )

    print(f"Connected to recipe database ({collection.count()} recipes loaded)")
    return collection

def clean_query(query: str) -> str:
    """
    Cleans the user query for better vector search.
    Keeps most words as modern embedding models (like nomic-embed-text) 
    benefit from natural language context.
    """
    if not query:
        return ""
        
    # Just basic cleaning: strip whitespace and remove some redundant punctuation
    query = query.strip()
    
    # We'll keep most words, but remove some very common conversational fluff 
    # that doesn't add any semantic value to a recipe search.
    fluff = {"please", "hey", "bro", "bot", "assistant"}
    
    words = query.split()
    cleaned_words = [w for w in words if w.lower().strip("?!.,") not in fluff]
    
    return " ".join(cleaned_words)
