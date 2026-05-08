import os
import openai
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment variables.")

# Initialize OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key
else:
    print("Warning: OPENAI_API_KEY not found in environment variables.")

def search_products(query_text: str, match_count: int = 3) -> list:
    """
    Embed query_text using OpenAI text-embedding-3-small.
    Call Supabase match_products() RPC with the embedding.
    Return list of matching product dicts with id, name, similarity score.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    if not openai.api_key:
        raise ValueError("OpenAI API key not initialized")

    try:
        # 1. Embed the query text
        response = openai.embeddings.create(
            input=query_text,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        # 2. Call Supabase RPC
        # The RPC function `match_products` needs to be defined in Supabase
        # to accept `query_embedding` and `match_count`
        rpc_response = supabase.rpc(
            "match_products",
            {"query_embedding": query_embedding, "match_count": match_count}
        ).execute()

        # 3. Return results
        return rpc_response.data

    except Exception as e:
        print(f"Error in search_products: {e}")
        return []