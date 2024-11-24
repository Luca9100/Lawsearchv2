import requests
import os
import json

# SPARQL-Abfrage-Ergebnisse mit relevanten Gesetzen
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

# Ordner für heruntergeladene XML-Dateien erstellen
laws_folder = "laws"
os.makedirs(laws_folder, exist_ok=True)

def download_laws():
    """
    Lädt die XML-Dateien der Gesetze von den angegebenen Links herunter und speichert sie im Ordner.
    """
    for result in sparql_results:
        shortName = result["shortName"]
        title = result["title"]
        fileUrl = result["fileUrl"]

        print(f"Verarbeite Gesetz: {title} ({shortName})")

        # Download der XML-Datei
        try:
            response = requests.get(fileUrl)
            response.raise_for_status()  # Raise HTTP errors
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Herunterladen von {fileUrl}: {e}")
            continue

        # Speichere die XML-Datei mit shortName
        file_path = os.path.join(laws_folder, f"{shortName}.xml")
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"XML-Datei gespeichert: {file_path}")

if __name__ == "__main__":
    download_laws()
