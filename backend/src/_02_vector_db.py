import pandas as pd
import chromadb
import os
import sys
from chromadb.utils import embedding_functions 
from ollama import Client as OllamaClient, ResponseError

# Build paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add backend dir to sys.path so we can import our modules
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
EMBEDDING_MODEL  = os.getenv('EMBEDDING_MODEL')


from utils.functions import get_ollama_embedding_function

def create_and_populate_db(df):
    print(f"Initializing local Chroma Vector DB with Ollama ({EMBEDDING_MODEL})...")
    db_path = os.path.join(os.path.dirname(BASE_DIR), 'chroma_db')
    db_client = chromadb.PersistentClient(path=db_path)
    
    ollama_ef = get_ollama_embedding_function()
    
    # 2. Delete any existing collection to avoid embedding function conflicts
    existing_collections = [c.name for c in db_client.list_collections()]
    if "recipes" in existing_collections:
        print("Wiping old collection for fresh run...")
        db_client.delete_collection(name="recipes")
    
    # 3. Create a fresh collection
    collection = db_client.create_collection(
        name="recipes",
        embedding_function=ollama_ef
    )

    print(f"Adding {len(df)} recipes to vector store...")
    
    ids = []
    documents = []
    metadatas = []

    for index, row in df.iterrows():
        ids.append(f"recipe_{index}")
        # Combining title and ingredients for document text
        documents.append(str(row['title']) + " " + str(row['ingredients']))  
        metadatas.append({                         
            "title": str(row['title']),
            "ingredients": str(row['ingredients']),
            "instructions": str(row['directions']) 
        })

    # Add in batches
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        print(f"Adding batch {i} to {i + batch_size}...")
        collection.add(
            ids=ids[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size]
        )
    
    print(f"Success! {collection.count()} recipes stored in Vector Database.")
    return collection

if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(BASE_DIR), 'dataset', '_02_cleaned', 'recipes_cleaned.csv')
    if os.path.exists(csv_path):
        recipe_df = pd.read_csv(csv_path)
        create_and_populate_db(recipe_df)
    else:
        print(f"Cleaned CSV not found at {csv_path}. Run _01_data_prep.py first.")
