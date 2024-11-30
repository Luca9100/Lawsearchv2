from lxml import etree
import os
import json

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
        return data["base_url"], data["laws"], data["buckets"]

base_url, laws_by_language, buckets = load_laws_and_buckets()

def assign_buckets(law_name, language):
    """
    Determine all applicable buckets for a given law name and language.
    """
    assigned_buckets = []
    for bucket_name, laws_in_languages in buckets.items():
        if law_name in laws_in_languages.get(language, []):
            assigned_buckets.append(bucket_name)
    return assigned_buckets

def parse_or_zgb_article(article, law_name, law_buckets, base_url, relative_path, language):
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

    # Construct the link dynamically
    link = f"{base_url}{relative_path}/#art_{article_number}"

    # Return a single article with all buckets
    return {
        'law_name': law_name,
        'eId': eId,
        'bucket': law_buckets,  # Assign all applicable buckets as a list
        'title': title,
        'text': full_text,
        'link': link,
        'language': language  # Add the language field
    }

def parse_or_zgb_section(section, law_name, law_buckets, base_url, relative_path, language):
    """
    Recursive parsing for OR/ZGB sections.
    """
    articles = []

    for child in section:
        tag_name = child.tag.split("}")[-1]
        if tag_name == "article":
            # Parse individual article
            article_data = parse_or_zgb_article(child, law_name, law_buckets, base_url, relative_path, language)
            articles.append(article_data)
        else:
            # Recursively parse subsections
            articles.extend(parse_or_zgb_section(child, law_name, law_buckets, base_url, relative_path, language))

    return articles

def parse_or_zgb_file(file_path, language):
    """
    Parse OR/ZGB files with specific logic for different languages.
    """
    # Map abbreviations based on language
    law_map = {
        "de": {"OR": "OR", "ZGB": "ZGB"},
        "en": {"CO": "CO", "CC": "CC"},
        "fr": {"CO": "CO", "CC": "CC"}
    }

    # Extract the filename without the path or extension
    law_filename = os.path.basename(file_path).replace(".xml", "")

    # Check if the filename matches a key in the mapping for the given language
    if law_filename in law_map.get(language, {}):
        law_name = law_map[language][law_filename]
    else:
        print(f"No matching law name for {file_path}. Skipping.")
        return []

    print(f"Starting to parse {law_name} ({language})...")

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist!")
        return []

    try:
        # Get the relative path for the law from laws.json
        relative_path = laws_by_language.get(language, {}).get(law_name, "")
        if not relative_path:
            print(f"Relative path for {law_name} not found in {language}. Skipping.")
            return []

        # Determine applicable buckets for the law
        law_buckets = assign_buckets(law_name, language)

        # Parse the XML file
        tree = etree.parse(file_path)
        root = tree.getroot()

        # Locate <body> element
        body = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}body")
        if body is None:
            print(f"Body not found for {law_name}.")
            return []

        # Parse sections within the body
        articles = []
        for section in body:
            articles.extend(parse_or_zgb_section(section, law_name, law_buckets, base_url, relative_path, language))
        print(f"Parsed {len(articles)} articles from {law_name} in {language} assigned to buckets {law_buckets}.")
        return articles

    except etree.XMLSyntaxError as e:
        print(f"Error parsing {file_path}: {e}")
        return []

if __name__ == "__main__":
    # Test the parser for OR in German
    law_file = os.path.join(os.path.dirname(__file__), "../laws/de/OR.xml")
    parsed_articles = parse_or_zgb_file(law_file, "de")

    # Display a few parsed articles for verification
    for article in parsed_articles[:5]:
        print(article)
