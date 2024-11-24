import sys
import os
from dotenv import load_dotenv

# Adjust path to find the .env file in the root directory
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path=env_path)

# Adjust path to find config.py in the same folder
database_path = os.path.dirname(__file__)
sys.path.append(database_path)

# Import the collection and parsers
from config import collection
from xmlparser import main as parse_general_laws
from xmlparserORandZGB import parse_or_zgb_file

def parse_all_laws(law_folder):
    """
    Parses all XML laws in the specified folder and inserts the parsed data into the database.
    """
    # Parse OR and ZGB separately
    or_data = parse_or_zgb_file(os.path.join(law_folder, "OR.xml"), "OR", "Gesetz", "General Counsel Law")
    zgb_data = parse_or_zgb_file(os.path.join(law_folder, "ZGB.xml"), "ZGB", "Gesetz", "General Counsel Law")

    # Parse other laws
    general_data = parse_general_laws(law_folder)

    # Combine all parsed data
    all_data = or_data + zgb_data + general_data

    # Insert parsed data into the database
    if all_data:
        collection.insert_many(all_data)
        print(f"Inserted {len(all_data)} documents into the collection.")

if __name__ == "__main__":
    # Define the folder where the laws are stored
    law_folder = os.path.join(os.path.dirname(__file__), "laws")

    # Clear the collection before inserting new data
    result = collection.delete_many({})
    print(f"Cleared {result.deleted_count} documents from the collection.")

    # Parse and insert all laws
    parse_all_laws(law_folder)
