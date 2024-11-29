import os
import sys
from dotenv import load_dotenv
from config import collection
from xmlparser import main as parse_general_laws
from xmlparserORandZGB import parse_or_zgb_file

# Ensure the script can locate sibling modules within the `database` directory
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# Load environment variables from the root `.env` file
env_path = os.path.abspath(os.path.join(current_dir, "../.env"))
load_dotenv(dotenv_path=env_path)

def parse_all_laws(law_folder):
    """
    Parses all XML laws in the specified folder (by language) and inserts the parsed data into the database.
    """
    all_data = []
    languages = ["de", "en", "fr"]  # Supported languages

    for language in languages:
        lang_folder = os.path.join(law_folder, language)
        if not os.path.exists(lang_folder):
            print(f"Language folder '{lang_folder}' does not exist. Skipping.")
            continue

        print(f"Parsing laws for language: {language}")

        # Parse OR and ZGB specifically
        or_file = os.path.join(lang_folder, "OR.xml")
        zgb_file = os.path.join(lang_folder, "ZGB.xml")

        if os.path.exists(or_file):
            or_data = parse_or_zgb_file(or_file, "OR", "Gesetz")
            all_data.extend(or_data)

        if os.path.exists(zgb_file):
            zgb_data = parse_or_zgb_file(zgb_file, "ZGB", "Gesetz")
            all_data.extend(zgb_data)

        # Parse other general laws
        general_data = parse_general_laws(lang_folder)
        all_data.extend(general_data)

    # Insert all parsed data into the database
    if all_data:
        collection.insert_many(all_data)
        print(f"Inserted {len(all_data)} documents into the collection.")
    else:
        print("No data to insert.")

if __name__ == "__main__":
    # Define the base folder where the laws are stored
    law_folder = os.path.join(current_dir, "laws")

    # Clear the collection before inserting new data
    result = collection.delete_many({})
    print(f"Cleared {result.deleted_count} documents from the collection.")

    # Parse and insert all laws
    parse_all_laws(law_folder)
