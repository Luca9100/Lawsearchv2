from lxml import etree
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

def extract_identifier(meta_element, law_name):
    """
    Extracts the unique identifier for the law from the <meta> section.
    """
    if meta_element is not None:
        frbr_manifestation = meta_element.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRManifestation")
        if frbr_manifestation is not None:
            identifier = frbr_manifestation.attrib.get("value")
            if identifier:
                # Extract the relevant part of the identifier for the URL
                parts = identifier.split("eli/cc/")
                if len(parts) > 1:
                    return parts[1].split("/")[0]
    # Use fedlex_identifiers fallback if <meta> is missing or invalid
    return fedlex_identifiers.get(law_name, "default")

def parse_or_zgb_article(article, law_name, law_type, buckets, base_url):
    """
    Parse articles with specific logic for OR and ZGB.
    """
    eId = article.attrib.get("eId", "")
    article_number = "_".join(eId.split("_")[1:])  # Handle suffixes like 4_bis or 4_ter
    text = []
    title = ""

    # Extract the heading closest to the article
    current_element = article
    while current_element is not None:
        heading = current_element.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading")
        if heading is not None:
            title = " ".join(heading.itertext()).strip()
            break
        current_element = current_element.getparent()

    title = title if title else "No Title"

    # Gather content paragraphs
    for child in article:
        tag_name = child.tag.split("}")[-1]
        if tag_name in {"paragraph", "content", "p"}:
            paragraph_text = "".join(child.itertext()).strip()
            text.append(paragraph_text)

    full_text = "\n".join(text)

    # Return a single article with all buckets
    return {
        'law_name': law_name,
        'eId': eId,
        'bucket': buckets,  # Assign all applicable buckets as a list
        'law_type': law_type,
        'title': title,
        'text': full_text,
        'link': f"https://www.fedlex.admin.ch/eli/cc/{base_url}/de#art_{article_number}"
    }

def parse_or_zgb_section(section, law_name, law_type, buckets, base_url):
    """
    Recursive parsing for OR/ZGB sections.
    """
    articles = []

    for child in section:
        tag_name = child.tag.split("}")[-1]
        if tag_name == "article":
            # Parse individual article
            article_data = parse_or_zgb_article(child, law_name, law_type, buckets, base_url)
            articles.append(article_data)
        else:
            # Recursively parse subsections
            articles.extend(parse_or_zgb_section(child, law_name, law_type, buckets, base_url))

    return articles

def parse_or_zgb_file(file_path, law_name, law_type):
    """
    Parse OR/ZGB files with specific logic.
    """
    print(f"Starting to parse {law_name}...")

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist!")
        return []

    try:
        tree = etree.parse(file_path)
        root = tree.getroot()

        # Extract <meta> element and base URL
        meta_element = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}meta")
        base_url = extract_identifier(meta_element, law_name)

        # Determine applicable buckets for the law
        law_buckets = assign_buckets(law_name)

        # Locate <body> element
        body = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}body")
        if body is None:
            print(f"Body not found for {law_name}.")
            return []

        # Parse sections within the body
        articles = []
        for section in body:
            articles.extend(parse_or_zgb_section(section, law_name, law_type, law_buckets, base_url))
        print(f"Parsed {len(articles)} articles from {law_name} assigned to buckets {law_buckets}.")
        return articles

    except etree.XMLSyntaxError as e:
        print(f"Error parsing {file_path}: {e}")
        return []

if __name__ == "__main__":
    # Test the parser with OR.xml
    law_file = os.path.join(os.path.dirname(__file__), "../laws/OR.xml")
    parsed_articles = parse_or_zgb_file(law_file, "OR", "Gesetz")

    # Display a few parsed articles for verification
    for article in parsed_articles[:5]:
        print(article)
