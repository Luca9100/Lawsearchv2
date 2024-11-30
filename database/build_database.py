import os
import shutil
import json
from fetch_laws import fetch_laws  # Assuming fetch_laws.py is in the same directory
from xmlparser import parse_law_file  # Assuming xmlparser handles generic laws
from xmlparserORandZGB import parse_or_zgb_file  # Assuming this handles OR and ZGB
from config import collection

# Load laws and buckets from laws.json
def load_laws_and_buckets():
    """
    Loads laws and buckets from laws.json.
    """
    json_path = os.path.join(os.path.dirname(__file__), "laws.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError("laws.json not found. Please create it with the laws and buckets.")
    with open(json_path, "r") as f:
        data = json.load(f)
        return data["laws"], data["buckets"]

laws_by_language, buckets = load_laws_and_buckets()
laws_folder = os.path.join(os.path.dirname(__file__), "laws")

def clear_database():
    """Delete all entries in the current MongoDB collection."""
    collection.delete_many({})
    print("Cleared the existing database.")

def delete_laws_folder():
    """Delete the current 'laws' folder and all its contents."""
    if os.path.exists(laws_folder):
        shutil.rmtree(laws_folder)
        print(f"Deleted the folder: {laws_folder}")
    else:
        print(f"Laws folder '{laws_folder}' does not exist. Skipping deletion.")

def build_database():
    """
    Fetch laws, parse them, and populate the database for all supported languages.
    """
    # Clear existing database
    clear_database()

    # Delete laws folder
    delete_laws_folder()

    # Fetch new laws
    print("Fetching new laws...")
    fetch_laws()

    # Supported languages
    languages = ["de", "en", "fr"]

    # Parse and write laws to the database for each language
    print("Building the database...")
    for language in languages:
        print(f"Processing language: {language}")
        for bucket_name, laws_in_languages in buckets.items():
            # Get the bucket-specific laws for the current language
            law_list = laws_in_languages.get(language, [])
            for short_name in law_list:
                # Construct file path for the current law
                file_path = os.path.join(laws_folder, language, f"{short_name}.xml")
                if os.path.exists(file_path):
                    # Determine parsing method based on file
                    if short_name in ["OR", "ZGB", "CO", "CC"]:
                        parsed_data = parse_or_zgb_file(file_path, language)
                    else:
                        parsed_data = parse_law_file(file_path, short_name, language)

                    # Assign bucket information explicitly (since it might not be in the parser output)
                    for article in parsed_data:
                        if 'bucket' not in article:
                            article['bucket'] = []
                        if bucket_name not in article['bucket']:
                            article['bucket'].append(bucket_name)


                    if parsed_data:
                        collection.insert_many(parsed_data)
                        print(f"Inserted {len(parsed_data)} articles for {short_name} ({language}) into {bucket_name}.")
                else:
                    print(f"File {file_path} for {short_name} ({language}) not found.")

if __name__ == "__main__":
    build_database()
