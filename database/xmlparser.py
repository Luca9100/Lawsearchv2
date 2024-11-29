import xml.etree.ElementTree as ET
import os
import json

# Define buckets and associated laws
buckets = {
    "General Counsel Law": ["OR", "ZGB", "DSG"],
    "Corporate Law": ["OR", "ZGB"],
    "Financial Law": ["OR", "ZGB", "FINIG", "KAG", "FIDLEG", "GwG", "BankG"]
}

# Load fedlex_identifiers from JSON
def load_fedlex_identifiers():
    json_path = os.path.join(os.path.dirname(__file__), "fedlex_identifiers.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError("fedlex_identifiers.json not found. Please run fetch_laws.py.")
    with open(json_path, "r") as f:
        return json.load(f)

fedlex_identifiers = load_fedlex_identifiers()

def assign_buckets(law_name):
    """
    Determine all applicable buckets for a given law name.
    """
    assigned_buckets = []
    for bucket, laws in buckets.items():
        if law_name in laws:
            assigned_buckets.append(bucket)
    return assigned_buckets

def parse_article(article, law_name, law_type, buckets, base_url, language):
    """Parse an individual article element to extract relevant fields."""
    eId = article.attrib.get("eId", "")
    article_parts = eId.split("_")
    article_number = "_".join(article_parts[1:])  # Extract the full article number (e.g., 4_bis)
    title = ""
    text = []

    # Construct the link
    link = f"https://www.fedlex.admin.ch/eli/cc/{base_url}/{language}#art_{article_number}"

    # Traverse through the article's children to gather title and text
    for child in article:
        tag_name = child.tag.split("}")[-1]  # Ignore namespace
        if tag_name == "heading":  # Capture title
            title = child.text.strip() if child.text else "No Title"
        elif tag_name in {"paragraph", "content", "p"}:  # Capture text
            paragraph_text = "".join(child.itertext()).strip()  # Gather all text within paragraph
            text.append(paragraph_text)

    # Join all paragraphs to form the complete text of the article
    full_text = "\n".join(text)

    # Create one article per bucket
    return [
        {
            'law_name': law_name,
            'eId': eId,
            'bucket': bucket,
            'law_type': law_type,
            'title': title,
            'text': full_text,
            'link': link,
            'language': language  # Add the language field
        }
        for bucket in buckets
    ]

def parse_section(section, law_name, law_type, buckets, base_url, language):
    """Parse sections to find articles and other subsections recursively."""
    articles = []

    for child in section:
        tag_name = child.tag.split("}")[-1]
        if tag_name == "article":
            # Parse individual article
            article_data = parse_article(child, law_name, law_type, buckets, base_url, language)
            articles.extend(article_data)
        else:
            # Recursively parse sections, chapters, etc.
            articles.extend(parse_section(child, law_name, law_type, buckets, base_url, language))

    return articles

def parse_law_file(file_path, law_name, law_type, language):
    """Parse an XML law file and extract all articles."""
    print(f"Starting to parse {law_name} in {language}...")

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist!")
        return []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract the <meta> element and base_url
        meta_element = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}meta")
        frbr_manifestation = None
        base_url = fedlex_identifiers.get(law_name, "unknown")  # Fallback to the identifier from JSON

        if meta_element is not None:
            frbr_manifestation = meta_element.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRManifestation")
            if frbr_manifestation is not None:
                value = frbr_manifestation.attrib.get("value")
                if value and "eli/cc/" in value:
                    base_url = value.split("eli/cc/")[1].split("/")[0]

        # Determine all applicable buckets for the law
        law_buckets = assign_buckets(law_name)

        # Start parsing from the body tag, where articles are usually contained
        body = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}body")
        if body is None:
            print(f"Body not found for {law_name}. XML structure may be different.")
            return []
        else:
            print(f"Body found for {law_name}. Parsing sections...")
            articles = parse_section(body, law_name, law_type, law_buckets, base_url, language)
            print(f"Parsed {len(articles)} articles from {law_name} in {language} assigned to buckets {law_buckets}.")
            return articles
    except ET.ParseError as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def main(law_folder, language):
    """Main function to parse all XML files in the specified folder and return parsed data."""
    all_articles = []

    print(f"Scanning folder: {law_folder} for language: {language}")
    for filename in os.listdir(law_folder):
        if filename.endswith(".xml"):
            law_name = filename.split(".")[0]  # Extract law name from filename
            file_path = os.path.join(law_folder, filename)
            law_type = "Gesetz"  # Set law type; can be customized per file

            # Parse the law file
            articles = parse_law_file(file_path, law_name, law_type, language)
            all_articles.extend(articles)

    print(f"Total articles parsed: {len(all_articles)} for language: {language}")
    return all_articles

if __name__ == "__main__":
    # For testing purposes, specify the folder and language directly if running this script alone.
    law_folder = os.path.join(os.path.dirname(__file__), "../laws/de")
    parsed_data = main(law_folder, "de")

    # Optionally, print the parsed data for verification
    for article in parsed_data[:5]:  # Display only the first 5 articles for preview
        print(article)
