import os
import json
import csv
from dotenv import load_dotenv

# Build paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 10)) 
DISTANCE_THRESHOLD = 1.0 # Higher is more inclusive. 
_RECIPE_INDEX = None

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

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    for ch in '.,!?()[]"\'':
        text = text.replace(ch, ' ')
    stop_words = {'a', 'an', 'the', 'and', 'or', 'is', 'are', 'to', 'of', 'in', 'with', 'for', 'from', 'by', 'recipe', 'dish', 'make', 'make', 'cook', 'cooking'}
    words = [w for w in text.split() if w and w not in stop_words]
    return ' '.join(words)


def has_keyword_overlap(query: str, title: str, ingredients: str) -> bool:
    """Check if query keywords appear in recipe title or ingredients."""
    query_words = set(w.lower().strip(',.!?') for w in query.split() if len(w) > 2 and w.lower() not in {'a', 'an', 'the', 'and', 'or', 'is', 'are', 'to', 'of', 'in', 'with', 'for', 'from', 'by', 'recipe', 'dish'})
    combined = (str(title) + " " + str(ingredients)).lower()

    for word in query_words:
        if word in combined:
            return True
    return False


def title_matches_query(query: str, title: str) -> bool:
    normalized_query = normalize_text(query)
    normalized_title = normalize_text(title)
    if not normalized_title:
        return False

    if normalized_title in normalized_query or normalized_query in normalized_title:
        return True

    query_words = set(normalized_query.split())
    title_words = set(normalized_title.split())
    return title_words and title_words.issubset(query_words)


def load_recipe_index():
    global _RECIPE_INDEX
    if _RECIPE_INDEX is not None:
        return _RECIPE_INDEX

    csv_path = os.path.join(os.path.dirname(BASE_DIR), 'dataset', '_02_cleaned', 'recipes_cleaned.csv')
    _RECIPE_INDEX = []

    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            _RECIPE_INDEX = [row for row in reader]
    except FileNotFoundError:
        _RECIPE_INDEX = []

    return _RECIPE_INDEX


def find_exact_title_matches(query: str):
    matches = []
    for row in load_recipe_index():
        title = str(row.get('title', ''))
        if title_matches_query(query, title):
            matches.append(row)
    return matches


def build_context_from_rows(rows):
    context_parts = []
    for i, row in enumerate(rows, start=1):
        title = str(row.get('title', 'Unknown'))
        ingredients = str(row.get('ingredients', '[]'))
        instructions = str(row.get('directions', '[]'))
        formatted_ingredients = format_list_string(ingredients)
        formatted_instructions = format_list_string(instructions)
        context_parts.append(
            f"### Recipe {i}: {title}\n\n"
            f"**Ingredients:**\n{formatted_ingredients}\n\n"
            f"**Instructions:**\n{formatted_instructions}\n"
        )
    return "\n---\n".join(context_parts)


def search_recipes(collection, query: str, n_results: int = TOP_K_RESULTS):
    if not query.strip():
        return None, 2.0, [], 'none'

    exact_rows = find_exact_title_matches(query)
    if exact_rows:
        matched_titles = [str(row.get('title', 'Unknown')) for row in exact_rows]
        return build_context_from_rows(exact_rows), 0.0, matched_titles, 'exact'

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    if not results or not results["metadatas"] or not results["metadatas"][0]:
        return None, 2.0, [], 'none'

    candidates = []
    exact_matches = []
    matched_titles = []
    min_distance = 2.0
    
    for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
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

        entry = {
            "title": title,
            "ingredients": format_list_string(ingredients),
            "instructions": format_list_string(instructions),
        }
        candidates.append(entry)

        if title_matches_query(query, title):
            exact_matches.append(entry)

    chosen = exact_matches if exact_matches else candidates
    if not chosen:
        return None, min_distance, [], 'none'

    context_parts = []
    for i, entry in enumerate(chosen, start=1):
        context_parts.append(
            f"### Recipe {i}: {entry['title']}\n\n"
            f"**Ingredients:**\n{entry['ingredients']}\n\n"
            f"**Instructions:**\n{entry['instructions']}\n"
        )
        matched_titles.append(entry['title'])

    match_type = 'exact' if exact_matches else 'related'
    return "\n---\n".join(context_parts), min_distance, matched_titles, match_type

