import os
import json
from dotenv import load_dotenv

# Build paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 3)) 
DISTANCE_THRESHOLD = 1.0 # Higher is more inclusive. 

def format_list_string(s):
    """Helper to parse a string that looks like a JSON list and format it."""
    if not s or not isinstance(s, str):
        return s
        
    data = None
    # 1. Try JSON parsing
    try:
        data = json.loads(s)
    except:
        pass
    
    # If it's a list with multiple items, just join them
    if isinstance(data, list) and len(data) > 1:
        return "\n".join([f"- {item.strip()}" for item in data if item.strip()])
    
    # If it's a list with ONE long item, treat that item as the string to split
    if isinstance(data, list) and len(data) == 1:
        cleaned_s = data[0]
    else:
        # 2. Fallback: Clean up malformed JSON-like artifacts
        cleaned_s = s.strip()
        if cleaned_s.startswith('["'): cleaned_s = cleaned_s[2:]
        if cleaned_s.endswith('"]'): cleaned_s = cleaned_s[:-2]
        if cleaned_s.startswith('"'): cleaned_s = cleaned_s[1:]
        if cleaned_s.endswith('"'): cleaned_s = cleaned_s[:-1]
    
    # 3. Try to split by sentences
    if len(cleaned_s) > 20:
        import re
        # Split by period followed by space or newline
        sentences = re.split(r'\.[\s\n]+', cleaned_s)
        if len(sentences) > 1:
            # Re-add periods and format as bullets
            formatted = []
            for sent in sentences:
                sent = sent.strip()
                if not sent: continue
                if not sent.endswith('.'): sent += '.'
                formatted.append(f"- {sent.capitalize()}")
            return "\n".join(formatted)
    
    return cleaned_s

def has_keyword_overlap(query: str, title: str, ingredients: str) -> bool:
    """Check if query keywords appear in recipe title or ingredients."""
    # Common stop words that don't matter for relevance
    stop_words = {'a', 'an', 'the', 'and', 'or', 'is', 'are', 'to', 'of', 'in', 'with', 'for', 'from', 'by'}
    
    # Extract words from query
    query_words = set(w.lower().strip(',.!?') for w in query.split() if w.lower() not in stop_words and len(w) > 2)
    
    # Combined text from recipe
    combined = (str(title) + " " + str(ingredients)).lower()
    
    # Check for keyword overlap
    for word in query_words:
        if word in combined:
            return True
    
    return False

def search_recipes(collection, query: str, n_results: int = TOP_K_RESULTS):
    if not query.strip():
        return None, 2.0, []

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    if not results or not results["metadatas"] or not results["metadatas"][0]:
        return None, 2.0, []

    context_parts = []
    matched_titles = []
    min_distance = 2.0
    
    for i, (metadata, distance) in enumerate(zip(results["metadatas"][0], results["distances"][0]), start=1):
        if distance < min_distance:
            min_distance = distance
            
        # Filter out results that are too distant (irrelevant)
        if distance > DISTANCE_THRESHOLD:
            continue

        title = metadata.get("title", "Unknown")
        ingredients = metadata.get("ingredients", "[]")
        instructions = metadata.get("instructions", "[]")
        
        # Only include if there's actual keyword relevance to the query
        if not has_keyword_overlap(query, title, ingredients):
            continue

        formatted_ingredients = format_list_string(ingredients)
        formatted_instructions = format_list_string(instructions)

        context_parts.append(
            f"### Recipe {i}: {title}\n\n"
            f"**Ingredients:**\n{formatted_ingredients}\n\n"
            f"**Instructions:**\n{formatted_instructions}\n"
        )
        matched_titles.append(title)

    if not context_parts:
        return None, min_distance, []

    return "\n---\n".join(context_parts), min_distance, matched_titles

