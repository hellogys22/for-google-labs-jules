import os
import openai
from dotenv import load_dotenv

from core.db import get_db

load_dotenv()

# Initialize OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key
else:
    print("Warning: OPENAI_API_KEY not found in environment variables.")

def search_products(query_text: str, match_count: int = 3) -> list:
    """
    Embed query_text using OpenAI text-embedding-3-small.
    Call MongoDB Atlas $vectorSearch pipeline with the embedding.
    Return list of matching product dicts with id, name, similarity score.
    """
    db = get_db()
    if db is None:
        raise ValueError("Database client not initialized")
    if not openai.api_key:
        print("Warning: OpenAI API key not initialized. RAG search will be skipped.")
        return []

    try:
        # 1. Embed the query text
        response = openai.embeddings.create(
            input=query_text,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        # 2. Call MongoDB $vectorSearch
        # Note: Requires an Atlas Vector Search index named 'vector_index' configured on the 'embedding' field
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": match_count * 10,
                    "limit": match_count
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "name": 1,
                    "price": 1,
                    "platform": 1,
                    "image_url": 1,
                    "similarity": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = list(db.products.aggregate(pipeline))

        # 3. Return results
        return results

    except Exception as e:
        print(f"Error in search_products: {e}")
        return []