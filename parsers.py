import re
from bs4 import BeautifulSoup
from utils import clean_text, parse_timestamp

def extract_article_links(soup: BeautifulSoup) -> list[dict]:
    print('--- DEBUG: Starting extract_article_links ---')

    if soup == None:
        print('DEBUG: Soup is None (Likely a network error)')
        return []

    results = []
    seen_links = set()

    # Target the parent container
    cards = soup.find_all("div", class_="card__post__content")
    print(f"DEBUG: Found {len(cards)} article cards on the page.")

    for idx, card in enumerate(cards, 1):
        print(f"\n--- Checking Card {idx} ---")

        # 1. Grab Title and Link
        h2 = card.find("h2", class_=re.compile(r"post_title"))
        if not h2:
            print("DEBUG: No h2 tag found.")
            continue

        a_tag = h2.find("a")
        if not a_tag:
            print("DEBUG: No a tag found inside h2.")
            continue

        href = a_tag.get("href", "").strip()
        title = a_tag.get_text(strip=True)
        print(f"DEBUG: Found Link -> {href}")

        if not href or href in seen_links:
            print("DEBUG: Link is empty or already seen.")
            continue

        # 2. Grab the Date
        date_span = card.find("span", class_="text-secondary")
        if not date_span:
            print("DEBUG: No date span ('text-secondary') found.")
            continue

        raw_date = date_span.get_text(strip=True)
        print(f"DEBUG: Raw Date String -> '{raw_date}'")

        parsed_date = parse_timestamp(raw_date)
        print(f"DEBUG: Parsed Date Object -> {parsed_date}")

        if parsed_date:
            seen_links.add(href)
            results.append({
                "title": title,
                "link": href,
                "date": parsed_date
            })
            print("DEBUG: Successfully added to results!")
        else:
            print("DEBUG: FAILED to parse the date. Dropping article.")

    print(f"\n--- DEBUG: Finished extracting. Returning {len(results)} valid articles. ---")
    return results

def extract_article_text(soup: BeautifulSoup) -> str | None:
    print('extracting text')
    if soup == None:
        return None

    for tag in soup.find_all(["script", "style", "aside", "footer", "header", "figure"]):
        tag.decompose()

    content_div = soup.find("div", class_=re.compile(r"wrap__article-detail-content"))

    if not content_div:
        return None

    unwanted_classes = ["baca-juga", "text-muted"]
    for tag in content_div.find_all(["span", "p", "div"], class_=unwanted_classes):
        tag.decompose()

    paragraphs = []
    for text in content_div.stripped_strings:
        cleaned = clean_text(text)
        if len(cleaned) > 20:
            paragraphs.append(cleaned)

    return " ".join(paragraphs) if paragraphs else None
