from configuration import BASE_URL
import re
from bs4 import BeautifulSoup
from utils import clean_text, parse_timestamp

def extract_article_links(soup: BeautifulSoup) -> list[dict]:
    """Extract candidate article links, titles, and dates from a list page."""
    print('extracting links')

    if soup == None:
        return []

    results = []
    seen_links = set()

    # Target the parent container shown in Image 2
    cards = soup.find_all("div", class_="card__post__content")

    for card in cards:
        h2 = card.find("h2", class_=re.compile(r"post_title"))
        if not h2: continue

        a_tag = h2.find("a")
        if not a_tag: continue

        href = a_tag.get("href", "").strip()
        title = a_tag.get_text(strip=True)

        if not href or href in seen_links: continue

        date_span = card.find("span", class_="text-secondary")
        if not date_span: continue

        raw_date = date_span.get_text(strip=True)
        parsed_date = parse_timestamp(raw_date)

        if parsed_date:
            seen_links.add(href)
            results.append({
                "title": title,
                "link": href,
                "date": parsed_date
            })

    return results

def extract_article_text(soup: BeautifulSoup) -> str | None:
    """Extract clean body text from a detail page separated by <br> tags."""
    print('extracting text')
    if soup == None:
        return None

    for tag in soup.find_all(["script", "style", "aside", "footer", "header", "figure"]):
        tag.decompose()

    content_div = soup.find("div", class_=re.compile(r"wrap__article-detail-content"))

    if not content_div:
        return None

    paragraphs = []
    for text in content_div.stripped_strings:
        cleaned = clean_text(text)
        # Keep chunks longer than 20 chars to filter out social media buttons/junk
        if len(cleaned) > 20:
            paragraphs.append(cleaned)

    return " ".join(paragraphs) if paragraphs else None
