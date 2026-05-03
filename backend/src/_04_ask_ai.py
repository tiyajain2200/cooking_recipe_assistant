from ollama import Client as OllamaClient
import os
from dotenv import load_dotenv
import sys

# Add backend dir to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from utils.prompts import SYSTEM_PROMPT, RECIPE_OUTPUT_FORMAT, RAG_QUERY_PROMPT, GENERAL_QUERY_PROMPT
from utils.functions import get_recipe_collection, clean_query
from src._03_rag import search_recipes

load_dotenv(os.path.join(os.path.dirname(BASE_DIR), '.env'))

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
LLM_MODEL = os.getenv('LLM_MODEL')

def ask_llm(user_query: str, context: str):
    client = OllamaClient(host=OLLAMA_BASE_URL)

    if context:
        full_user_prompt = RAG_QUERY_PROMPT.format(
            context=context,
            user_query=user_query
        )
    else:
        full_user_prompt = GENERAL_QUERY_PROMPT.format(
            user_query=user_query
        )

    print("\nChef Bot is generating response...\n")
    print("-" * 60)

    try:
        full_response = ""
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
            print(token, end="", flush=True)
            full_response += token
        
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "-" * 60)
    return full_response


def main():
    print("\n" + "=" * 60)
    print("   RECIPE BOT — AI Kitchen Assistant")
    print("=" * 60)
    print("\nEnter ingredients or a dish name.")
    print("Type 'quit' to exit.\n")

    collection = get_recipe_collection()

    while True:
        print()
        user_input = input("You: ").strip()

        if not user_input:
            print("Please enter something!")
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("\nGoodbye! Happy cooking!")
            break

        cleaned_query_text = clean_query(user_input)
        context, min_dist = search_recipes(collection, cleaned_query_text)

        ask_llm(user_input, context)


if __name__ == "__main__":
    main()
