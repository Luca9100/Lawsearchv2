from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Hole das Passwort aus der .env-Datei
mongo_uri = os.getenv("MONGO_URI")

# Verbindung mit MongoDB Atlas herstellen
connection_string = f"{mongo_uri}"

try:
    # MongoDB-Client erstellen
    client = MongoClient(connection_string)
    
    # Zugriff auf die gewünschte Datenbank
    db = client["legal_database"]  # Name der Datenbank
    print("Erfolgreich mit MongoDB verbunden!")

    # Zugriff auf die Collection "laws"
    collection = db["laws"]

    # Testeintrag in die Datenbank
    test_entry = {
        "law_id": "test123",
        "title": "Testgesetz",
        "valid_from": "2024-01-01"
    }
    # Testeintrag in die Collection einfügen
    collection.insert_one(test_entry)
    print("Testeintrag erfolgreich hinzugefügt:", test_entry)

except Exception as e:
    print("Fehler bei der Verbindung mit MongoDB:", e)

