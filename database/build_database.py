import os
import json
from config import collection
from parse_laws import parse_law_file

laws_folder = os.path.join(os.path.dirname(__file__), "laws")
buckets_path = os.path.join(os.path.dirname(__file__), "buckets.json")
with open(buckets_path, "r") as f:
    config = json.load(f)

def build_database(language="de"):
    """Build the database for the specified language."""
    collection.delete_many({})
    print("Cleared existing database.")

    for bucket, law_list in config["buckets"].items():
        for short_name in law_list:
            file_path = os.path.join(laws_folder, f"{short_name}_{language}.xml")
            if os.path.exists(file_path):
                parsed_data = parse_law_file(file_path, short_name, bucket)
                collection.insert_many(parsed_data)
                print(f"Inserted {len(parsed_data)} articles for {short_name} ({language}) into {bucket}.")
            else:
                print(f"File {file_path} for {short_name} ({language}) not found.")

if __name__ == "__main__":
    build_database(language="de")  # Default to German
