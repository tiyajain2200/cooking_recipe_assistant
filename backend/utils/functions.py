import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from ollama import Client as OllamaClient, ResponseError
import os

# Build paths relative to this file's location so it works regardless of CWD
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env from the root directory
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
EMBEDDING_MODEL  = os.getenv('EMBEDDING_MODEL')


def get_ollama_embedding_function():
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
    import re

    stopwords = {
        "please", "can", "you", "suggest", "something",
        "give", "me", "i", "want", "to", "make",
        "recipe", "dish", "food", "bro", "hey",
        "with", "using", "how", "what", "should",
        "is", "the", "a", "it", "for", "of", "in",
        "some", "any", "tell", "show", "get"
    }

    query = query.lower()
    query = re.sub(r"[^\w\s]", "", query)

    words = [word for word in query.split() if word not in stopwords]

    return " ".join(words)
