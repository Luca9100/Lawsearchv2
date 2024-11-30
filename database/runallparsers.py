import os
import sys
from dotenv import load_dotenv
from config import collection
from xmlparser import main as parse_general_laws
from xmlparserORandZGB import parse_or_zgb_file
import json

# Ensure the script can locate sibling modules within the `database` directory
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# Load environment variables from the root `.env` file
env_path = os.path.abspath(os.path.join(current_dir, "../.env"))
load_dotenv(dotenv_path=env_path)

# Load laws.json to access abbreviations, base_url, and buckets
laws_json_path = os.path.join(current_dir, "laws.json")
with open(laws_json_path, "r") as f:
    laws_data = json.load(f)

base_url = laws_data["base_url"]
laws_by_language = laws_data["laws"]

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

        # Access language-specific laws
        language_laws = laws_by_language.get(language, {})
        if not language_laws:
            print(f"No laws found for language: {language}. Skipping.")
            continue

        # Parse OR and ZGB specifically
        for abbreviation in ["OR", "ZGB"]:
            if abbreviation in language_laws:
                law_path = os.path.join(lang_folder, f"{abbreviation}.xml")
                if os.path.exists(law_path):
                    print(f"Parsing {abbreviation} in {language}...")
                    or_zgb_data = parse_or_zgb_file(
                        law_path,
                        abbreviation,
                        language,
                        base_url
                    )
                    all_data.extend(or_zgb_data)

        # Parse other general laws
        for abbreviation, path_suffix in language_laws.items():
            if abbreviation not in ["OR", "ZGB"]:  # Skip OR and ZGB here
                law_path = os.path.join(lang_folder, f"{abbreviation}.xml")
                if os.path.exists(law_path):
                    print(f"Parsing {abbreviation} in {language}...")
                    general_data = parse_general_laws(
                        law_path, abbreviation, language, base_url
                    )
                    all_data.extend(general_data)

    # Insert all parsed data into the database
    if all_data:
        # Ensure buckets are always lists and remove unwanted fields
        for doc in all_data:
            if not isinstance(doc["bucket"], list):
                doc["bucket"] = [doc["bucket"]]
            doc.pop("law_type", None)  # Remove `law_type` if present

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
