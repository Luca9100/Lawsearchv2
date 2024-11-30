import os
import json
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

# Ensure the 'laws' folder is created in the correct directory
laws_folder = os.path.join(os.path.dirname(__file__), "laws")
os.makedirs(laws_folder, exist_ok=True)

# Initialize the SPARQL endpoint
SPARQL_ENDPOINT = "https://fedlex.data.admin.ch/sparqlendpoint"

# Define the SPARQL query template
SPARQL_QUERY_TEMPLATE = """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT (str(?srNotation) as ?rsNr) (str(?dateApplicability) as ?dateApplicability) ?title ?abrev ?fileUrl WHERE {
  FILTER(?language = <http://publications.europa.eu/resource/authority/language/{LANGUAGE}>)
  # FRA = français, ITA = italiano, DEU = deutsch, ENG = english, ROH = rumantsch
  ?consolidation a jolux:Consolidation .
  ?consolidation jolux:dateApplicability ?dateApplicability .
  OPTIONAL { ?consolidation jolux:dateEndApplicability ?dateEndApplicability }
  FILTER(xsd:date(?dateApplicability) <= xsd:date(now()) && (!BOUND(?dateEndApplicability) || xsd:date(?dateEndApplicability) >= xsd:date(now())))
  ?consolidation jolux:isRealizedBy ?consoExpr .
  ?consoExpr jolux:language ?language .
  ?consoExpr jolux:isEmbodiedBy ?consoManif .
  ?consoManif jolux:userFormat <https://fedlex.data.admin.ch/vocabulary/user-format/xml> .
  ?consoManif jolux:isExemplifiedBy ?fileUrl .
  ?consolidation jolux:isMemberOf ?cc .
  ?cc jolux:classifiedByTaxonomyEntry/skos:notation ?srNotation .
  OPTIONAL { ?cc jolux:dateNoLongerInForce ?ccNoLonger }
  OPTIONAL { ?cc jolux:dateEndApplicability ?ccEnd }
  FILTER(!BOUND(?ccNoLonger) || xsd:date(?ccNoLonger) > xsd:date(now()))
  FILTER(!BOUND(?ccEnd) || xsd:date(?ccEnd) >= xsd:date(now()))
  FILTER(datatype(?srNotation) = <https://fedlex.data.admin.ch/vocabulary/notation-type/id-systematique>)
  OPTIONAL {
    ?cc jolux:isRealizedBy ?ccExpr .
    ?ccExpr jolux:language ?language .
    ?ccExpr jolux:title ?title .
    OPTIONAL {?ccExpr jolux:titleShort ?abrev }
  }
} ORDER BY ?srNotation
"""

# Languages supported by the Swiss legal system
LANGUAGES = {
    "de": "DEU",
    "en": "ENG",
    "fr": "FRA"
}

# Load the laws to fetch from laws.json
def load_laws_and_buckets():
    """
    Loads the laws and buckets from laws.json.
    """
    laws_path = os.path.join(os.path.dirname(__file__), "laws.json")
    if not os.path.exists(laws_path):
        raise FileNotFoundError("laws.json not found. Please create it with the laws and buckets.")
    with open(laws_path, "r") as f:
        data = json.load(f)
        return data["laws"]

laws_by_language = load_laws_and_buckets()

# Function to query the SPARQL endpoint
def query_sparql(language_code):
    """
    Queries the SPARQL endpoint for legal resources in the specified language.
    """
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    query = SPARQL_QUERY_TEMPLATE.replace("{LANGUAGE}", language_code)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        return results.get("results", {}).get("bindings", [])
    except Exception as e:
        print(f"Error querying SPARQL endpoint for language '{language_code}': {e}")
        return []

def fetch_laws():
    """
    Fetches legal XML files for the specified languages and saves them to the laws folder.
    """
    base_url = "https://www.fedlex.admin.ch/eli/"

    for lang, code in LANGUAGES.items():
        print(f"Fetching laws for language: {lang}")

        # Get the list of laws for the current language
        current_language_laws = laws_by_language.get(lang, {})
        if not current_language_laws:
            print(f"No laws specified for language: {lang}")
            continue

        for law, path in current_language_laws.items():
            print(f"Processing law: {law} for language {lang}")
            file_url = f"{base_url}{path}"
            print(f"Downloading from URL: {file_url}")

            try:
                response = requests.get(file_url)
                response.raise_for_status()

                # Create language-specific subfolder
                language_folder = os.path.join(laws_folder, lang)
                os.makedirs(language_folder, exist_ok=True)

                # Save the file
                file_path = os.path.join(language_folder, f"{law}.xml")
                with open(file_path, "wb") as file:
                    file.write(response.content)

                print(f"Saved XML file: {file_path}")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {file_url}: {e}")

if __name__ == "__main__":
    fetch_laws()
import os
import json
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

# Ensure the 'laws' folder is created in the correct directory
laws_folder = os.path.join(os.path.dirname(__file__), "laws")
os.makedirs(laws_folder, exist_ok=True)

# Initialize the SPARQL endpoint
SPARQL_ENDPOINT = "https://fedlex.data.admin.ch/sparqlendpoint"

# Define the SPARQL query template
SPARQL_QUERY_TEMPLATE = """
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT (str(?srNotation) as ?rsNr) (str(?dateApplicability) as ?dateApplicability) ?title ?abrev ?fileUrl WHERE {
  FILTER(?language = <http://publications.europa.eu/resource/authority/language/{LANGUAGE}>)
  # FRA = français, ITA = italiano, DEU = deutsch, ENG = english, ROH = rumantsch
  ?consolidation a jolux:Consolidation .
  ?consolidation jolux:dateApplicability ?dateApplicability .
  OPTIONAL { ?consolidation jolux:dateEndApplicability ?dateEndApplicability }
  FILTER(xsd:date(?dateApplicability) <= xsd:date(now()) && (!BOUND(?dateEndApplicability) || xsd:date(?dateEndApplicability) >= xsd:date(now())))
  ?consolidation jolux:isRealizedBy ?consoExpr .
  ?consoExpr jolux:language ?language .
  ?consoExpr jolux:isEmbodiedBy ?consoManif .
  ?consoManif jolux:userFormat <https://fedlex.data.admin.ch/vocabulary/user-format/xml> .
  ?consoManif jolux:isExemplifiedBy ?fileUrl .
  ?consolidation jolux:isMemberOf ?cc .
  ?cc jolux:classifiedByTaxonomyEntry/skos:notation ?srNotation .
  OPTIONAL { ?cc jolux:dateNoLongerInForce ?ccNoLonger }
  OPTIONAL { ?cc jolux:dateEndApplicability ?ccEnd }
  FILTER(!BOUND(?ccNoLonger) || xsd:date(?ccNoLonger) > xsd:date(now()))
  FILTER(!BOUND(?ccEnd) || xsd:date(?ccEnd) >= xsd:date(now()))
  FILTER(datatype(?srNotation) = <https://fedlex.data.admin.ch/vocabulary/notation-type/id-systematique>)
  OPTIONAL {
    ?cc jolux:isRealizedBy ?ccExpr .
    ?ccExpr jolux:language ?language .
    ?ccExpr jolux:title ?title .
    OPTIONAL {?ccExpr jolux:titleShort ?abrev }
  }
} ORDER BY ?srNotation
"""

# Languages supported by the Swiss legal system
LANGUAGES = {
    "de": "DEU",
    "en": "ENG",
    "fr": "FRA"
}

# Load the laws to fetch from laws.json
def load_laws_to_fetch():
    """
    Loads the laws to fetch from laws.json, ensuring compatibility with language-specific lists.
    """
    laws_path = os.path.join(os.path.dirname(__file__), "laws.json")
    if not os.path.exists(laws_path):
        raise FileNotFoundError("laws.json not found. Please create it with the laws to fetch.")
    with open(laws_path, "r") as f:
        data = json.load(f)
        laws_by_language = data.get("laws", {})
        if not isinstance(laws_by_language, dict):
            raise ValueError("The 'laws' field in laws.json must be a dictionary with language-specific lists.")
        return laws_by_language

laws_to_fetch = load_laws_to_fetch()

# Function to query the SPARQL endpoint
def query_sparql(language_code):
    """
    Queries the SPARQL endpoint for legal resources in the specified language.
    """
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    query = SPARQL_QUERY_TEMPLATE.replace("{LANGUAGE}", language_code)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        return results.get("results", {}).get("bindings", [])
    except Exception as e:
        print(f"Error querying SPARQL endpoint for language '{language_code}': {e}")
        return []

def fetch_laws():
    """
    Fetches legal XML files for the specified languages and saves them to the laws folder.
    """
    for lang, code in LANGUAGES.items():
        print(f"Fetching laws for language: {lang}")

        # Get the list of laws for the current language
        current_language_laws = laws_to_fetch.get(lang, [])
        if not current_language_laws:
            print(f"No laws specified for language: {lang}")
            continue

        results = query_sparql(code)

        if not results:
            print(f"No results found for language: {lang}")
            continue

        # Filter results based on the laws specified in laws.json
        filtered_results = [
            result for result in results
            if result.get("abrev", {}).get("value", "").strip() in current_language_laws
        ]

        if not filtered_results:
            print(f"No matching laws found for language: {lang}")
            continue

        # Save each filtered result
        for result in filtered_results:
            abrev = result.get("abrev", {}).get("value", "unknown")
            title = result.get("title", {}).get("value", "No Title")
            fileUrl = result.get("fileUrl", {}).get("value", "")

            print(f"Processing law: {title} ({abrev})")

            # Download and save the XML file
            try:
                response = requests.get(fileUrl)
                response.raise_for_status()
                # Create language-specific subfolder
                language_folder = os.path.join(laws_folder, lang)
                os.makedirs(language_folder, exist_ok=True)
                file_path = os.path.join(language_folder, f"{abrev}.xml")
                with open(file_path, "wb") as file:
                    file.write(response.content)
                print(f"Saved XML file: {file_path}")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {fileUrl}: {e}")

if __name__ == "__main__":
    fetch_laws()