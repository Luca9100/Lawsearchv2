import sys
import os
from dotenv import load_dotenv

# Adjust path to find the .env file in the root directory
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=env_path)

# Adjust path to find config.py in the main database folder
database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
sys.path.append(database_path)

# Import the collection from config.py
from config import collection

def clear_collection():
    """
    Clears all documents in the target collection.
    """
    result = collection.delete_many({})
    print(f"Deleted {result.deleted_count} documents from the collection.")

if __name__ == "__main__":
    clear_collection()
