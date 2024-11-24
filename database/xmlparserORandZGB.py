from lxml import etree
import os

# Define buckets and associated laws
buckets = {
    "General Counsel Law": ["OR", "ZGB", "DSG"],
    "Corporate Law": ["OR", "ZGB"],
    "Financial Law": ["OR", "ZGB", "FINIG", "KAG", "FIDLEG", "GwG", "BankG"]
}

def parse_or_zgb_article(article, law_name, law_type, bucket, hierarchy):
    """Parse articles with specific logic for OR and ZGB."""
    eId = article.attrib.get("eId", "")
    text = []
    title = ""

    # Extract the heading closest to the article
    current_element = article
    lowest_heading = None

    while current_element is not None:
        # Find heading within the current element
        heading = current_element.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}heading")
        if heading is not None:
            lowest_heading = " ".join(heading.itertext()).strip()
            break  # Stop once we find the nearest heading
        current_element = current_element.getparent()

    # Assign the nearest heading as the title
    title = lowest_heading if lowest_heading else "No Title"

    # Gather content paragraphs
    for child in article:
        tag_name = child.tag.split("}")[-1]
        if tag_name in {"paragraph", "content", "p"}:
            paragraph_text = "".join(child.itertext()).strip()
            text.append(paragraph_text)

    full_text = "\n".join(text)

    return {
        'law_name': law_name,
        'eId': eId,
        'bucket': bucket,
        'law_type': law_type,
        'title': title,  # Closest heading to the article
        'text': full_text,
        'hierarchy': hierarchy
    }

def parse_or_zgb_section(section, law_name, law_type, bucket, parent_tags):
    """Recursive parsing for OR/ZGB sections."""
    articles = []
    hierarchy = parent_tags + [section.tag.split("}")[-1]]

    for child in section:
        tag_name = child.tag.split("}")[-1]
        if tag_name == "article":
            article_data = parse_or_zgb_article(child, law_name, law_type, bucket, hierarchy + [tag_name])
            articles.append(article_data)
        else:
            articles.extend(parse_or_zgb_section(child, law_name, law_type, bucket, hierarchy))

    return articles

def parse_or_zgb_file(file_path, law_name, law_type, bucket):
    """Parse OR/ZGB files with specific logic."""
    tree = etree.parse(file_path)
    root = tree.getroot()

    body = root.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}body")
    articles = parse_or_zgb_section(body, law_name, law_type, bucket, ["akomaNtoso", "act", "body"]) if body is not None else []

    print(f"Parsed {len(articles)} articles from {law_name} under bucket '{bucket}'")
    return articles
