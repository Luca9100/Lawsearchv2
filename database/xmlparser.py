import xml.etree.ElementTree as ET
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

def parse_article(article, law_name, buckets, base_url, relative_path, language):
    """Parse an individual article element to extract relevant fields."""
    eId = article.attrib.get("eId", "")
    article_parts = eId.split("_")
    article_number = "_".join(article_parts[1:])  # Extract the full article number (e.g., 4_bis)
    title = ""
    text = []

    # Construct the link dynamically
    link = f"{base_url}{relative_path}/#art_{article_number}"

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

    # Create one article with bucket list
    return {
        'law_name': law_name,
        'eId': eId,
        'bucket': buckets,
        'title': title,
        'text': full_text,
        'link': link,
        'language': language  # Add the language field
    }

def parse_section(section, law_name, buckets, base_url, relative_path, language):
    """Parse sections to find articles and other subsections recursively."""
    articles = []

    for child in section:
        tag_name = child.tag.split("}")[-1]
        if tag_name == "article":
            # Parse individual article
            article_data = parse_article(child, law_name, buckets, base_url, relative_path, language)
            articles.append(article_data)
        else:
            # Recursively parse sections, chapters, etc.
            articles.extend(parse_section(child, law_name, buckets, base_url, relative_path, language))

    return articles

def parse_law_file(file_path, law_name, language):
    """Parse an XML law file and extract all articles."""
    print(f"Starting to parse {law_name} in {language}...")

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist!")
        return []

    try:
        # Get the relative path for the law from laws.json
        relative_path = laws_by_language.get(language, {}).get(law_name, "")
        if not relative_path:
            print(f"Relative path for {law_name} not found in {language}. Skipping.")
            return []

        # Determine all applicable buckets for the law
        law_buckets = assign_buckets(law_name, language)

        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Start parsing from the body tag, where articles are usually contained
        body = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}body")
        if body is None:
            print(f"Body not found for {law_name}. XML structure may be different.")
            return []
        else:
            print(f"Body found for {law_name}. Parsing sections...")
            articles = parse_section(body, law_name, law_buckets, base_url, relative_path, language)
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

            # Parse the law file
            articles = parse_law_file(file_path, law_name, language)
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
