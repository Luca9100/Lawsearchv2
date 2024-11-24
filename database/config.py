import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MongoDB connection string (MONGO_URI) is missing in .env.")

# Database and Collection Names
DATABASE_NAME = "legal_database"
COLLECTION_NAME = "parsed_laws"

# MongoDB Client
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
