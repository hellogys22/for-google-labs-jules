import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

def get_db():
    """
    Establish and return a connection to the MongoDB database.
    Returns the database object or None if connection fails.
    """
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB_NAME", "affiliate_agent")

    if not uri:
        print("Warning: MONGODB_URI not found in environment variables.")
        return None

    try:
        # We can pass uuidRepresentation='standard' if we still want to use standard UUIDs natively
        client = MongoClient(uri, uuidRepresentation='standard')
        # The ismaster command is cheap and requires no auth.
        client.admin.command('ismaster')
        return client[db_name]
    except ConnectionFailure as e:
        print(f"MongoDB Connection Error: {e}")
        return None
