import re
from bs4 import BeautifulSoup
from utils import clean_text, parse_timestamp
from configuration import BASE_URL

def extract_article_links(soup: BeautifulSoup) -> list[dict]:
    """Extract candidate article links and dates from a list page."""
    print('extracting links')
    if soup != None:
        return 'notthing passed from curresnt session'

    results = []
    seen_links = set()
    anchors = soup.find_all("a", href=re.compile(r"/berita/\d+/"))

    for a in anchors:
        href = a.get("href", "").strip()
        if not href:
            continue

        full_url = href if href.startswith("http") else BASE_URL + href
        if full_url in seen_links:
            continue

        container = a.parent or a
        raw_ts = None

        # Look for time tag
        time_tag = container.find("time")
        if time_tag:
            raw_ts = time_tag.get("datetime") or time_tag.get_text(strip=True)

        # Look for span with date
        if not raw_ts:
            for span in container.find_all("span"):
                txt = span.get_text(" ", strip=True)
                if re.search(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", txt):
                    raw_ts = txt
                    break

        if raw_ts:
            parsed_date = parse_timestamp(raw_ts)
            if parsed_date:
                seen_links.add(full_url)
                results.append({"link": full_url, "date": parsed_date})

    return results

def extract_article_text(soup: BeautifulSoup) -> str | None:
    """Extract clean body text from a detail page."""
    print('extracting text')
    for tag in soup.find_all(["script", "style", "aside", "footer", "header"]):
        tag.decompose()

    # Generic approach to find content container
    best_div, best_len = None, 0
    for div in soup.find_all("div", class_=re.compile(r"post.?content|detail.?text", re.I)):
        text_len = len(div.get_text(strip=True))
        if text_len > best_len:
            best_len = text_len
            best_div = div

    if not best_div:
        return None

    paragraphs = []
    for p in best_div.find_all("p"):
        text = clean_text(p.get_text(separator=" "))
        if len(text) > 20 and not re.match(r"^(Baca juga|Pewarta|Editor|COPYRIGHT)", text, re.I):
            paragraphs.append(text)

    return " ".join(paragraphs) if paragraphs else None
