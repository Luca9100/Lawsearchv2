import requests
import os
import json

# SPARQL query results with relevant laws
sparql_results = [
    {"shortName": "ZGB", "title": "Schweizerisches Zivilgesetzbuch (ZGB)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/24/233_245_233/20240101/de/xml/fedlex-data-admin-ch-eli-cc-24-233_245_233-20240101-de-xml-25.xml"},
    {"shortName": "OR", "title": "Obligationenrecht (OR)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/27/317_321_377/20240101/de/xml/fedlex-data-admin-ch-eli-cc-27-317_321_377-20240101-de-xml-15.xml"},
    {"shortName": "DSG", "title": "Datenschutzgesetz (DSG)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2022/491/20230901/de/xml/fedlex-data-admin-ch-eli-cc-2022-491-20230901-de-xml-12.xml"},
    {"shortName": "FIDLEG", "title": "Finanzdienstleistungsgesetz (FIDLEG)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2019/758/20240301/de/xml/fedlex-data-admin-ch-eli-cc-2019-758-20240301-de-xml-3.xml"},
    {"shortName": "KAG", "title": "Kollektivanlagengesetz (KAG)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2006/822/20240301/de/xml/fedlex-data-admin-ch-eli-cc-2006-822-20240301-de-xml-3.xml"},
    {"shortName": "BankG", "title": "Bankengesetz (BankG)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/51/117_121_129/20240101/de/xml/fedlex-data-admin-ch-eli-cc-51-117_121_129-20240101-de-xml-1.xml"},
    {"shortName": "FINIG", "title": "Finanzinstitutsgesetz (FINIG)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2018/801/20240301/de/xml/fedlex-data-admin-ch-eli-cc-2018-801-20240301-de-xml-3.xml"},
    {"shortName": "GwG", "title": "Geldwäschereigesetz (GwG)", "fileUrl": "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/1998/892_892_892/20240301/de/xml/fedlex-data-admin-ch-eli-cc-1998-892_892_892-20240301-de-xml-2.xml"}
]

# Ensure the 'laws' folder is created in the correct directory
laws_folder = os.path.join(os.path.dirname(__file__), "laws")
os.makedirs(laws_folder, exist_ok=True)

# Initialize fedlex_identifiers
fedlex_identifiers = {}

def fetch_laws():
    """
    Downloads XML files for laws and constructs the fedlex_identifiers mapping.
    """
    for result in sparql_results:
        shortName = result["shortName"]
        title = result["title"]
        fileUrl = result["fileUrl"]

        print(f"Processing law: {title} ({shortName})")

        # Extract identifier from the fileUrl
        identifier = "/".join(fileUrl.split("/eli/cc/")[1].split("/")[0:2])  # Extracts "51/117_121_129"
        fedlex_identifiers[shortName] = identifier

        # Download the XML file
        try:
            response = requests.get(fileUrl)
            response.raise_for_status()  # Raise HTTP errors
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {fileUrl}: {e}")
            continue

        # Save the XML file with shortName
        file_path = os.path.join(laws_folder, f"{shortName}.xml")
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Saved XML file: {file_path}")

    # Save fedlex_identifiers as JSON in the correct directory
    json_path = os.path.join(os.path.dirname(__file__), "fedlex_identifiers.json")
    with open(json_path, "w") as f:
        json.dump(fedlex_identifiers, f, indent=4)
    print(f"Saved fedlex_identifiers.json")

if __name__ == "__main__":
    fetch_laws()
