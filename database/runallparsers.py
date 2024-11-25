import os
import sys
from dotenv import load_dotenv

# Ensure the script can locate sibling modules within the `database` directory
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# Load environment variables from the root `.env` file
env_path = os.path.abspath(os.path.join(current_dir, "../.env"))
load_dotenv(dotenv_path=env_path)

# Import dependencies
from config import collection
from xmlparser import main as parse_general_laws
from xmlparserORandZGB import parse_or_zgb_file  # Corrected import

def parse_all_laws(law_folder):
    """
    Parses all XML laws in the specified folder and inserts the parsed data into the database.
    """
    # Parse OR and ZGB laws
    or_data = parse_or_zgb_file(os.path.join(law_folder, "OR.xml"), "OR", "Gesetz")
    zgb_data = parse_or_zgb_file(os.path.join(law_folder, "ZGB.xml"), "ZGB", "Gesetz")

    # Parse other general laws
    general_data = parse_general_laws(law_folder)

    # Combine all parsed data
    all_data = or_data + zgb_data + general_data

    # Insert parsed data into the database
    if all_data:
        collection.insert_many(all_data)
        print(f"Inserted {len(all_data)} documents into the collection.")

if __name__ == "__main__":
    # Define the folder where the laws are stored
    law_folder = os.path.join(current_dir, "laws")

    # Clear the collection before inserting new data
    result = collection.delete_many({})
    print(f"Cleared {result.deleted_count} documents from the collection.")

    # Parse and insert all laws
    parse_all_laws(law_folder)
