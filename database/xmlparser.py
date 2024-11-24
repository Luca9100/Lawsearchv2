import xml.etree.ElementTree as ET
import os

# Define buckets and associated laws
buckets = {
    "General Counsel Law": ["OR", "ZGB", "DSG"],
    "Corporate Law": ["OR", "ZGB"],
    "Financial Law": ["OR", "ZGB", "FINIG", "KAG", "FIDLEG", "GwG", "BankG"]
}

def parse_article(article, law_name, law_type, bucket, hierarchy):
    """Parse an individual article element to extract relevant fields."""
    eId = article.attrib.get("eId", "")
    title = ""
    text = []

    # Traverse through the article's children to gather title and text
    for child in article:
        tag_name = child.tag.split("}")[-1]  # Ignore namespace
        if tag_name == "heading":  # Capture title
            title = child.text.strip() if child.text else ""
        elif tag_name in {"paragraph", "content", "p"}:  # Capture text
            paragraph_text = "".join(child.itertext()).strip()  # Gather all text within paragraph
            text.append(paragraph_text)

    # Join all paragraphs to form the complete text of the article
    full_text = "\n".join(text)

    # Debug: Print extracted title and text sample
    if title:
        print(f"Extracted title: {title[:50]}...")
    else:
        print("No title extracted")
    if full_text:
        print(f"Extracted text sample: {full_text[:50]}...")
    else:
        print("No text extracted")

    return {
        'law_name': law_name,
        'eId': eId,
        'bucket': bucket,
        'law_type': law_type,
        'title': title,
        'text': full_text,
        'hierarchy': hierarchy
    }

def parse_section(section, law_name, law_type, bucket, parent_tags):
    """Parse sections to find articles and other subsections recursively."""
    articles = []
    hierarchy = parent_tags + [section.tag.split("}")[-1]]  # Add current tag to hierarchy

    for child in section:
        tag_name = child.tag.split("}")[-1]
        if tag_name == "article":
            # Parse individual article
            article_data = parse_article(child, law_name, law_type, bucket, hierarchy + [tag_name])
            articles.append(article_data)
        else:
            # Recursively parse sections, chapters, etc.
            articles.extend(parse_section(child, law_name, law_type, bucket, hierarchy))

    return articles

def parse_law_file(file_path, law_name, law_type, bucket):
    """Parse an XML law file and extract all articles."""
    print(f"Starting to parse {law_name}...")

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist!")
        return []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Start parsing from the body tag, where articles are usually contained
        body = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}body")
        if body is None:
            print(f"Body not found for {law_name}. XML structure may be different.")
            return []
        else:
            print(f"Body found for {law_name}. Parsing sections...")
            articles = parse_section(body, law_name, law_type, bucket, ["akomaNtoso", "act", "body"])
            print(f"Parsed {len(articles)} articles from {law_name} under bucket '{bucket}'.")
            return articles
    except ET.ParseError as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def main(law_folder):
    """Main function to parse all XML files in the specified folder and return parsed data."""
    all_articles = []

    print(f"Scanning folder: {law_folder}")
    for filename in os.listdir(law_folder):
        if filename.endswith(".xml"):
            law_name = filename.split(".")[0]  # Extract law name from filename
            file_path = os.path.join(law_folder, filename)
            law_type = "Gesetz"  # Set law type; can be customized per file

            # Skip OR and ZGB, as they are handled by a separate parser
            if law_name in ["OR", "ZGB"]:
                print(f"Skipping {law_name} as it is handled by a separate parser.")
                continue

            # Assign law to the appropriate bucket
            law_bucket = None
            for bucket, laws in buckets.items():
                if law_name in laws:
                    law_bucket = bucket
                    break

            if not law_bucket:
                print(f"No bucket found for {law_name}. Skipping.")
                continue

            # Parse the law file
            articles = parse_law_file(file_path, law_name, law_type, law_bucket)
            all_articles.extend(articles)

    print(f"Total articles parsed: {len(all_articles)}")
    return all_articles

if __name__ == "__main__":
    # For testing purposes, specify the folder directly if running this script alone.
    law_folder = os.path.join(os.path.dirname(__file__), "../laws")
    parsed_data = main(law_folder)

    # Optionally, print the parsed data for verification
    for article in parsed_data[:5]:  # Display only the first 5 articles for preview
        print(article)
