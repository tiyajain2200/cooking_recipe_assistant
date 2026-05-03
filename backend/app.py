"""
Flask API Server for the Cooking Recipe RAG application.
Serves the frontend and exposes API endpoints for chat.
"""

import os
import sys
import json

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from ollama import Client as OllamaClient

# Path Setup 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

# Add backend dir to sys.path so we can import our modules
sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

#  Imports from our project 

from src._03_rag import search_recipes
from utils.functions import get_recipe_collection, clean_query
from utils.prompts import SYSTEM_PROMPT, RECIPE_OUTPUT_FORMAT, RAG_QUERY_PROMPT, GENERAL_QUERY_PROMPT

# Config 

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
LLM_MODEL = os.getenv('LLM_MODEL')

# Flask App 

app = Flask(__name__)
CORS(app)

# Initialize the ChromaDB collection once at startup
print("Starting Recipe RAG server...")
collection = get_recipe_collection()


# Serve Frontend 

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# API: Chat (SSE Streaming) 

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_query = data.get('query', '').strip()

    if not user_query:
        return jsonify({"error": "Please enter a query."}), 400

    # 1. Clean the query
    cleaned = clean_query(user_query)

    # 2. Retrieve relevant recipes from ChromaDB
    context, min_dist = search_recipes(collection, cleaned)

    # 3. Decision Logic: Prioritize dataset if match is very strong
    if context and min_dist < 0.45:
        def generate_direct():
            direct_message = (
                "### 🎯 Found in Database\n\n"
                "I found these great matches directly in my recipe collection:\n\n"
                f"{context}"
            )
            yield f"data: {json.dumps({'token': direct_message})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return Response(generate_direct(), mimetype='text/event-stream')

    # 4. Otherwise, use Ollama to process or provide a general answer
    if context:
        full_user_prompt = RAG_QUERY_PROMPT.format(
            context=context,
            user_query=user_query
        )
    else:
        full_user_prompt = GENERAL_QUERY_PROMPT.format(
            user_query=user_query
        )

    # 5. Stream response from Ollama via SSE
    def generate():
        try:
            client = OllamaClient(host=OLLAMA_BASE_URL)

            stream = client.chat(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + RECIPE_OUTPUT_FORMAT},
                    {"role": "user", "content": full_user_prompt},
                ],
                stream=True,
            )

            for chunk in stream:
                token = chunk["message"]["content"]
                yield f"data: {json.dumps({'token': token})}\n\n"

        except Exception as e:
            error_message = f"### ❌ Error\n\nSorry, I encountered an error: {str(e)}"
            yield f"data: {json.dumps({'token': error_message})}\n\n"

        # Signal the end of stream
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
